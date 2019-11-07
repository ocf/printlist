import functools
import os
import sys
import redis
from configparser import ConfigParser
from select import poll
from select import POLLERR
from select import POLLHUP
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

def parse_printer(status_message):
    return status_message.split()[-1].strip('.')

printer_dict = {'logjam': ['test_user1'], 'pagefault': ['test_user2'], 'papercut': ['test_user3']}

def add_to_printer_dict (username, printer):
    if printer == 'logjam':
        printer_dict['logjam'].append(username)
    elif printer == 'pagefault':
        printer_dict['pagefault'].append(username)
    elif printer == 'papercut':
        printer_dict['papercut'].append(username)

def main():
    username = os.environ.get('USER')

    # read config file
    host, password = 'broker.ocf.berkeley.edu', '###'

    # set up stdout monitoring
    p = poll()
    p.register(sys.stdout.fileno(), POLLERR | POLLHUP)

    s = subscribe(host, password, username)
    while True:
        message = s.get_message()
        if message and 'data' in message:
            status_message = message['data'].decode(encoding='UTF-8').replace('\n', ' ')
            test_file = open('testfile.txt', 'w')
            print(username + ' | ' + parse_printer(status_message) + '\n', file = test_file, flush=True)
            test_file.close()
            add_to_printer_dict(username, parse_printer(status_message))
        if p.poll(0.1):
            break

if __name__ == "__main__":
    main()

app = Flask(__name__)

@app.route('/')
def home():
    return printer_dict
    #return ', '.join(printer_dict['logjam'])

@app.route('/logjam')
def logjam():
    return render_template('logjam.html')

@app.route('/papercut')
def papercut():
    return render_template('papercut.html')

@app.route('/pagefault')
def pagefault():
    return render_template('pagefault.html')
