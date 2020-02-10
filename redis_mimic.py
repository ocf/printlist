import random
import time
printers = ('printer-logjam', 'printer-pagefault', 'printer-papercut')

def randUsername():
	username = ''
	while(len(username) < 10):
		username+=chr(random.randint(65, 90))
	return username

def addJob():
	print('job')
	rand = random.randint(0, len(printers)-1)
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