import functools
import os
import sys
import time
import redis
import threading
import json
from configparser import ConfigParser
from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request

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

printer_names = {
    'printer-papercut': 'papercut',
    'printer-logjam': 'logjam',
    'printer-pagefault': 'pagefault'
}
print_jobs = {
    'printer-papercut': {},
    'printer-logjam': {},
    'printer-pagefault': {}
}

persist = 180
persist_completed = 60

class Job:
    @staticmethod
    def cleanup():
        for printer in print_jobs:
            for job in printer:
                if job.currentStatus() == 0:
                    if job.time+persist_completed < time.time():
                        del job
                else:
                    if job.time+persist < time.time():
                        del job
    @staticmethod
    def getRecent(time):
        jobs = {}
        for printer in print_jobs:
            jobs[printer] = {}
            jobs[printer] = {job: print_jobs[printer][job] for job in print_jobs[printer] if job.last_updated > time}
        return jobs

    @staticmethod
    def add(printer_name, username, time, status, job_id):
        if job_id in print_jobs[printer_name]:
            return print_jobs[printer_name][job_id].update(username, status, time)
        print_jobs[printer_name][job_id] = Job(username, time, status, job_id)
        Job.cleanup()

    def __init__(self, username, time, status, job_id):
        self.username = username
        self.id = job_id
        self.last_updated = time
        self.statusQueue = [(status, time)]

    def update(self, username, status, time):
        if username != self.username:
            print("Conflict: Job#" + job_id + " | " + self.username + " vs " + username);
            return False
        self.statusQueue.append((status, time))
        self.last_updated = time
        return True

    def currentStatus(self):
        return self.statusQueue[-1]


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


def monitor_printer():
    host, password = read_config()

    s = subscribe(host, password, 'printer-logjam', 'printer-pagefault', 'printer-papercut')
    while True:
        message = s.get_message()
        if message and 'data' in message:
            try:
                printer_name = message['channel']
                print_job = json.loads(message['data'])
                Job.add(
                    printer_name=printer_name,
                    username=print_job.user,
                    time=print_job.time,
                    status=print_job.status,
                    job_id=print_job.id
                )
            except ValueError:
                print('Unable to parse JSON')


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
    if not request.args.get('last-fetch', '').isdigit():
        return 'Invalid Request', 400
    last_fetch = int(request.args.get('last-fetch'))/1000
    return jsonify(Job.getrecent(last_fetch))

if DEV_MODE:
    app.config.update(TEMPLATES_AUTO_RELOAD = True, SEND_FILE_MAX_AGE_DEFAULT=0)
    app.run(port=3000)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print('Program Closed')
            sys.exit(1)
