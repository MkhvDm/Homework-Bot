import os
import sys
import time
import requests
from pprint import pprint

import logging

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


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    pass


def get_api_answer(current_timestamp):
    """XXX."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    bot_logger.info('GET data from Practicum API done!')

    response_dict = response.json()
    pprint(response_dict)
    # check_response()
    return response_dict


def check_response(response):
    """
    Проверка ответа API на корректность. Возвращает список домашних работ.
    """
    if not isinstance(response, dict):
        print('raise ApiResponseNotCorrect')
        return []
    if 'current_date' and 'homeworks' not in response.keys():
        print('raise ApiResponseNotCorrect')
        return []



def parse_status(homework):
    homework_name = ...
    homework_status = ...
    #
    verdict = ...
    #
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Check all required tokens."""
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def main():
    """Основная логика работы бота."""

    if check_tokens():
        bot_logger.info('Tokens found!')
    else:
        bot_logger.critical('[!] Tokens not found! Please add your tokens in .env file!')

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 2629743
    bot_logger.info(f'Current time: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)

            #

            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            # ...
            time.sleep(RETRY_TIME)
        else:
            pass
            # ...


if __name__ == '__main__':
    main()
