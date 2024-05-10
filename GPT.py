import requests
import logging  # модуль для сбора логов
from config import *
import json
import time
from datetime import datetime


def get_creds():
    try:
        # чтение iam_token
        with open(IAM_TOKEN_PATH, 'r') as f:
            file_data = json.load(f)
            expiration = datetime.strptime(file_data["expires_at"][:26], "%Y-%m-%dT%H:%M:%S.%f")
        # если срок годности истёк
        if expiration < datetime.now():
            logging.info("Срок годности iam_token истёк")
            # получаем новый iam_token
            create_new_token()
    except:
        # если что-то пошло не так - получаем новый iam_token
        create_new_token()

    # чтение iam_token
    with open(IAM_TOKEN_PATH, 'r') as f:
        file_data = json.load(f)
        iam_token = file_data["access_token"]

    # чтение folder_id
    with open(FOLDER_ID_PATH, 'r') as f:
        folder_id = f.read().strip()

    return iam_token, folder_id


IAMTOKEN, FOLDER_ID = get_creds()  # получаем iam_token и folder_id из файлов


def create_new_token():
    url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {
        "Metadata-Flavor": "Google"
    }
    try:
        response = requests.get(url=url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()  # вытаскиваем из ответа iam_token
            # добавляем время истечения iam_token к текущему времени
            token_data['expires_at'] = time.time() + token_data['expires_in']
            # записываем iam_token в файл
            with open(IAM_TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Получен новый iam_token")
        else:
            logging.error(f"Ошибка получения iam_token. Статус-код: {response.status_code}")
    except Exception as e:
        logging.error(f"Ошибка получения iam_token: {e}")

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.ERROR, format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="w")

# подсчитываем количество токенов в сообщениях


def count_gpt_tokens(messages):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"
    headers = {
        'Authorization': f'Bearer {IAMTOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "messages": messages
    }
    try:
        return len(requests.post(url=url, json=data, headers=headers).json()['tokens'])
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return 0

# запрос к GPT


def ask_gpt(messages):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {IAMTOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": MAX_GPT_TOKENS
        },
        "messages": SYSTEM_PROMPT + messages  # добавляем к системному сообщению предыдущие сообщения
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        # проверяем статус код
        if response.status_code != 200:
            return False, f"Ошибка GPT. Статус-код: {response.status_code}", None
        # если всё успешно - считаем количество токенов, потраченных на ответ, возвращаем статус, ответ, и количество токенов в ответе
        answer = response.json()['result']['alternatives'][0]['message']['text']
        tokens_in_answer = count_gpt_tokens([{'role': 'assistant', 'text': answer}])
        return True, answer, tokens_in_answer
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return False, "Ошибка при обращении к GPT",  None


def count_tokens(text):
    headers = {  # заголовок запроса, в котором передаем IAM-токен
        'Authorization': f'Bearer {IAMTOKEN}',  # token - наш IAM-токен
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",  # указываем folder_id
        "maxTokens": MAX_GPT_TOKENS,
        "text": text  # text - тот текст, в котором мы хотим посчитать токены
    }
    return len(
        requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenize",
            json=data,
            headers=headers
        ).json()['tokens']
    )  # здесь, после выполнения запроса, функция возвращает количество токенов в text
