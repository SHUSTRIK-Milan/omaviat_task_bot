import telebot
import config

back = telebot.types.InlineKeyboardButton('↩', callback_data='back')
full_back = telebot.types.InlineKeyboardButton('⏬', callback_data='fullback')

check = telebot.types.InlineKeyboardButton('👀 Посмотреть', callback_data='check')
add = telebot.types.InlineKeyboardButton('✅ Добавить', callback_data='add')
delete = telebot.types.InlineKeyboardButton('❌ Удалить', callback_data='delete')
debug = telebot.types.InlineKeyboardButton('⚙ Отладка', callback_data='debug')
admin_set = telebot.types.InlineKeyboardButton('🎟 Назначить админом', callback_data='admin_set')
admin_delete = telebot.types.InlineKeyboardButton('💥 Отозвать админа', callback_data='admin_delete')
id_check = telebot.types.InlineKeyboardButton('🆔 Посмотреть ID', callback_data='id_check')

today_check = telebot.types.InlineKeyboardButton('☀ Сегодня', callback_data='date_today_check')
next_check = telebot.types.InlineKeyboardButton('🌙 Завтра', callback_data='date_next_check')
date_check = telebot.types.InlineKeyboardButton('📅 Выбрать дату', callback_data='date_select_check')
all_check = telebot.types.InlineKeyboardButton('📟 Отобразить всё', callback_data='date_all_check')

today_delete = telebot.types.InlineKeyboardButton('☀ Сегодня', callback_data='date_today_delete')
next_delete = telebot.types.InlineKeyboardButton('🌙 Завтра', callback_data='date_next_delete')
date_delete = telebot.types.InlineKeyboardButton('📅 Выбрать дату', callback_data='date_select_delete')
all_delete = telebot.types.InlineKeyboardButton('📟 Отобразить всё', callback_data='date_all_delete')

def start_markup(user):
    if user.admin:
        return telebot.types.InlineKeyboardMarkup([[check, add, delete], [debug, back]])
    else:
        return telebot.types.InlineKeyboardMarkup([[check], [debug, back]])

check_markup = telebot.types.InlineKeyboardMarkup([[today_check, next_check], [date_check, all_check], [back, full_back]])
delete_markup = telebot.types.InlineKeyboardMarkup([[today_delete, next_delete], [date_delete], [back, full_back]])
back_markup = telebot.types.InlineKeyboardMarkup([[back, full_back]])