#meant to be run in interactive mode
import functools
import os
import sys
import redis

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

def monitor_printer(printer):
    host, password = 'broker.ocf.berkeley.edu', '###'

    s = subscribe(host, password, 'printer-' + printer)
    while True:
        message = s.get_message()
        if message and 'data' in message:
            username = message['data'].decode(encoding='UTF-8').replace('\n', ' ')
            print(username)
