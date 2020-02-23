import json
import random
import string
import time
import copy
from config import Config

CONFIG = Config('conf/mimic.yaml')

printers = tuple('printer-' + name for name in CONFIG.printers.names)
jobIds = 0
currentPending = []

def newId():
    global jobIds
    jobIds += 1
    return jobIds


def randUsername():
    return ''.join([random.choice(string.ascii_lowercase) for _ in range(CONFIG.redis_mimic.name_length)])


def addJob():
    rand = random.randrange(len(printers))
    tempId = newId()
    tempStatus = random.randrange(CONFIG.redis_mimic.status_code_range)
    completeOne = random.randrange(2)
    if not(completeOne) and len(currentPending) != 0:
        completed = currentPending.pop(0)
        completed['data']['time'] = time.time()
        completed['data']['status'] = 0
        print(completed['data'])
        completed['data'] = json.dumps(completed['data'])
        return completed
    else:
        tempData = {
            'channel': printers[rand],
            'data': {
                'user': randUsername(),
                'time': time.time(),
                'status': tempStatus,
                'id': tempId
            }
        }
        if tempStatus == 1:
            currentPending.append(tempData)
        returnedData = copy.deepcopy(tempData)
        returnedData['data'] = json.dumps(returnedData['data'])
        return returnedData


def mimic_sub(*args):
    return mimic


class mimic:
    @staticmethod
    def get_message():
        time.sleep(CONFIG.redis_mimic.refresh_rate)
        return addJob()
