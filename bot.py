
import json

import telebot

from info import survey


token = ""
bot = telebot.TeleBot(token)


def get_user_data(user_id: str) -> tuple:
    OPTIMIST = 0
    PESSIMIST = 0
    current_step = 0

    try:
        with open('data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}

    if user_data := data.get(user_id):
        OPTIMIST = user_data['OPTIMIST']
        PESSIMIST = user_data['PESSIMIST']
        current_step = user_data['step']

    return (OPTIMIST, PESSIMIST, current_step, data)


def save_user_data(point_optimist, point_pessimist, next_step, user_id):
    old_optimist, old_pessimist, _, data = get_user_data(user_id)

    user_data = {
        "OPTIMIST": point_optimist + old_optimist,
        "PESSIMIST": point_pessimist + old_pessimist,
        "step": next_step
    }
    data[user_id] = user_data

    with open('data.json', 'w') as file:
        json.dump(data, file)


def clear_user_data(user_id):
    try:
        with open('data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        return

    if data.get(user_id) is not None:
        del data[user_id]

    with open('data.json', 'w') as file:
        json.dump(data, file)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Начнем опрос")
    ask_question(message, survey[0])


def ask_question(message, question):
    bot.send_message(message.chat.id, question["question"])
    options = ""
    for num, answer in question["answers"].items():
        options += f"{num} - {answer[0]}\n"
    bot.send_message(message.chat.id, "Варианты ответов:\n" + options)

    bot.register_next_step_handler(message, process_answer, question)


def process_answer(message, question):
    answer = message.text.lower()
    points = question["answers"].get(answer)
    OPTIMIST = 0
    PESSIMIST = 0
    if points is not None:
        points = points[1]
        if points > 0:
            OPTIMIST += points
        else:
            PESSIMIST += abs(points)
    else:
        if message.text == '/start':
            bot.send_message(message.chat.id, "Продолжаем наш опрос...")
        else:
            bot.send_message(message.chat.id, "❌Неверный ответ, попробуйте её раз...")
        ask_question(message, survey[survey.index(question)])
        return

    next_question_index = survey.index(question) + 1
    save_user_data(OPTIMIST, PESSIMIST, next_question_index, str(message.from_user.id))

    if next_question_index < len(survey):
        ask_question(message, survey[next_question_index])
    else:
        show_results(message)


def show_results(message):
    result_message = "Результаты опроса:\n"
    OPTIMIST, PESSIMIST, _, _ = get_user_data(str(message.from_user.id))

    if PESSIMIST > OPTIMIST:
        result_message += "🙁 Вы пессимист. 🙁"
    else:
        result_message += "🙂 Вы оптимист! 🙂"

    bot.send_message(message.chat.id, result_message)
    bot.send_message(message.chat.id, "Чтобы пройти опрос повторно введите /start")
    clear_user_data(str(message.from_user.id))
    print(f'Пользователь {message.from_user.first_name} с ID: {message.from_user.id} - {result_message}')


@bot.message_handler(content_types=['text','photo', 'audio'])
def send_text(message):
    bot.send_message(message.chat.id, 'Неизвестная команда, чтобы пройти опрос введите /start')


bot.polling(non_stop=True, timeout=60)
