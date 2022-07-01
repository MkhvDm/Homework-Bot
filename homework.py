import os
import sys
import time
import requests
from pprint import pprint
from http import HTTPStatus

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import logging
import exceptions

from telegram import ReplyKeyboardMarkup, Bot
from telegram.ext import Updater, CommandHandler

from dotenv import load_dotenv

load_dotenv()

# Prepare your logger...
FORMATTER = logging.Formatter("%(asctime)s - [%(levelname)s] %(message)s")
bot_logger = logging.getLogger(__name__)
bot_logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(FORMATTER)
bot_logger.addHandler(stream_handler)
bot_logger.debug('Logger enabled...')

# Get tokens from .env
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')      # bot
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

LOG_ERRORS_STATE = {
    'TOKENS_ERR': None,
    # 'TELEGRAM_ERR': None,
    'ENDPOINT_ERR': False,
    'ENDPOINT_API_ERR': None,
    'INCORRECT_API_RESPONSE_ERR': None,
    'UNEXPECT_STATUS': None,
}


def send_message(bot, message) -> None:
    """Отправка сообщения в чат Telegram."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,  #'adb',
            text=message
        )
    except Exception as err:
        msg = f'{type(err).__name__}: {err}'
        bot_logger.error(msg, exc_info=True)
        raise exceptions.TelegramSendErr(
            'Ошибка отправки сообщения в чат!'
        )
        # send_message(bot, msg)
        # if telegram_available:
        #     bot.send_message(
        #         chat_id=TELEGRAM_CHAT_ID,
        #         text=msg
        #     )


def get_api_answer(current_timestamp) -> dict:
    """
    Запрос данных об изменениях статуса домашней работы с определённого
    момента времени. Возращает словарь с ключами 'current_date' и 'homeworks'.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}  # 0
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        err_message = (f'Нет ответа от сервиса Практикум.Домашка! '
                       f'Ошибка {response.status_code}')
        bot_logger.error(err_message)
        raise exceptions.PracticumApiErr(err_message)
    bot_logger.info('GET data from Practicum API done!')
    bot_logger.debug(response.json())
    LOG_ERRORS_STATE['ENDPOINT_ERR'] = False
    # print('[getapiresp]:', LOG_ERRORS_STATE['ENDPOINT_ERR'])
    return response.json()


def check_response(response) -> list:
    """
    Проверка ответа API на корректность. Возвращает список домашних работ.
    """
    if not isinstance(response, (dict, list)):
        raise exceptions.ApiResponseNotCorrect(
            'По Практикум.Домашка API ожидаем словарь или список!'
        )
        # return []
    if 'current_date' and 'homeworks' not in response.keys():
        raise exceptions.ApiResponseNotCorrect(
            'В API-ответе ожидаем ключи "current_date" и "homeworks"!'
        )
        # return []
    if not isinstance(response.get('homeworks'), list):
        raise exceptions.ApiResponseNotCorrect(
            'В API-ответе по ключу "homeworks" ожидаем список!!'
        )
    # альтернативный вариант validate() (jsonschema lib):
    # можно проверить всю структуру ответа в соответстии с шаблоном,
    # недостаток - сложно вывести сообщение, где конкретно проблема в ответе.
    validate(instance=response, schema=API_RESP_STRUCT)
    homeworks = response.get('homeworks', [])
    if not homeworks:
        bot_logger.debug('Нет обновлений.')
    return homeworks


def parse_status(homework: dict):
    """Извлечение из объекта домашней работы информации о статусе."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        err_message = (
            f'Незадокументированный статус домашней работы: {homework_status}'
        )
        bot_logger.error(err_message)
        raise exceptions.UndefinedHWStatus(err_message)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка всех требуемых токенов."""
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def main():
    """Основная логика работы бота."""

    if check_tokens():
        bot_logger.info('Tokens found!')
    else:
        bot_logger.critical(
            '[!] Tokens not found! Please add your tokens in .env file!'
        )
        # try to send in TG

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 0  # 1655587998  # int(time.time()) - 2629743
    bot_logger.info(f'Start time: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                print('homework message:', message)
                send_message(bot, message)
            current_timestamp = response.get('current_date')
        except exceptions.PracticumApiErr as err:
            print('\t', LOG_ERRORS_STATE.get('ENDPOINT_ERR'))
            if not LOG_ERRORS_STATE.get('ENDPOINT_ERR'):
                message = f'{type(err).__name__}: {err}'
                send_message(bot, message)
                LOG_ERRORS_STATE['ENDPOINT_ERR'] = True
        except exceptions.ApiResponseNotCorrect as err:
            print('EXCEPT:')
            print(err)
            message = 'Невалидный формат API-ответа.'
            # send_message(bot, message)
        except ValidationError as err:
            message = 'Невалидный формат API-ответа.'
            print(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print()
            # ...
        else:
            pass
        finally:
            time.sleep(1)


if __name__ == '__main__':
    main()
