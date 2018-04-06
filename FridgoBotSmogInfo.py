import datetime
import time

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)

import urllib.request
from requests import ConnectionError
import requests
import urllib3
import io
import re


# running on telegram fridgobot
updater = Updater(token='TOKEN')
dispatcher = updater.dispatcher
jq = updater.job_queue

# user management
users = []

def start(bot, update):
	if update.message.chat_id not in users:
		users.append(update.message.chat_id)
		print(update.message.chat_id)
		bot.send_message(chat_id=update.message.chat_id, text='- Feinsaubalarm abonniert -')
	
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def stop(bot, update):
	users.remove(update.message.chat_id)

stop_handler = CommandHandler('stop', stop)
dispatcher.add_handler(stop_handler)
updater.start_polling()


def callback(bot, job):

	# download info from page and cut
	try:
		stuttgartPage = urllib.request.urlopen("https://www.stuttgart.de/feinstaubalarm/widget/wider", data = None)
		f = io.TextIOWrapper(stuttgartPage,encoding='utf-8')
		wholeHTML = f.read()
		print("Get info from https://www.stuttgart.de/feinstaubalarm/widget/wider")
		findFeinstaub = re.search('<h2><span class="hl-aktuell hl-light">(.+?)</span> Feinstaub<br>Alarm', wholeHTML).group(1)
		sendMessageText = 'Guten Morgen! \n<b>' + findFeinstaub + ' Feinsaubalarm in Stuttgart.</b>'
	except AttributeError:
		findFeinstaub = wholeHTML # apply your error handling
	except Exception as e:
		print(e)
		sendMessageText = "cant reach server"


	# send info to all users that subscribed
	i = 0
	while i < len(users):
		fault = True
		try:
			print("try sending info to: " + str(users[i]) + "...")
			bot.send_message(chat_id=users[i], text=sendMessageText, parse_mode= 'HTML')
			print("...successful")
			fault = False # i = i + 1
		except Unauthorized:
			print("user canceled request - remove user from list: " + users[i])
			users.remove(users[i])
			fault = True
		except ConnectionError:
			print("... connection error: retry sending...")
			time.sleep(3)
			bot.send_message(chat_id=users[i], text=sendMessageText, parse_mode= 'HTML')
			print("...successful")
			fault = False # i = i + 1
		except ConnectionResetError:
			print("... connection reset error: retry sending...")
			time.sleep(3)
			bot.send_message(chat_id=users[i], text=sendMessageText, parse_mode= 'HTML')
			print("...successful")
			fault = False # i = i + 1
		except Exception as ex:
			print(ex)
			print("...retry sending...")
			time.sleep(3)
			bot.send_message(chat_id=users[i], text=sendMessageText, parse_mode= 'HTML')
			print("...successful")
			fault = False # i = i + 1
		
		if not fault:
			i = i + 1

		fault = True



# run job once at current daytime
myDate = datetime.time(17, 5, 0) 

job_daily = jq.run_daily(callback, myDate)

#run_repeating(callback, interval, first=None, context=None, name=None)
#run_daily(callback, time, days=(0, 1, 2, 3, 4, 5, 6), context=None, name=None)
