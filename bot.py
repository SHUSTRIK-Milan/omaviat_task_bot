import telebot
from mysql.connector import connect, Error
import config

bot = telebot.TeleBot(config.TOKEN)

connection = connect(
	host="localhost",
	user="root",
	password="",
	database="hometask",
)

print(connection)

import handlers