import functools
import os
import sys
import redis
from multiprocessing import Process
from flask import Flask
from flask import render_template

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

printer_dict = {'logjam': ['test_user1'], 'pagefault': ['test_user2'], 'papercut': ['test_user3']}

def pop_user(printer, username):
    printer_dict[printer].append(username)

def monitor_printer(printer):
    host, password = 'broker.ocf.berkeley.edu', '###'

    s = subscribe(host, password, 'printer-' + printer)
    while True:
        message = s.get_message()
        if message and 'data' in message:
            username = message['data'].decode(encoding='UTF-8').replace('\n', ' ')
            pop_user(printer, username)

if __name__ == '__main__':
    p1 = Process(target = monitor_printer('logjam'))
    p1.start
    p2 = Process(target = monitor_printer('pagefault'))
    p2.start
    p3 = Process(target = monitor_printer('papercut'))
    p3.start

app = Flask(__name__)

@app.route('/')
def home():
    return printer_dict