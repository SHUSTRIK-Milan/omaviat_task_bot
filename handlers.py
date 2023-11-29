import json
import datetime
from bot import bot, connect
import telebot
import keyboard
import config

class Group:
    def __init__(self, id, name, items, admins):
        self.id = id
        self.name = name
        self.items = items
        self.admins = admins

class User:
    def __init__(self, id, username, admin = False):
        self.id = id
        self.username = username
        self.admin = admin

class Session:
    def __init__(self, start, user, group = None, data = [], id = None, backward = []):
        self.id = id
        self.start = start
        self.user = user
        self.group = group
        self.data = data
        self.backward = backward

sessions = {}

def get_task_ondate(session, day = None, mounth = None):
    output = []
    connection = connect(
        host="localhost",
        user="root",
        password="",
        database="hometask",
    )
    cursor = connection.cursor()
    if day and mounth:
        cursor.execute("SELECT * FROM `tasks` WHERE `group_id` = '" + str(session.group.id) + "' AND `date` = '" + str(datetime.date(datetime.datetime.today().timetuple().tm_year, mounth, day)) + "';")
    else:
        cursor.execute("SELECT * FROM `tasks` WHERE `group_id` = '" + str(session.group.id) + "';")
    
    result = cursor.fetchall()
    for row in result:
        output.append(row)
    return output

def fadusha_mama(tasks):
    output = {}
    
    for item in tasks:
        id = item[4]

        if not output.get(id):
            output[id] = []
        output[id].append(item)
    return output

@bot.message_handler(commands=['start'])
def send_welcome(message):
    registered = False
    user_id = 0

    connection = connect(
        host="localhost",
        user="root",
        password="",
        database="hometask",
    )

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `users` WHERE `user_id` = " + str(message.chat.id) + ";")
    result = cursor.fetchall()
    if result:
        registered = True

    if not registered:
        insert = """
        INSERT INTO `users`(`user_id`, `username`)
        VALUES (%s, %s)
        """

        cursor.executemany(insert, [(message.chat.id, message.chat.username or message.chat.first_name or "unnamed")])
        connection.commit()
        cursor.execute("SELECT * FROM `users` WHERE `user_id` = " + str(message.chat.id) + ";")
        registered = True

    groups = []
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `groups` WHERE 1")
    result = cursor.fetchall()
    for group in result:
        item = telebot.types.InlineKeyboardButton(group[1], callback_data="group_"+str(group[0]))
        if len(groups) % 3 == 0:
            groups.append([item])
        else:
            groups[-1].append(item)
    groups_markup = telebot.types.InlineKeyboardMarkup(groups)
    
    user = User(message.chat.id, message.chat.username or message.chat.first_name or "unnamed")
    start = bot.send_message(chat_id=message.chat.id, text="Выберите группу!", reply_markup=groups_markup)
    session = Session(start, user)
    sessions[session.start.chat.id] = session

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    session = sessions.get(call.message.chat.id)
    if not session: return
    s_call = call.data.split(config.SPLIT)

    connection = connect(
        host="localhost",
        user="root",
        password="",
        database="hometask",
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM `users` WHERE `user_id` = " + str(call.message.chat.id) + ";")
    user = cursor.fetchall()

    if s_call[0] == "group":
        cursor.execute("SELECT * FROM `groups` WHERE `id` = " + str(s_call[1]) + ";")
        result = cursor.fetchall()
        if not result:
            return
        
        group = Group(result[0][0], result[0][1], json.loads(result[0][2]), json.loads(result[0][3]))
        session.group = group
        session.user.admin = False

        for admin in group.admins:
            if admin == user[0][0]:
                session.user.admin = True
                break
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Выберите действие!", reply_markup=keyboard.start_markup(session.user))
    elif call.data == "debug":
        debug_markup = [[keyboard.id_check], [keyboard.back, keyboard.full_back]]
        if session.user.id == 876993119:
            debug_markup.insert(0, [keyboard.admin_set, keyboard.admin_delete])
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Выберите действие!", reply_markup=telebot.types.InlineKeyboardMarkup(debug_markup))
    elif call.data == "id_check":
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text=str(user[0][0]), reply_markup=keyboard.back_markup)
    elif call.data == "check":
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Посмотрите Д/З на сегодня или выберите дату", reply_markup=keyboard.check_markup)
    elif call.data == "delete":
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Удалите Д/З на сегодня или выберите дату", reply_markup=keyboard.delete_markup)
    elif s_call[0] == "date":
        def tasks_menu(tasks):
            if len(tasks) > 0:
                tasks_sort = fadusha_mama(tasks)
                tasks_buttons = []
                keys = list(tasks_sort.keys())
                for id in range(0, len(keys)):
                    item = telebot.types.InlineKeyboardButton(session.group.items[keys[id]], callback_data="task_"+str(keys[id])+"_"+s_call[2])
                    if id % 2 == 0:
                        tasks_buttons.append([item])
                    else:
                        tasks_buttons[-1].append(item)
                tasks_buttons.append([keyboard.back, keyboard.full_back])
                tasks_markup = telebot.types.InlineKeyboardMarkup(tasks_buttons)

                session.data = [tasks_sort]

                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Выберите предмет!", reply_markup=tasks_markup)
            else:
                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="На эту дату домашнего задания нет. Возрадуйтесь!", reply_markup=keyboard.back_markup)
        if s_call[1] == "select":
            def process_date_step(message):
                try:
                    date = message.text
                    date = date.split(".")

                    if len(date) == 2:
                        date = datetime.date(datetime.datetime.today().timetuple().tm_year, int(date[1]), int(date[0]))

                        tasks = get_task_ondate(session, date.timetuple().tm_mday, date.timetuple().tm_mon)
                        tasks_menu(tasks)
                    else:
                        raise Exception("incorrect date")
                except Exception as e:
                    bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Неверная дата", reply_markup=keyboard.back_markup)
                    print(e)
                bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            bot.register_next_step_handler(session.start, process_date_step)
            bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Напишите дату, на которую задана домашняя работа в подобном формате: 22.09", reply_markup=keyboard.back_markup)
        elif s_call[1] == "today":
            tasks = get_task_ondate(session, datetime.datetime.today().timetuple().tm_mday, datetime.datetime.today().timetuple().tm_mon)
            tasks_menu(tasks)
        elif s_call[1] == "next":
            tasks = get_task_ondate(session, (datetime.datetime.today()+datetime.timedelta(days=1)).timetuple().tm_mday, (datetime.datetime.today()+datetime.timedelta(days=1)).timetuple().tm_mon)
            tasks_menu(tasks)
        elif s_call[1] == "all":
            tasks = get_task_ondate(session)
            tasks_menu(tasks)
    elif call.data == "add":
        items = []
        for id in range(0, len(session.group.items)):
            item = telebot.types.InlineKeyboardButton(session.group.items[id], callback_data="item_"+str(id))
            if id % 2 == 0:
                items.append([item])
            else:
                items[-1].append(item)
        items.append([keyboard.back, keyboard.full_back])
        add_markup = telebot.types.InlineKeyboardMarkup(items)

        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Выберите предмет!", reply_markup=add_markup)
    elif s_call[0] == "item":
        task = {
			"user_id": session.start.chat.id,
            "group_id": session.group.id,
			"item": int(s_call[1])
		}

        def process_date_step(message):
            try:
                date = message.text
                date = date.split(".")
                print(date)

                if len(date) == 2:
                    date = datetime.datetime(datetime.datetime.today().timetuple().tm_year, int(date[1]), int(date[0]))
                    print(date)
                    #if date.timestamp() < datetime.datetime.today().timestamp():
                    #    raise Exception("incorrect date")
                    
                    task["date"] = date

                    bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Напишите текст задания", reply_markup=keyboard.back_markup)
                    bot.register_next_step_handler(session.start, process_text_step)
                else:
                    raise Exception("incorrect date")
            except Exception as e:
                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Неверная дата", reply_markup=keyboard.back_markup)
                print(e)
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        def process_text_step(message):
            try:
                if message.chat.id == session.start.chat.id:
                    bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Супер! Вы записали домашнее задание для группы", reply_markup=keyboard.back_markup)
                    task["description"] = message.text

                    insert = """
                    INSERT INTO `tasks`(`date`, `user_id`, `group_id`, `item`, `description`)
                    VALUES (%s, %s, %s, %s, %s)
                    """

                    cursor = connection.cursor()
                    cursor.executemany(insert,
                        [(task["date"], task["user_id"], task["group_id"], task["item"], task["description"])])
                    connection.commit()
                else:
                    raise Exception("incorrect date")
            except Exception as e:
                print(e)
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        bot.register_next_step_handler(session.start, process_date_step)
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Напишите дату, на которую задана домашняя работа в подобном формате: 22.09", reply_markup=keyboard.back_markup)
    elif s_call[0] == "task":
        tasks = session.data[0][int(s_call[1])]

        if s_call[2] == "check":
            text = "Домашнее задание по " + session.group.items[int(s_call[1])] + "\n\n"
            for i in range(0, len(tasks)):
                task = tasks[i]

                date = str(tasks[i][1])
                date = date.split(" ")[0]
                date = date.split("-")
                date.reverse()
                date = ".".join(date)

                text += str(date) + "\n" + str(task[5]) + "\n\n"
            try:
                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text=text, reply_markup=keyboard.back_markup)
            except:
                pass
        else:
            for i in range(0, len(tasks)):
                task = tasks[i]
                delete = """
                DELETE FROM `tasks` WHERE `id` = %s
                """%task[0]

                cursor = connection.cursor()
                cursor.execute(delete)
                connection.commit()
            
            try:
                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Отлично! Вы удалили домашнее задание для группы", reply_markup=keyboard.back_markup)
            except:
                pass
    elif s_call[0] == "admin":
        def process_id_step(message):
            try:
                id = int(message.text)

                if s_call[1] == "set":
                    session.group.admins.append(id)
                elif s_call[1] == "delete":
                    session.group.admins.remove(id)
                update_query = "UPDATE `groups` SET `admins`='" + json.dumps(session.group.admins) + "' WHERE `id` = " + str(session.group.id) + ";"
                cursor = connection.cursor()
                cursor.execute(update_query)
                connection.commit()

                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Успешно! Вы изменили права пользователя", reply_markup=keyboard.back_markup)
            except Exception as e:
                bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Неверный ID", reply_markup=keyboard.back_markup)
                print(e)
            bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)    
        
        bot.register_next_step_handler(session.start, process_id_step)
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text="Напишите ID пользователя", reply_markup=keyboard.back_markup)
    if call.data == "back":
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text=session.backward[-1][0], reply_markup=session.backward[-1][1])
        session.backward.pop()
    elif call.data == "fullback":
        bot.edit_message_text(chat_id=session.start.chat.id, message_id=session.start.message_id, text=session.backward[-1][0], reply_markup=keyboard.start_markup(session.user))
        first = session.backward[0]
        session.backward = [first]
    else:
        session.backward.append([call.message.text, call.message.reply_markup])