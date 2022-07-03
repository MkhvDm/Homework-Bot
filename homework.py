import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
# from jsonschema import validate  # alternative check json
from telegram import Bot, TelegramError

from exceptions import (ApiResponseNotCorrect, PracticumApiErr,
                        TelegramSendErr, UndefinedHWStatus)

load_dotenv()

# # Prepare your logger...
FORMATTER = logging.Formatter("%(asctime)s - [%(levelname)s] %(message)s")
bot_logger = logging.getLogger(__name__)
bot_logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(FORMATTER)
bot_logger.addHandler(stream_handler)
bot_logger.debug('Logger enabled...')

# Get tokens from .env
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # me

RETRY_TIME = 600
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

ERRORS = {
    # errors and flag 'need send notification about error in TG'
    'ENDPOINT_ERR': False,
    'RESPONSE_NOT_DICT': False,
    'RESPONSE_DONT_CONTAINS_ALL_KEYS': False,
    'HOMEWORKS_NOT_LIST': False,
    'CURRENT_DATE_NOT_INT': False,
    'UNEXPECT_HOMEWORK_STATUS': False,
}


def send_message(bot, message) -> None:
    """Отправка сообщения в чат Telegram."""
    try:
        bot_logger.debug(f'Send message: {message}')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
    except TelegramError as err:
        raise TelegramSendErr(
            (f'{type(err).__name__}: {err}. '
             f'Не удалось отправить сообщение в Telegram-чат!')
        )


def get_api_answer(current_timestamp) -> dict:
    """
    Запрос данных об изменениях статуса домашней работы.
    Возращает словарь с ключами 'current_date' и 'homeworks'.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}  # 0
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        err_message = (f'Нет ответа от сервиса Практикум.Домашка. '
                       f'Ошибка {response.status_code}!')
        raise PracticumApiErr(err_message, 'ENDPOINT_ERR')
    bot_logger.info('GET data from Practicum API done!')
    bot_logger.debug(f'RESPONSE_status: {response}')
    bot_logger.debug(f'RESPONSE JSON: {response.json()}')
    ERRORS['ENDPOINT_ERR'] = False
    return response.json()


def check_response(response) -> list:
    """
    Проверка ответа API на корректность.
    Возвращает список домашних работ.
    """
    bot_logger.debug('Start check_response...')
    if not isinstance(response, (dict, list)):
        raise ApiResponseNotCorrect(
            'По API Практикум.Домашка ожидаем словарь!',
            'RESPONSE_NOT_DICT'
        )
    if isinstance(response, list):
        response = response[0]
    if 'current_date' not in response or 'homeworks' not in response:
        raise ApiResponseNotCorrect(
            'В API-ответе ожидаем ключи "current_date" и "homeworks"!',
            'RESPONSE_DONT_CONTAINS_ALL_KEYS'
        )

    if not isinstance(response.get('homeworks'), list):
        raise ApiResponseNotCorrect(
            'В API-ответе по ключу "homeworks" ожидаем список!',
            'HOMEWORKS_NOT_LIST'
        )
    if not isinstance(response.get('current_date'), int):
        raise ApiResponseNotCorrect(
            'В API-ответе по ключу "current_date" ожидаем целое число!',
            'CURRENT_DATE_NOT_INT'
        )
    # reset errors flag for enable new error notification:
    for key in ('RESPONSE_NOT_DICT',
                'RESPONSE_DONT_CONTAINS_ALL_KEYS',
                'HOMEWORKS_NOT_LIST',
                'CURRENT_DATE_NOT_INT'):
        ERRORS[key] = False

    # альтернативный вариант validate() (jsonschema lib):
    # можно проверить всю структуру ответа в соответстии с шаблоном,
    # недостаток - сложно вывести сообщение, где конкретно проблема в ответе.
    # validate(instance=response, schema=API_RESP_STRUCT)

    homeworks = response.get('homeworks')
    if not homeworks:
        bot_logger.debug('Нет обновлений.')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлечение из объекта домашней работы информации о статусе."""
    bot_logger.debug('Start parse_status...')
    bot_logger.debug(homework)
    homework_name = homework['homework_name']
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES.keys():
        raise UndefinedHWStatus(
            f'Незадокументированный статус домашней работы: {homework_status}',
            'UNEXPECT_HOMEWORK_STATUS'
        )
    verdict = HOMEWORK_STATUSES.get(homework_status)
    ERRORS['UNEXPECT_HOMEWORK_STATUS'] = False
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка всех требуемых токенов."""
    return PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID


def errors_sender(bot, err_msg, err_key):
    """
    Функция отправки сообщения в Telegram об ошибке уровня ERROR.
    Будет отправлено только одно сообщение, до момента исправления.
    """
    if not ERRORS[err_key]:
        send_message(bot, err_msg)
        ERRORS[err_key] = True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot_logger.info('Tokens found!')
    else:
        bot_logger.critical(
            '[!] Tokens not found! Please add your tokens in .env file!'
        )
        exit()

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    bot_logger.info(f'Start time: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
            current_timestamp = response.get('current_date')

        except PracticumApiErr as err:
            err_name, (err_msg, err_key) = type(err).__name__, err.args
            bot_logger.error(f'{err_name}: {err_msg}')
            errors_sender(bot, f'{err_name}: {err_msg}', err_key)

        except TelegramSendErr as err:
            bot_logger.error(err)  # opt.: exc_info=True

        except ApiResponseNotCorrect as err:
            err_name, (err_msg, err_key) = type(err).__name__, err.args
            bot_logger.error(f'{err_name}: {err_msg}')
            errors_sender(bot, f'{err_name}: {err_msg}', err_key)

        except UndefinedHWStatus as err:
            err_name, (err_msg, err_key) = type(err).__name__, err.args
            bot_logger.error(f'{err_name}: {err_msg}')
            errors_sender(bot, f'{err_name}: {err_msg}', err_key)

        except Exception as err:
            bot_logger.error(f'Сбой в работе программы: {err}', exc_info=True)

        finally:
            time.sleep(60)


if __name__ == '__main__':
    main()
