from GPT import *
import telebot
from validators import *
from speechkit import *
from DB import *
from telebot.types import *
import math


def get_bot_token():
    with open(BOT_TOKEN_PATH, 'r') as f:
        return f.read().strip()


bot = telebot.TeleBot(get_bot_token())
create_database()


def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


def is_stt_block_limit(user_id, duration):

    # Переводим секунды в аудио блоки
    audio_blocks = math.ceil(duration / 15)  # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудио блоков
    all_blocks = count_all_blocks(user_id) + audio_blocks

    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем all_blocks с количеством доступных пользователю аудио блоков
    if all_blocks >= MAX_USER_STT_BLOCKS:
        msg = (f"Превышен общий лимит SpeechKit STT {MAX_USER_STT_BLOCKS}. Использовано {all_blocks} блоков. "
               f"Доступно: {MAX_USER_STT_BLOCKS - all_blocks}")
        bot.send_message(user_id, msg)
        return None

    return audio_blocks


def is_tts_symbol_limit(message, text):
    user_id = message.from_user.id
    text_symbols = len(text)

# Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_symbol(user_id) + text_symbols

# Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= MAX_USER_TTS_SYMBOLS:
        msg = (f"Превышен общий лимит SpeechKit TTS {MAX_USER_TTS_SYMBOLS}. Использовано: {all_symbols} символов. "
               f"Доступно: {MAX_USER_TTS_SYMBOLS - all_symbols}")
        bot.send_message(user_id, msg)
        return None

# Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит SpeechKit TTS на запрос {MAX_TTS_SYMBOLS}, в сообщении {text_symbols} символов"
        bot.send_message(user_id, msg)
        return None
    return len(text)


def select_n_last_messages(user_id, n_last_messages=4):
    messages = []  # список с сообщениями
    total_spent_tokens = 0  # количество потраченных токенов за всё время общения
    try:
        # подключаемся к базе данных
        print("Получилось")
        with sqlite3.connect('messages.db') as conn:
            cursor = conn.cursor()
            # получаем последние <n_last_messages> сообщения для пользователя
            cursor.execute('''
            SELECT message, role, total_gpt_tokens FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?''',
                           (user_id, n_last_messages))
            data = cursor.fetchall()
            # проверяем data на наличие хоть какого-то полученного результата запроса
            # и на то, что в результате запроса есть хотя бы одно сообщение - data[0]
            if data and data[0]:
                # формируем список сообщений
                for message in reversed(data):
                    messages.append({'text': message[0], 'role': message[1]})
                    total_spent_tokens = max(total_spent_tokens, message[2])  # находим максимальное количество потраченных токенов
            # если результата нет, так как у нас ещё нет сообщений - возвращаем значения по умолчанию
            return messages, total_spent_tokens
    except Exception as e:
        print('Ошибка')
        logging.error(e)  # если ошибка - записываем её в логи
        return messages, total_spent_tokens


# подсчитываем количество потраченных пользователем ресурсов (<limit_type> - символы или аудио блоки)
def count_all_limits(user_id, limit_type):
    try:
        # подключаемся к базе данных
        with sqlite3.connect('messages.db') as conn:
            cursor = conn.cursor()
            # считаем лимиты по <limit_type>, которые использовал пользователь
            cursor.execute(f'''SELECT SUM({limit_type}) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            # проверяем data на наличие хоть какого-то полученного результата запроса
            # и на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # если результат есть и data[0] == какому-то числу, то:
                logging.info(f"DATABASE: У user_id={user_id} использовано {data[0]} {limit_type}")
                return data[0]  # возвращаем это число - сумму всех потраченных <limit_type>
            else:
                # результата нет, так как у нас ещё нет записей о потраченных <limit_type>
                return 0  # возвращаем 0
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return 0


@bot.message_handler(commands=['debug'])
def debug(message):
    with open('logs.txt', 'rb') as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(commands=['start'])
def start(message):
    logging.info('Использована команда /start')
    bot.send_message(message.from_user.id, f'Привет, {message.from_user.first_name}😍! Очень рад видеть тебя. '
                                           f'Меня зовут Шурик и я буду твоим помощником🫡.'
                                           f'\n \nМогу переписываться с тобой или общаться ...голосовыми!😮'
                                           f'\n \nЗнаю почти обо всем на свете, не стесняйся меня спрашивать о чем хочешь!👌'
                                           f'\n \nВсегда помогу и поддержу, не оставлю в беде!😉'
                                           f'\n \nЧтобы поговорить со мной, напиши любое текстовое сообщение, или запиши голосовое!'
                                           f'\n \nЕсли хочешь узнать обо мне подробнее или прочесть подробную инструкцию, '
                                           f'\nнажми /help', reply_markup=create_keyboard(["/help", '/start']))


@bot.message_handler(commands=['help'])
def help_the_user(message):
    bot.send_message(message.from_user.id, f'Приветствую Вас, мой пользователь {message.from_user.first_name}.'
                                           f'\n \nЭто @MAPPPC, автор и разработчик данного бота.'
                                           f'\n \nБот работает с использованием YandexGPT2 и Yandex Speechkit'
                                           f'\n \nБот очень прост в использовании - чтобы поговорить с GPT, нужно написать любое текстовое сообщение, или записать голосовое.'
                                           f'\n \nСписок доступных команд находится во вкладке "меню" в левом нижнем углу Вашего устройства.'
                                           f'\n \nЕсли у Вас есть претензии или пожелания - пишите мне, я буду рад помощи в разработке и поддержке этого бота'
                                           f'\n \n*Удачи в использовании!*😉', reply_markup=create_keyboard(["/help", '/start']))


@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:

        # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(message.from_user.id)
        if not status_check_users:
            bot.send_message(message.from_user.id, error_message)  # мест нет =(
            return

        # БД: добавляем сообщение пользователя и его роль в базу данных
        add_message(user_id=message.from_user.id, message=message.text, role='user',
                    total_gpt_tokens=count_tokens(message.text), tts_symbols='0', stt_blocks='0')

        # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
        # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = select_n_last_messages(message.from_user.id, COUNT_LAST_MSG)
        print(last_messages)
        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(message.from_user.id, error_message)
            return

        # GPT: отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        # GPT: обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(message.from_user.id, answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer

        # БД: добавляем ответ GPT и потраченные токены в базу данных
        add_message(user_id=message.from_user.id, message=answer_gpt, role='assistant',
                    total_gpt_tokens=(count_tokens(answer_gpt) + count_tokens(message.text)), tts_symbols='0', stt_blocks='0')

        bot.send_message(message.from_user.id, answer_gpt, reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    user_id = message.from_user.id
    stt_blocks = is_stt_block_limit(message.from_user.id, message.voice.duration)
    if not stt_blocks:
        return

    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение

    # Получаем статус и содержимое ответа от SpeechKit
    status, text = speech_to_text(file)  # преобразовываем голосовое сообщение в текст

    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        add_message(user_id=message.from_user.id, message=text, role='user',
                    total_gpt_tokens=int(count_tokens(text)), tts_symbols='0',
                    stt_blocks=stt_blocks)
        print(select_n_last_messages(message.from_user.id)[0])
        success, answer, tokens = ask_gpt(select_n_last_messages(message.from_user.id)[0])
        if success:
            text_symbol = is_tts_symbol_limit(message, text)
            if text_symbol is None:
                return

            # Записываем сообщение и кол-во символов в БД

            # Получаем статус и содержимое ответа от SpeechKit
            status, content = text_to_speech(answer)

            # Если статус True - отправляем голосовое сообщение, иначе - сообщение об ошибке
            if status:
                add_message(user_id=message.from_user.id, message=answer, role='assistant',
                            total_gpt_tokens=(int(count_tokens(text)) + int(count_tokens(answer))),
                            tts_symbols=text_symbol, stt_blocks='0')
                bot.send_voice(user_id, content)
            else:
                bot.send_message(user_id, content)
        else:
            bot.send_message(user_id, 'Какая-то ошибка при обращении к GPT. Она появляется рандомно, '
                                      'попробуй задать другой вопрос или этот же самый, и скорее всего, все заработает.')
    else:
        bot.send_message(user_id, text)


# обрабатываем все остальные типы сообщений
@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.from_user.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")
bot.polling()
