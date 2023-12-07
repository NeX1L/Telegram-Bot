import telebot
import sqlite3
import time
import threading
from telebot import types
from datetime import datetime
from dateutil import parser

bot = telebot.TeleBot('6636340841:AAGT6Hz_zaM3YbZQOby2iZ3oQGJvKJ_sH7c')
note_name = None
note_text = None
user_id = None

def send_commands_keyboard(bot, chat_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('/add'), types.KeyboardButton('/delete'), types.KeyboardButton('/edit'))
    keyboard.add(types.KeyboardButton('/notes'), types.KeyboardButton('/rule'), types.KeyboardButton('/help'))

    bot.send_message(chat_id, "Выберите команду:", reply_markup=keyboard)

def check_notes_and_notify():
    while True:
        time.sleep(1)

        current_time = datetime.now()
        conn = sqlite3.connect('notes.sql')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE time <= ?", (current_time,))
        notes = cursor.fetchall()

        for note in notes:
            user_id, notes_name, notes_text, _ = note
            bot.send_message(user_id, f"Напоминание: {notes_name}\n{notes_text}")

            cursor.execute("DELETE FROM notes WHERE user_id = ? AND notes_name = ?", (user_id, notes_name))
            conn.commit()

        cursor.close()
        conn.close()

timer_thread = threading.Thread(target=check_notes_and_notify)
timer_thread.start()

@bot.message_handler(commands = ['start'])
def main(message):
    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS notes (user_id INTEGER, notes_name TEXT PRIMARY KEY, notes_text TEXT, time DATETIME)')
    conn.commit()
    cursor.close()
    conn.close()

    if message.from_user.first_name == None:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.last_name}. Этот бот предназнаен для ваших заметок и напоминая их вам.')
        bot.send_message(message.chat.id, 'Чтобы работать с ботом, воспользуйтесь командой /help')
    elif message.from_user.last_name == None:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}. Этот бот предназнаен для ваших заметок и напоминая их вам.')
        bot.send_message(message.chat.id, 'Чтобы работать с ботом, воспользуйтесь командой /help')
    else:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}. Этот бот предназнаен для ваших заметок и напоминая их вам.')
        bot.send_message(message.chat.id, 'Чтобы работать с ботом, воспользуйтесь командой /help')
    send_commands_keyboard(bot, message.chat.id)


@bot.message_handler(commands = ['help'])
def mai(message):
    bot.send_message(message.chat.id, 'Команды:\n/add - добавить заметку\n/delete - удалить заметку \n/edit - редактировать текст заметки\n/notes - просмотреть свою заметку\n/rule - главное правило бота')
    send_commands_keyboard(bot, message.chat.id)


@bot.message_handler(commands=['add'])
def add(message):
    bot.send_message(message.chat.id, 'Введите имя вашей заметки')
    bot.register_next_step_handler(message, noteName)
def noteName(message):
    global note_name
    global user_id
    note_name = message.text
    user_id = message.from_user.id
    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE user_id = ? AND notes_name = ?", (user_id, note_name))
    existing_note = cursor.fetchone()
    cursor.close()
    conn.close()
    if existing_note:
        bot.send_message(message.chat.id, "Заметка с таким именем уже существует. Введите уникальное имя заметки.")
        add(message)
    else:
        try:
            if ' ' in note_name:
                raise ValueError('Имя вашей заметки должно быть без пробела!')
            bot.send_message(message.chat.id, 'Имя заметки готово')
            bot.send_message(message.chat.id, 'Введите текст вашей заметки')
            bot.register_next_step_handler(message, noteText)
        except Exception as e:
            bot.send_message(message.chat.id, f'Ошибка: {str(e)} Пожалуйста, попробуйте еще раз')
            add(message)
def noteText(message):
    global note_text
    note_text = ' '.join(message.text.strip().split())
    bot.send_message(message.chat.id, 'Заметка готова')
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%d.%m.%Y %H:%M")
    bot.send_message(message.chat.id, f'Введите дату и время напоминания для вашей заметки\nВот пример текущей даты {formatted_datetime}')
    bot.register_next_step_handler(message, date)
def date(message):
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%d.%m.%Y %H:%M")
    try:
        user_datetime = parser.parse(message.text, dayfirst=True, yearfirst=False)
        if user_datetime <= current_datetime:
            raise OverflowError
        conn = sqlite3.connect('notes.sql')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes(user_id, notes_name, notes_text, time) VALUES (?, ?, ?, ?)", (user_id, note_name, note_text, user_datetime))
        conn.commit()
        cursor.close()
        conn.close()
        bot.send_message(message.chat.id, "Ваша заметка была сохранена 👌")
        send_commands_keyboard(bot, message.chat.id)

    except ValueError:
        bot.send_message(message.chat.id, "Ошибка при разборе даты и времени 🧐")
        bot.send_message(message.chat.id,f'Введите дату и время напоминания для вашей заметки\nВот пример текущей даты {formatted_datetime}')
        bot.register_next_step_handler(message, date)
    except OverflowError:
        bot.send_message(message.chat.id, 'Дата и время напоминания должны быть не раньше текущей даты и времени')
        bot.send_message(message.chat.id, f'Введите дату и время напоминания для вашей заметки\nВот пример текущей даты {formatted_datetime}')
        bot.register_next_step_handler(message, date)


@bot.message_handler(commands=['reply'])
def reply(message):
    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute('select * from notes')
    users = cursor.fetchall()
    info = ''

    for el in users:
        if len(el) >= 4:  # Проверяем, что у кортежа есть как минимум 4 элемента
            info += f'if: {el[0]}, имя заметки: {el[1]}, текст заметки: {el[2]}, дата: {el[3]}\n'
        else:
            info += 'Ошибка: некорректные данные в базе\n'

    cursor.close()
    conn.close()

    if info:
        bot.send_message(message.chat.id, info)
    else:
        bot.send_message(message.chat.id, "Нет заметок для отображения.")


@bot.message_handler(commands=['delete'])
def delete(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    if count == 0:
        bot.send_message(message.chat.id, "У вас нет заметок для удаления 🧐")
        send_commands_keyboard(bot, message.chat.id)
        return
    bot.send_message(message.chat.id, "Введите название заметки, которую вы хотите удалить")
    bot.register_next_step_handler(message, delete_note)
def delete_note(message):
    try:
        user_id = message.from_user.id
        note_name = message.text

        conn = sqlite3.connect('notes.sql')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE user_id = ? AND notes_name = ?", (user_id, note_name))
        existing_note = cursor.fetchone()

        if existing_note:
            # Заметка существует, удаляем ее из базы данных
            cursor.execute("DELETE FROM notes WHERE user_id = ? AND notes_name = ?", (user_id, note_name))
            conn.commit()
            bot.send_message(message.chat.id, "Заметка успешно удалена 👌")
            send_commands_keyboard(bot, message.chat.id)
        else:
           raise Exception
    except Exception:
        bot.send_message(message.chat.id,"Заметка не найдена. Пожалуйста, убедитесь, что вы ввели правильное название заметки.\nИмя заметки должно быть без пробела!")
        delete(message)
    finally:
        cursor.close()
        conn.close()
@bot.message_handler(commands=['edit'])
def startEdit(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    if count == 0:
        bot.send_message(message.chat.id, "У вас нет заметок для изменения 🧐")
        send_commands_keyboard(bot, message.chat.id)
        return
    bot.send_message(message.chat.id, "Введите название вашей заметки, которую вы хотите изменить")
    bot.register_next_step_handler(message, edit)
def edit(message):
    try:
        note_name = message.text
        user_id = message.from_user.id
        conn = sqlite3.connect('notes.sql')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE user_id = ? AND notes_name = ?", (user_id, note_name))
        existing_note = cursor.fetchone()
        cursor.close()
        conn.close()

        if existing_note:
            bot.send_message(message.chat.id, "Введите новый текст для заметки:")
            bot.register_next_step_handler(message, update_note, user_id, note_name)
        else:
            raise Exception
    except Exception:
        bot.send_message(message.chat.id,"Заметка не найдена. Пожалуйста, убедитесь, что вы ввели правильное название заметки.\nИмя заметки должно быть без пробела!")
        startEdit(message)
def update_note(message, user_id, note_name):
    new_text = ' '.join(message.text.strip().split())

    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET notes_text = ? WHERE user_id = ? AND notes_name = ?",(new_text, user_id, note_name))
    conn.commit()
    cursor.close()
    conn.close()

    bot.send_message(message.chat.id, "Заметка успешно обновлена 👌")
    send_commands_keyboard(bot, message.chat.id)

@bot.message_handler(commands=['notes'])
def notes(message):
    user_id = message.from_user.id

    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT notes_name FROM notes WHERE user_id = ?", (user_id,))
    user_notes = cursor.fetchall()
    cursor.close()
    conn.close()

    if not user_notes:
        bot.send_message(message.chat.id, "У вас пока нет заметок. Создайте сначала какие-то заметки! 🧐")
        send_commands_keyboard(bot, message.chat.id)
        return

    notes_list = "\n".join(f"{index + 1} - {note[0]}" for index, note in enumerate(user_notes))
    bot.send_message(message.chat.id, f"Ваши заметки:\n{notes_list}")
    keyboard = types.InlineKeyboardMarkup(row_width=1)


    for index, note in enumerate(user_notes):
        button_text = str(index + 1)
        callback_data = f"show_note_{index + 1}"
        keyboard.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))

    bot.send_message(message.chat.id, "Выберите заметку, чтобы посмотреть ее текст:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_note_'))
def process_note_selection(call):
    user_id = call.from_user.id
    selected_index = int(call.data.split('_')[2]) - 1

    conn = sqlite3.connect('notes.sql')
    cursor = conn.cursor()
    cursor.execute("SELECT notes_name, notes_text FROM notes WHERE user_id = ?", (user_id,))
    user_notes = cursor.fetchall()
    cursor.close()
    conn.close()

    if 0 <= selected_index < len(user_notes):
        selected_note_name, selected_note_text = user_notes[selected_index]
        bot.send_message(call.message.chat.id, f"Текст заметки {selected_note_name}:\n{selected_note_text}")
    send_commands_keyboard(bot, call.message.chat.id)


@bot.message_handler(commands=['rule'])
def rule(message):
    bot.send_message(message.chat.id, 'Самое важное правило, когда выскочило напоминание вашей заметки, она автоматически ботом удаляется!\nЖелаю приятно пользоваться этим ботом 😉')
    send_commands_keyboard(bot, message.chat.id)
@bot.message_handler()
def info(message):
    bot.send_message(message.chat.id, 'Что-то пошло не так, воспользуйтесь /help')
    send_commands_keyboard(bot, message.chat.id)


bot.polling(none_stop=True)