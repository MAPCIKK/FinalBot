import sqlite3
import logging  # модуль для сбора логов
# подтягиваем константы из config-файла
from config import LOGS, DB_FILE

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.info,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")
path_to_db = DB_FILE  # файл базы данных

# создаём базу данных и таблицу messages


def create_database():
    try:
        # подключаемся к базе данных
        with sqlite3.connect(path_to_db) as conn:
            cursor = conn.cursor()
            # создаём таблицу messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                message TEXT,
                role TEXT,
                total_gpt_tokens INTEGER,
                tts_symbols INTEGER,
                stt_blocks INTEGER)
            ''')
            logging.info("DATABASE: База данных создана")  # делаем запись в логах
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return None

# добавляем новое сообщение в таблицу messages


def add_message(user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks):
    try:
        # подключаемся к базе данных
        with sqlite3.connect(path_to_db) as conn:
            cursor = conn.cursor()
            # записываем в таблицу новое сообщение
            cursor.execute('''
                    INSERT INTO messages (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                           (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks)
                           )
            conn.commit()  # сохраняем изменения
            logging.info(f"DATABASE: INSERT INTO messages "
                         f"VALUES ({user_id}, {message}, {role}, {total_gpt_tokens}, {tts_symbols}, {stt_blocks})")
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return None

# считаем количество уникальных пользователей помимо самого пользователя


def count_users(user_id):
    try:
        # подключаемся к базе данных
        with sqlite3.connect(path_to_db) as conn:
            cursor = conn.cursor()
            # получаем количество уникальных пользователей помимо самого пользователя
            cursor.execute('''SELECT COUNT(DISTINCT user_id) FROM messages WHERE user_id <> ?''', (user_id,))
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return None


def count_all_symbol(user_id, db_name="messages.db"):
    try:
        # Подключаемся к базе
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Считаем, сколько символов использовал пользователь
            cursor.execute('''SELECT SUM(tts_symbols) FROM messages WHERE user_id=?''', (user_id,))
            data = cursor.fetchone()
            # Проверяем data на наличие хоть какого-то полученного результата запроса
            # И на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # Если результат есть и data[0] == какому-то числу, то
                return data[0]  # возвращаем это число - сумму всех потраченных символов
            else:
                # Результата нет, так как у нас ещё нет записей о потраченных символах
                return 0  # возвращаем 0
    except Exception as e:
        print(f"Error: {e}")


def count_all_blocks(user_id, db_name="messages.db"):
    # Подключаемся к базе
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        # Считаем, сколько аудиоблоков использовал пользователь
        cursor.execute('''SELECT SUM(stt_blocks) FROM messages WHERE user_id=?''', (user_id,))
        data = cursor.fetchone()
        print()
        # Проверяем data на наличие хоть какого-то полученного результата запроса
        # И на то, что в результате запроса мы получили какое-то число в data[0]
        if data and data[0]:
            # Если результат есть и data[0] == какому-то числу, то
            return data[0]  # возвращаем это число - сумму всех потраченных аудиоблоков
        else:
            # Результата нет, так как у нас ещё нет записей о потраченных аудиоблоках
            return 0  # возвращаем 0
