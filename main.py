import telebot
import sqlite3
import os
from telebot import types
from datetime import date
from dotenv import load_dotenv

load_dotenv()
My_Token = os.getenv('TOKEN')
bot = telebot.TeleBot(My_Token)

today = date.today()
today1 = str(today)
dtoday = today.strftime("%d/%m/%Y")

def add_birth_date_column():
    conn = sqlite3.connect('my_database.db')
    cur = conn.cursor()
    try:
        cur.execute('ALTER TABLE data ADD COLUMN birth_date TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()

add_birth_date_column()

@bot.message_handler(commands=['start'])
def start(message):
    global user_id
    user_id = message.from_user.id

    conn = sqlite3.connect('my_database.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            lastname TEXT,
            name TEXT,
            surname TEXT,
            birth_date TEXT,
            visit_date TEXT,
            contact TEXT
        )
    ''')
    conn.commit()
    conn.close()

    if message.text == '/start':
        my_message = f'Здравствуйте, <b>Dr.{message.from_user.first_name}</b>'
        bot.send_message(message.chat.id, my_message, parse_mode='html')

    send_main_menu(message)

def send_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton('Внести пациента'),
        types.KeyboardButton('Получить список за каждый день недели')
    )
    markup.row(
        types.KeyboardButton('Получить список пациентов за сегодня'),
        types.KeyboardButton('Удалить пациента по ID')
    )
    markup.row(
        types.KeyboardButton('Экспортировать в .txt'),
        types.KeyboardButton('Главное меню')
    )
    bot.send_message(message.chat.id, 'Держите список функций!', reply_markup=markup)
    bot.register_next_step_handler(message, branches)

@bot.message_handler(content_types=['text'])
def branches(message):
    if message.text == 'Внести пациента':
        bot.send_message(message.chat.id, 'Введите фамилию:')
        bot.register_next_step_handler(message, get_lastname)

    elif message.text == 'Получить список пациентов за сегодня':
        conn = sqlite3.connect('my_database.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM data WHERE tg_id = ? AND visit_date = ?', (user_id, today1))
        us = cur.fetchall()
        conn.close()

        ans = ""
        for i in us:
            ans += f'ID: {i[0]} | ФИО: {i[2]} {i[3]} {i[4]} | Дата рождения - {i[5]} | Контакт - {i[7]}\n'

        if not ans:
            ans = 'Сегодня не зарегистрировано пациентов.'

        bot.send_message(message.chat.id, ans)
        send_main_menu(message)

    elif message.text == 'Получить список за каждый день недели':
        conn = sqlite3.connect('my_database.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM data WHERE tg_id = ?', (user_id,))
        us = cur.fetchall()
        conn.close()

        ans = ""
        for i in us:
            if len(i) >= 7:
                ans += f'ID: {i[0]} | ФИО: {i[2]} {i[3]} {i[4]} | Дата рождения - {i[5]} | День посещения - {i[6]} | Контакт - {i[7]}\n'

        if not ans:
            ans = 'Нет данных.'

        bot.send_message(message.chat.id, ans)
        send_main_menu(message)

    elif message.text == 'Удалить пациента по ID':
        bot.send_message(message.chat.id, 'Введите ID пациента для удаления:')
        bot.register_next_step_handler(message, delete_by_id)

    elif message.text == 'Главное меню':
        send_main_menu(message)

    elif message.text == 'Экспортировать в .txt':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Экспортировать за сегодня'), types.KeyboardButton('Экспортировать за весь период'))
        bot.send_message(message.chat.id, 'Выберите период для экспорта:', reply_markup=markup)
        bot.register_next_step_handler(message, export_choice)

    else:
        bot.send_message(message.chat.id, 'Выберите одну из опций!')
        bot.register_next_step_handler(message, branches)

def export_choice(message):
    if message.text == 'Экспортировать за сегодня':
        export_to_txt(message, today1)

    elif message.text == 'Экспортировать за весь период':
        export_to_txt(message)

    else:
        bot.send_message(message.chat.id, 'Пожалуйста, выберите один из вариантов!')
        bot.register_next_step_handler(message, export_choice)

def export_to_txt(message, date_filter=None):
    conn = sqlite3.connect('my_database.db')
    cur = conn.cursor()

    if date_filter:
        cur.execute('SELECT * FROM data WHERE tg_id = ? AND visit_date = ?', (user_id, date_filter))
    else:
        cur.execute('SELECT * FROM data WHERE tg_id = ?', (user_id,))
    
    patients = cur.fetchall()
    conn.close()

    file_content = "Список пациентов:\n"
    for patient in patients:
        file_content += f'ID: {patient[0]} | ФИО: {patient[2]} {patient[3]} {patient[4]} | Дата рождения - {patient[5]} | Дата посещения - {patient[6]} | Контакт - {patient[7]}\n'

    file_name = f"patients_{today1}.txt" if date_filter else "patients_all_time.txt"
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(file_content)

    with open(file_name, 'rb') as f:
        bot.send_document(message.chat.id, f)

    bot.send_message(message.chat.id, f"Список пациентов экспортирован в файл: {file_name}")
    send_main_menu(message)

def get_lastname(message):
    global lastname
    if message.text == 'Главное меню':
        start(message)
    elif message.text.isalpha():
        lastname = message.text
        bot.send_message(message.chat.id, 'Введите имя:')
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(message.chat.id, 'Введите фамилию:')
        bot.register_next_step_handler(message, get_lastname)

def get_name(message):
    global name
    if message.text == 'Главное меню':
        start(message)
    elif message.text.isalpha():
        name = message.text
        bot.send_message(message.chat.id, 'Введите отчество:')
        bot.register_next_step_handler(message, get_surname)
    else:
        bot.send_message(message.chat.id, 'Введите имя:')
        bot.register_next_step_handler(message, get_name)

def get_surname(message):
    global surname
    if message.text == 'Главное меню':
        start(message)
    elif message.text.isalpha():
        surname = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Да'), types.KeyboardButton('Нет'))
        bot.send_message(
            message.chat.id,
            f'Фамилия - {lastname}, Имя - {name}, Отчество - {surname}. Всё верно?',
            reply_markup=markup
        )
        bot.register_next_step_handler(message, callback_one)
    else:
        bot.send_message(message.chat.id, 'Введите отчество:')
        bot.register_next_step_handler(message, get_surname)

def callback_one(message):
    if message.text == 'Нет':
        start(message)
    else:
        bot.send_message(message.chat.id, 'Введите дату рождения (ГГГГ.ММ.ДД):')
        bot.register_next_step_handler(message, get_birth_date)

def get_birth_date(message):
    global birth_date
    if message.text == 'Главное меню':
        start(message)
    if True:
        birth_date = message.text
        bot.send_message(message.chat.id, f'Дата рождения - {birth_date}. Всё верно?', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Да'), types.KeyboardButton('Нет')))
        bot.register_next_step_handler(message, confirm_birth_date)
    else:
        bot.send_message(message.chat.id, 'Введите дату рождения (ГГГГ.ММ.ДД):')
        bot.register_next_step_handler(message, get_birth_date)

def confirm_birth_date(message):
    if message.text == 'Нет':
        bot.send_message(message.chat.id, 'Введите дату рождения (ГГГГ.ММ.ДД):')
        bot.register_next_step_handler(message, get_birth_date)
    else:
        bot.send_message(message.chat.id, 'Введите контакт пациента (например, номер телефона):')
        bot.register_next_step_handler(message, get_contact)

def get_contact(message):
    global contact
    if message.text == 'Главное меню':
        start(message)
    contact = message.text
    bot.send_message(message.chat.id, f'Контакт пациента - {contact}. Всё верно?', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Да'), types.KeyboardButton('Нет')))
    bot.register_next_step_handler(message, confirm_contact)

def confirm_contact(message):
    if message.text == 'Нет':
        bot.send_message(message.chat.id, 'Введите контакт пациента (например, номер телефона):')
        bot.register_next_step_handler(message, get_contact)
    else:
        conn = sqlite3.connect('my_database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO data (tg_id, lastname, name, surname, birth_date, visit_date, contact) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, lastname, name, surname, birth_date, today1, contact))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, 'Пациент добавлен!')
        send_main_menu(message)

def delete_by_id(message):
    if message.text == 'Главное меню':
        start(message)
    elif message.text.isdigit():
        id_to_delete = int(message.text)
        conn = sqlite3.connect('my_database.db')
        cur = conn.cursor()
        cur.execute('DELETE FROM data WHERE id = ? AND tg_id = ?', (id_to_delete, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f'Пациент с ID {id_to_delete} удалён.')
        send_main_menu(message)
    else:
        bot.send_message(message.chat.id, 'Введите корректный числовой ID:')
        bot.register_next_step_handler(message, delete_by_id)

bot.polling(non_stop=True)
