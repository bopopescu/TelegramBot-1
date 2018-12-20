# -*- coding: utf-8 -*-
import sys
import os
import asyncio
import time
import random
import mysql.connector
import sqlite3
import threading
import requests
import string
import telepot
import telepot.aio
import os.path
import re
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent
from telepot.namedtuple import InlineQueryResultPhoto
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import xml.etree.ElementTree as ET

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def operation(vr1, op, vr2):
	if(op == '+'):
		if(isinstance(vr1, int)):
			return vr1 + int(vr2)
		else:
			return vr1 + vr2
	if(op == '-'):
		if(isinstance(vr1, int)):
			return vr1 + int(vr2)
	return 0

def initializeVariables():
	return {
			'maxcount': 30,
			'actualcount': 0,
			}

class UserTracker(telepot.aio.Bot):
	def __init__(self, seed_tuple):
		super(UserTracker, self).__init__(seed_tuple)
		self.users = {}
		self.userVars = {}

	@asyncio.coroutine
	def on_callback_query(self, msg):
		query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
		chat_id = msg['message']['chat']['id']
		mylogin = msg['from']['username']
		print('Callback Query:', query_id, from_id, query_data)

		if(query_data == 'btn_kafe_1'):
			self.userVars[mylogin]['actualcount'] = operation(self.userVars[mylogin]['actualcount'], '+', 1)
			yield from bot.answerCallbackQuery(query_id, text = 'Již jsi vypil '+str(self.userVars[mylogin]['actualcount'])+'', show_alert = False)

		if(query_data == 'btn_kafe_2'):
			self.userVars[mylogin]['actualcount'] = operation(self.userVars[mylogin]['actualcount'], '+', 2)
			yield from bot.answerCallbackQuery(query_id, text = 'Již jsi vypil '+str(self.userVars[mylogin]['actualcount'])+'', show_alert = False)

		if(query_data == 'btn_kafe_reset'):
			self.userVars[mylogin]['actualcount'] = 0
			yield from bot.answerCallbackQuery(query_id, text = 'Počet vypitích kafí byl nastaven na 0', show_alert = True)


	@asyncio.coroutine
	def on_chat_message(self, msg):
		global cursor, cnx
		content_type, chat_type, chat_id = telepot.glance(msg)
		mylogin = msg['from']['username']

		if content_type != 'new_chat_member' and content_type != 'left_chat_member':
			if( mylogin not in self.users ):
				self.users[mylogin] = msg['from']['id']
				self.userVars[mylogin] = initializeVariables()

		if ('text' in msg) and (len(msg['text']) > 0):
			data_mess = msg['text'].split(' ');
		else:
			data_mess = []		

		if content_type == 'text':
			if data_mess[0] == '!count':
				args = {
					'amount': 1 if len(data_mess) < 2 else data_mess[1],
				}
				self.userVars[mylogin]['actualcount'] = operation(self.userVars[mylogin]['actualcount'], '+', args['amount'])

				keyboard = InlineKeyboardMarkup(inline_keyboard=[
					[
						InlineKeyboardButton(text = '+1 Kafe', callback_data = 'btn_kafe_1'),
						InlineKeyboardButton(text = '+2 Kafe', callback_data = 'btn_kafe_2')
					],
					[
						InlineKeyboardButton(text = 'Reset Kafe', callback_data = 'btn_kafe_reset')
					],
					[
						InlineKeyboardButton(text = 'Google', url = 'https://www.google.cz/search?q=kafe')
					]
				])
				yield from bot.sendMessage(chat_id, '<b>'+str(msg['from']['first_name'])+'</b> už vypil '+str(self.userVars[mylogin]['actualcount'])+' kafí.\n'+str(time.strftime('%d.%m.%Y'))+'', parse_mode = 'html', reply_to_message_id = msg['message_id'], reply_markup = keyboard)
				
				
				
				

TOKEN = '174152039:AAFAeOHYO07KWdMm3yz3nWHaYAZm_ZlAWMA'

print('Version of the bot: 2.1')
print('Opening connection to MySQL ...')

global data, events, cursor, cnx
#cnx = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='snowleopard')
cnx = sqlite3.connect('local.db')
cursor = cnx.cursor()

bot = UserTracker(TOKEN)

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop())

print('Listening ...')
loop.run_forever()

#Close MySQL
print('Closing connection to MySQL ...')
cursor.close()
cnx.close()
	