HOME_DIR = '/home/student/Final'  # путь к папке с проектом
LOGS = f'{HOME_DIR}/errors.txt'  # файл для логов
DB_FILE = f'{HOME_DIR}/messages.db'  # файл для базы данных
IAM_TOKEN_PATH = f'{HOME_DIR}/creds/iam_token.txt'  # файл для хранения iam_token
FOLDER_ID_PATH = f'{HOME_DIR}/creds/folder_id.txt'  # файл для хранения folder_id
BOT_TOKEN_PATH = f'{HOME_DIR}/creds/bot_token.txt'  # файл для хранения bot_token
MAX_USERS = 3  # максимальное кол-во пользователей
MAX_GPT_TOKENS = 120  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 4  # кол-во последних сообщений из диалога
MAX_TTS_SYMBOLS = 200
# лимиты для пользователя
MAX_USER_STT_BLOCKS = 10  # 10 аудиоблоков
MAX_USER_TTS_SYMBOLS = 5000  # 5 000 символов
MAX_USER_GPT_TOKENS = 2000  # 2 000 токенов
SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты - добрый и общительный чат-бот по имени Шурик.'
                                            'Не пиши ответ больше, чем на 170 символов'}]  # список с системным промтом
