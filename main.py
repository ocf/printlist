import functools
import os
import sys
import time
import redis
import threading
from configparser import ConfigParser
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
import sys

# Contains Redis secrets
BROKER_AUTH = 'conf/broker.conf'

# Enables Dev Mode
DEV_MODE = '--dev' in sys.argv

# Opens a Redis connection (printer information)
redis_connection = functools.partial(
    redis.StrictRedis,
    host='broker',
    port=6378,
    ssl=True,
    db=0,
    password=None
)

def subscribe(host, password, *channels):
    rc = redis_connection(host=host, password=password)
    sub = rc.pubsub(ignore_subscribe_messages=True)
    sub.subscribe(channels)
    return sub

def read_config():
    config = ConfigParser()
    config.read(BROKER_AUTH)
    host = config.get('broker', 'host')
    password = config.get('broker', 'password')
    return host, password

printer_dict = {'printer-logjam': [], 'printer-pagefault': [], 'printer-papercut': []}
printer_names = [('printer-papercut', 'papercut'), ('printer-logjam', 'logjam'), ('printer-pagefault', 'pagefault')]

def push_user(printer, username):
    printer_dict[printer].append(username)

def remove_user(printer, username):
    printer_dict[printer].remove(username)

def check_user(printer, username):
    curr_time = time.time()
    if curr_time - username[1] >= 180:
        remove_user(printer, username)

def monitor_printer():
    host, password = read_config()

    s = subscribe(host, password, 'printer-logjam', 'printer-pagefault', 'printer-papercut')
    while True:
        message = s.get_message()
        if message and 'data' in message:
            printer = message['channel'].decode(encoding='UTF-8').replace('\n', ' ')
            username = (message['data'].decode(encoding='UTF-8').replace('\n', ' '), time.time())
            push_user(printer, username)
            print(printer_dict) #temporary to see if things are working
        for p in printer_dict.keys():
            for u in printer_dict[p]:
                check_user(p, u)

def create_app():
    app = Flask(__name__)
    monitor_process = threading.Thread(target = monitor_printer)
    monitor_process.daemon = DEV_MODE
    monitor_process.start()
    return app

if DEV_MODE:
    print('Developer Mode Enabled')
    read_config = lambda: (None, None)
    from redis_mimic import mimic_sub
    subscribe = mimic_sub

app = create_app()

@app.route('/home')
def home():
    return render_template('full.html', title = 'home', print_list = printer_dict, printer_names = printer_names)

# Deprecated
@app.route('/printer/<string:printer>')
def printlist(printer):
    p = 'printer-' + printer
    requested_list = printer_dict[p]
    return render_template('printer.html', title = 'printer', requested_list = set(requested_list), printer = printer)

@app.route('/reload/recent')
def reload():
    if not('last-fetch' in request.args and request.args.get('last-fetch').isdigit()):
        return 'Invalid Request'
    last_fetch = int(request.args.get('last-fetch'))/1000
    recent = {}
    for printer in printer_dict:
        recent[printer] = [job for job in printer_dict[printer] if job[1] > last_fetch]
    return jsonify(recent)

if DEV_MODE:
    app.config.update(TEMPLATES_AUTO_RELOAD = True, SEND_FILE_MAX_AGE_DEFAULT=0)
    app.run(port=3000)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print('Program Closed')
            sys.exit(1)
