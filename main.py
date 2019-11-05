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

BROKER_AUTH = '/opt/share/broker/broker.conf'

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

def main():
    username = os.environ.get('USER')

    # read config file
    host, password = read_config()

    # set up stdout monitoring
    p = poll()
    p.register(sys.stdout.fileno(), POLLERR | POLLHUP)

    s = subscribe(host, password, username)
    while True:
        message = s.get_message()
        if message and 'data' in message:
            status_message = message['data'].decode(encoding='UTF-8').replace('\n', ' ')
            test_file = open('testfile.txt', 'w')
            print(status_message, file = test_file, flush=True)
            test_file.close()
        if p.poll(0.1):
            break

if __name__ == "__main__":
    main()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")