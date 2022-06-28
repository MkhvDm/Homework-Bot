import os
import sys
import time
import requests
from pprint import pprint

import logging
from logging import StreamHandler

from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler

from dotenv import load_dotenv

load_dotenv()

# LOGGING
FORMATTER = logging.Formatter(
    '%(asctime)s - [%(levelname)s] %(name)s - %(message)s'
)
# LOG_FILE = "bot_log.log"


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # bot
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # me

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
payload = {'from_date': 0}  #???


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_console_handler())
    logger.propagate = False  # todo GOOGLE???
    return logger


def send_message(bot, message):
    pass


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    pass


def check_response(response):
    pass


def parse_status(homework):
    homework_name = ...
    homework_status = ...
    #
    verdict = ...
    #
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    pass


def main():
    """Основная логика работы бота."""

    bot_logger = get_logger(__name__)

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.info(f'Current time: {current_timestamp}')

    # ...

    while True:
        try:
            response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
            pprint(response.text)
            pprint(response.json())
            # ...

            current_timestamp = int(time.time())  # ???
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
