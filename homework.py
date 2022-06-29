import os
import sys
import time
import requests
from pprint import pprint

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import logging
import exceptions

from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler

from dotenv import load_dotenv

load_dotenv()

# LOGGING
FORMATTER = logging.Formatter(
    "%(asctime)s - [%(levelname)s] %(name)s - %(message)s"
)
# Prepare your logger...
bot_logger = logging.getLogger(__name__)
bot_logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(FORMATTER)
bot_logger.addHandler(stream_handler)
bot_logger.debug('Logger enabled...')

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # bot
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # me

RETRY_TIME = 30
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

API_RESP_STRUCT = {
    "description": "Practicum.Domashka API response",
    "type": "object",
    "properties": {
        "current_date": {
            "description": "UNIX time",
            "type": "integer",
            "minimum": 0},
        "homeworks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date_updated": {"type": "string"},
                    "homework_name": {"type": "string"},
                    "id": {"type": "integer"},
                    "lesson_name": {"type": "string"},
                    "reviewer_comment": {"type": "string"},
                    "status": {"type": "string"},
                }
            },
        },
    },
    "required": ["current_date", "homeworks"]
}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    # TODO >>> STOP HERE <<<


def get_api_answer(current_timestamp) -> dict:
    """
    Запрос данных об изменениях статуса домашней работы с определённого
    момента времени. Возращает словарь с ключами 'current_date' и 'homeworks'.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}  # 0
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    bot_logger.info('GET data from Practicum API done!')
    pprint(response.json())
    return response.json()


def check_response(response) -> list:
    """
    Проверка ответа API на корректность. Возвращает список домашних работ.
    """
    if not isinstance(response, (dict, list)):
        raise exceptions.ApiResponseNotCorrect(
            'По Практикум.Домашка API ожидаем словарь или список!'
        )
        return []
    if 'current_date' and 'homeworks' not in response.keys():
        raise exceptions.ApiResponseNotCorrect(
            'В API-ответе ожидаем ключи "current_date" и "homeworks"!'
        )
        return []
    if not isinstance(response.get('homeworks'), list):
        raise exceptions.ApiResponseNotCorrect(
            'В API-ответе по ключу "homeworks" ожидаем список!!'
        )
    # альтернативный вариант (jsonschema lib):
    # можно проверить всю структуру ответа в соответстии с шаблоном,
    # недостаток - сложно вывести сообщение, где конкретно проблема в ответе.
    validate(instance=response, schema=API_RESP_STRUCT)
    return response.get('homeworks', [])


def parse_status(homework: dict):
    """Извлечение из объекта домашней работы информации о статусе."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка всех требуемых токенов."""
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def main():
    """Основная логика работы бота."""

    if check_tokens():
        bot_logger.info('Tokens found!')
    else:
        bot_logger.critical('[!] Tokens not found! Please add your tokens in .env file!')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1655587998  # int(time.time()) - 2629743
    bot_logger.info(f'Current time: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                print(message)
                # send_message()

            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except exceptions.ApiResponseNotCorrect as err:
            message = 'Невалидный формат API-ответа.'
            print(message)
        except ValidationError as err:
            message = 'Невалидный формат API-ответа.'
            print(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print()
            # ...
            time.sleep(RETRY_TIME)
        else:
            pass
            # ...


if __name__ == '__main__':
    main()
