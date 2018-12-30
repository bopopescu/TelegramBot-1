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
import collections
import enum
import ast
import psycopg2
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent
from telepot.namedtuple import InlineQueryResultPhoto
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import xml.etree.ElementTree as ET

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def infl(val, a1, a2, a3):
	if val == 1:
		return a1
	if val > 1 and val < 5:
		return a2
	return a3

def operation(vr1, op, vr2):
	if(op == '+'):		
		if(isinstance(vr1, int)):
			return vr1 + int(vr2)
		elif(vr1.isdigit()):
			return int(vr1) + int(vr2)
		else:
			return vr1 + vr2
	if(op == '-'):
		if(isinstance(vr1, int)):
			return vr1 - int(vr2)
	return 0

class MyList(collections.MutableSequence):
	def __init__(self, l=[]):
		if type(l) is not list:
			raise ValueError()
		self._inner_list = l

	def __len__(self):
		return len(self._inner_list)

	def __delitem__(self, index):
		self._inner_list.__delitem__(index - 1)

	def insert(self, index, value):
		self._inner_list.insert(index - 1, value)

	def __setitem__(self, index, value):
		found = self.Where(lambda x: x.name == index)
		if not found is None:
			return found._set(value)
		self._inner_list.__setitem__(index - 1, value)

	def __getitem__(self, index):
		found = self.Where(lambda x: x.name == index)
		if not found is None:
			return found._get()
		return self._inner_list.__getitem__(index - 1)

	def Where(self, action):
		for item in self._inner_list:
			if action(item):
				return item
		return None

	def print(self):
		print(self._inner_list)

#Variable context
class VariableType(enum.Enum):
	DEFAULT = 1
	GLOBAL = 2
	DATABASE = 3
	GLOBALDATABASE = 4
	SYSTEM = 5

class Variable():	
	def __init__(self, _type, name, value = "", userid = -1):
		self._type = _type
		self.name = name
		self.value = value
		self.userid = userid

	def _get(self):
		usrid = self.userid
		if(self._type == VariableType.GLOBALDATABASE):
			usrid = -1
		if(self._type == VariableType.SYSTEM):
			usrid = -2

		if self._type == VariableType.DATABASE or self._type == VariableType.GLOBALDATABASE or self._type == VariableType.SYSTEM:			
			cursor.execute("SELECT value FROM variables WHERE name='{}' AND userid={}".format(self.name, usrid))
			data = cursor.fetchone()
			if not data is None:			
				self.value, = data
		
		if self._type == VariableType.GLOBAL:
			self.value = Global.defaultVariableContext.Where(lambda x: x == self.name)._get()
		
		if self._type == VariableType.DEFAULT:
			pass
		
		return self.value
	
	def _set(self, value):
		if self._type == VariableType.DEFAULT:
			self.value = value
		elif self._type == VariableType.DATABASE or self._type == VariableType.SYSTEM or self.userid == -1:
			usrid = self.userid
			if self._type == VariableType.SYSTEM:
				usrid = -2

			cursor.execute("SELECT value FROM variables WHERE name='{}' AND userid={}".format(self.name, usrid))
			data = cursor.fetchone()
			if not data is None:			
				query = ("UPDATE variables SET value = ? WHERE name = ? AND userid = ?")
				cursor.execute(query, (value, self.name, usrid))
				cnx.commit()
			else:
				query = ("INSERT INTO variables (userid, name, value) VALUES (?, ?, ?)")
				cursor.execute(query, (usrid, self.name, str(value)))
				cnx.commit()
			self.value = value
		elif self._type == VariableType.GLOBAL:
			Global.defaultVariableContext.Where(lambda x: x.name == self.name)._set(value)

def initializeVariables(userid):
	return MyList([
		Variable(VariableType.GLOBAL, 'maxcount', 30, userid), 
		Variable(VariableType.DATABASE, 'actualcount', 0, userid), 
	])

class UserTracker(telepot.aio.Bot):
	def __init__(self, seed_tuple):
		super(UserTracker, self).__init__(seed_tuple)
		self.users = {}
		self.userVars = {}

	@asyncio.coroutine
	def on_callback_query(self, msg):
		query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
		chat_id = msg['message']['chat']['id']
		if 'username' in msg['from']:
			mylogin = msg['from']['username']
		else:
			mylogin = msg['from']['first_name']

		if( mylogin not in self.users ):
			self.users[mylogin] = msg['from']['id']
			self.userVars[mylogin] = initializeVariables(self.users[mylogin])
		
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
		if 'username' in msg['from']:
			mylogin = msg['from']['username']
		else:
			mylogin = msg['from']['first_name']

		if content_type != 'new_chat_member' and content_type != 'left_chat_member':
			if( mylogin not in self.users ):
				self.users[mylogin] = msg['from']['id']
				self.userVars[mylogin] = initializeVariables(self.users[mylogin])

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
				yield from bot.sendMessage(chat_id, '<b>'+str(msg['from']['first_name'])+'</b> už vypil '+str(self.userVars[mylogin]['actualcount'])+' '+str(infl(int(''+str(self.userVars[mylogin]['actualcount'])+''), 'kafe', 'kafe', 'kafí'))+'.\n'+str(time.strftime('%d.%m.%Y'))+'', parse_mode = 'html', reply_to_message_id = msg['message_id'], reply_markup = keyboard)
				
				
				
				

class Global:
	defaultVariableContext = MyList([])

def generateTable(hash):
	query = ("CREATE TABLE IF NOT EXISTS `variables` (`userid` INT NOT NULL, `name` VARCHAR(200) NOT NULL, `value` TEXT, PRIMARY KEY(userid,name));")
	cursor.execute(query)
	cnx.commit()

	Global.defaultVariableContext = initializeVariables(-1)

	versionDatabase = Variable(VariableType.SYSTEM, "dbversion")
	if(hash != versionDatabase._get()):
		print("New hash is '"+hash+"' the old is '"+versionDatabase._get()+"' updating global variables...")
		for var in Global.defaultVariableContext:
			var._set(var.value)
		versionDatabase._set(hash)

TOKEN = '174152039:AAFAeOHYO07KWdMm3yz3nWHaYAZm_ZlAWMA'

print('Version of the bot: 2.1')
print('Opening connection to LocalDB ...')

global data, events, cursor, cnx
#cnx = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='snowleopard')
#cnx = sqlite3.connect('local.db')
cnx = psycopg2.connect( host='ec2-54-225-150-216.compute-1.amazonaws.com', user='eriwbvlfdnqwgx', password='0b52612d34cf15404fcc4ca5750f18ddf0e2fa7b8be6aba43fb352de7f950575', dbname='d9905fj1co10al' )
cursor = cnx.cursor()

print('Checking database ...')
generateTable("e2f9b78f3dc7a71be67b994dc98cb72714d7eb40")

bot = UserTracker(TOKEN)

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop())

print('Listening ...')
loop.run_forever()

#Close MySQL
print('Closing connection to MySQL ...')
cursor.close()
cnx.close()
	