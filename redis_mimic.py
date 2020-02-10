import random
import time
import string
printers = ('printer-logjam', 'printer-pagefault', 'printer-papercut')

def randUsername():
    return ''.join([random.choice(string.ascii_lowercase) for _ in range(10)])

def addJob():
    rand = random.randrange(len(printers))
    return {
        'channel': printers[rand].encode(encoding='UTF-8'),
        'data': randUsername().encode(encoding='UTF-8')
    }

def mimic_sub(*args):
    return mimic

class mimic:
    @staticmethod
    def get_message():
        time.sleep(5)
        return addJob()
