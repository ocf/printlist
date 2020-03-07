import functools
import json
import os
import sys
import threading
import time
from configparser import ConfigParser
from enum import Enum

import redis
from flask import Flask
from flask import jsonify
from flask import render_template
from flask import request
from config import Config

CONFIG = Config()

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


class PrintJob(Enum):
    COMPLETED = 0
    PENDING = 1
    FILE_ERROR = 2
    QUOTA_LIMIT = 3
    JOB_ERROR = 4


class Job():
    """
    print_jobs = {
        'printer_name': {
            'job_id': <Job Object> {
                username: 'some username',
                id: 'job_id',
                last_updated: 'time of last update to status',
                status: [('oldest status', 'timestamp'), ('newest status', 'timestamp')]
            }
        }
    }
    """
    print_jobs = {name: {} for name in CONFIG.PRINTERS.NAMES}    
    def cleanup():
        def notdone(job):
            status = job.current_status()
            if status == PrintJob.COMPLETED:
                return job.last_updated + CONFIG.PERSIST_TIME.COMPLETED > time.time()
            elif status == PrintJob.PENDING:
                return job.last_updated + CONFIG.PERSIST_TIME.DEFAULT > time.time()
            return job.last_updated + CONFIG.PERSIST_TIME.ERROR > time.time()
        
        Job.print_jobs = {
            printer: {
                id: job for id, job in jobs.items() if notdone(job)
            } for printer, jobs in Job.print_jobs.items()
        }

    def get_recent(time):
        jobs = {}
        for printer_name, printer in Job.print_jobs.items():
            jobs[printer_name] = [job.object_wrap() for job_id, job in printer.items() if job.last_updated > time]
        return jobs

    def process(printer_name, username, time, status, job_id):
        if job_id in Job.print_jobs[printer_name]:
            Job.print_jobs[printer_name][job_id].update(username, status, time)
        else:
            Job.print_jobs[printer_name][job_id] = Job(username, time, status, job_id)
        Job.cleanup()

    def __init__(self, username, time, status, job_id):
        self.username = username
        self.id = job_id
        self.last_updated = time
        self.status_queue = [(status, time)]

    def update(self, username, status, time):
        if username != self.username:
            print("Conflict: Job#" + job_id + " | " +
                  self.username + " vs " + username)
            return False
        self.status_queue.append((status, time))
        self.last_updated = time
        return True

    def current_status(self):
        return self.status_queue[-1][0]

    def object_wrap(self):
        temp = {
            'username': self.username,
            'id': self.id,
            'last_updated': self.last_updated,
            'status': self.current_status()
        }
        return temp


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

    s = subscribe(host, password, *(['printer-' + printer_name for printer_name in CONFIG.PRINTERS.NAMES]))
    while True:
        message = s.get_message()
        if message and 'data' in message:
            try:
                printer_name = message['channel'].replace('printer-', '')
                print_job = json.loads(message['data'])
                Job.process(
                    printer_name=printer_name,
                    username=print_job['user'],
                    time=print_job['time'],
                    status=print_job['status'],
                    job_id=print_job['id']
                )
            except ValueError:
                print('Unable to parse JSON')
            except KeyError:
                print('Missing fields')


def create_app():
    app = Flask(__name__)
    monitor_process = threading.Thread(target=monitor_printer)
    monitor_process.daemon = DEV_MODE
    monitor_process.start()
    return app


if DEV_MODE:
    print('Developer Mode Enabled')
    def read_config(): return (None, None)
    from redis_mimic import mimic_sub
    subscribe = mimic_sub

app = create_app()


@app.route('/')
def home():
    return render_template('full.html', printer_names=CONFIG.PRINTERS.NAMES)


@app.route('/reload/recent')
def reload():
    if not request.args.get('last-fetch', '').isdigit():
        return 'Invalid Request', 400
    last_fetch = int(request.args.get('last-fetch'))/1000
    return jsonify(Job.get_recent(last_fetch))

@app.route('/configuration')
def config():
    return jsonify(CONFIG.PERSIST_TIME.__dict__)


if DEV_MODE:
    app.config.update(TEMPLATES_AUTO_RELOAD=True, SEND_FILE_MAX_AGE_DEFAULT=0)
    app.run(port=3000)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print('Program Closed')
            sys.exit(1)
