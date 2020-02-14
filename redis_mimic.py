import json
import random
import string
import time
printers = ('printer-logjam', 'printer-pagefault', 'printer-papercut')
jobIds = 0


def newId():
    global jobIds
    jobIds += 1
    return jobIds


def randUsername():
    return ''.join([random.choice(string.ascii_lowercase) for _ in range(10)])


def addJob():
    rand = random.randrange(len(printers))
    return {
        'channel': printers[rand],
        'data': json.dumps({
            'user': randUsername(),
            'time': time.time(),
            'status': 0,
            'id': newId()
        })
        # 'channel': printers[rand].encode(),
        # 'data': randUsername().encode()
    }


def mimic_sub(*args):
    return mimic


class mimic:
    @staticmethod
    def get_message():
        time.sleep(1)
        return addJob()
