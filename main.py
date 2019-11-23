import functools
import os
import sys
import time
import redis
import threading
from configparser import ConfigParser
from flask import Flask
from flask import render_template

BROKER_AUTH = 'broker.conf'

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

app = Flask(__name__)

@app.route('/<string:printer>')
def home(printer):
    p = 'printer-' + printer
    requested_list = printer_dict[p]
    return render_template('home.html', title = 'home', requested_list = requested_list, printer = printer)

if __name__ == '__main__':
    t1 = threading.Thread(target = app.run, kwargs = dict(port = 8020, host = "0.0.0.0", debug = True, use_reloader = False, threaded = True))
    t2 = threading.Thread(target = monitor_printer)
    t1.start()
    t2.start()
