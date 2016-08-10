import telebot
from telebot import types
import configparser
import copy
import time

class MiniChat:
	def __init__(self, title):
		self.title = title
		self.messages = []
		
	def add_message(self, message):
		self.messages.append(message)
		
	def as_string(self):
		return '*{}*\n'.format(self.title) + '\n'.join(self.messages[-10:])

since = int(time.time())

# get config
config = configparser.ConfigParser()
config.read("ch4tbot.cfg")

# get bot
bot = telebot.TeleBot(config['telegram_bot_api']['telegram_token'])

# group id -> message id
active_chat = {}

# message id -> minichat
chats = {}

# user id -> string
current_message = {}

# ,inichat name -> ,minichat
chats_by_name = {}

# minichat -> list of message ids to update
minichats_to_messages = {}

markup = types.InlineKeyboardMarkup()
markup.row(types.InlineKeyboardButton(callback_data="send", text="send >>"))
						
@bot.message_handler(commands=['newchat'])
def new_chat(message):
	title = message.text.replace('/newchat', '')
	if title and title[0] == ' ':
		title = title[1:]
	if not title:
		title = str(int(time.time()))

	chat_id = message.chat.id
	chat = MiniChat(title)
	out = bot.send_message(chat_id, chat.as_string(), 
			reply_markup=markup, parse_mode="Markdown")
			
	# add chats
	active_chat[chat_id] = chat
	chats[out.message_id] = chat
	chats_by_name[title] = chat
	if chat not in minichats_to_messages:
		minichats_to_messages[chat] = []
	minichats_to_messages[chat].append(out)

@bot.callback_query_handler(func=lambda call: call.message.date>since and call.message.message_id in chats)
def call(call):		
	key = call.from_user.id
	if key not in current_message or not current_message[key]:
		return
	chat = chats[call.message.message_id]
	chat.add_message("*{}*: {}".format(call.from_user.first_name, current_message[key]))
	update_minichat(chat)
	current_message[key] = None

@bot.inline_handler(lambda query: True)
def query_text(inline_query):
	current_message[inline_query.from_user.id] = inline_query.query
	
@bot.message_handler(commands = ['openchat'])
def open_chat(message):
	space_location = message.text.find(' ')
	if space_location == -1 or len(message.text) < space_location + 2:
		return
	chat_name = message.text[space_location + 1:]
	if chat_name not in chats_by_name:
		return
	chat = chats_by_name[chat_name]
	
	out = bot.send_message(message.chat.id, chat.as_string(), 
		reply_markup=markup, parse_mode="Markdown")

	active_chat[message.chat.id] = chat
	chats[out.message_id] = chat
	if chat not in minichats_to_messages:
		minichats_to_messages[chat] = []
	minichats_to_messages[chat].append(out)


def update_minichat(minichat):
	if minichat not in minichats_to_messages:
		return
	for message in minichats_to_messages[minichat]:
		bot.edit_message_text(minichat.as_string(),
				message_id=message.message_id, chat_id=message.chat.id,
				reply_markup=markup, parse_mode='Markdown')


bot.polling()

	
