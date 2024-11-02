import logging
from logging.handlers import RotatingFileHandler
import os
import requests
import sys
import time

from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import (VariableMissing, HomeworkKeyError, HomeworkApiError)
from handlers import telegram_handler


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
LOGS_PARAM = {
    'FILENAME': 'homework_bot.log',
    'MODE': 'a',
    'MAX_BYTES': 50000,
    'BACKUP_COUNT': 5,
    'FORMAT': '%(asctime)s - %(levelname)s: %(message)s',
}
logging.basicConfig(
    level=logging.DEBUG,
    format=LOGS_PARAM['FORMAT'],
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        RotatingFileHandler(
            filename=LOGS_PARAM['FILENAME'],
            mode=LOGS_PARAM['MODE'],
            maxBytes=LOGS_PARAM['MAX_BYTES'],
            backupCount=LOGS_PARAM['BACKUP_COUNT'],
        ),
    ],
)
homework_logger = logging.getLogger(__name__)
homework_logger.addHandler(telegram_handler)


def check_tokens():
    """Проверяет наличие необходимых переменных для работы бота."""
    for token in ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'):
        if not globals()[token]:
            msg = f'Проверьте доступность переменной {token}.'
            homework_logger.critical(msg)
            raise VariableMissing(msg)


def send_message(bot, message):
    """Отправляет сообщение message в чат телеграма."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message,)
    except Exception as error:
        homework_logger.error(f'Не удалось отправить сообщение - {error}')
    else:
        homework_logger.debug(
            f'Отправлено сообщение "{message}" в чат {TELEGRAM_CHAT_ID}'
        )


def get_api_answer(timestamp):
    """Возвращает ответ на запрос к api Яндекс в формате словаря Python."""
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
    except requests.exceptions.RequestException as error:
        homework_logger.error(f'Ошибка запроса к API – {error}.')
        return error
    else:
        if response.status_code == 400:
            msg = 'Неверное значение from_date'
            homework_logger.error(msg)
            raise HomeworkApiError(msg)
        if response.status_code == 401:
            msg = 'Неверное значение PRACTICUM_TOKEN'
            homework_logger.error(msg)
            raise HomeworkApiError(msg)
        if response.status_code != 200:
            homework_logger.error(
                f'Не получен ответ от API. Код ответа: {response.status_code}'
            )
            raise requests.exceptions.HTTPError
        return response.json()


def check_response(response):
    """Проверяет что в ответе данные соответствуют ожидаемым типам."""
    if type(response) is not dict:
        msg = f'Ответ от API не словарь. Тип ответа – {type(response)}'
        homework_logger.error(msg)
        raise TypeError(msg)
    if type(response.get('homeworks')) is not list:
        msg = (
            'Домашки передаются не списком, '
            f'а {type(response.get("homeworks"))}'
        )
        homework_logger.error(msg)
        raise TypeError(msg)


def parse_status(homework):
    """Извлекает данные из словаря и готовит сообщение для отправки в TG."""
    if 'homework_name' not in homework:
        msg = 'В ответе отсутствует имя домашки'
        homework_logger.error(msg)
        raise HomeworkKeyError(msg)
    elif homework.get('status') not in HOMEWORK_VERDICTS:
        msg = 'В ответе неожиданный статус домашки'
        homework_logger.error(msg)
        raise HomeworkKeyError(msg)
    else:
        homework_name = homework['homework_name']
        return str(
            f'Изменился статус проверки работы "{homework_name}". '
            f'{HOMEWORK_VERDICTS[homework["status"]]}'
        )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            api_response = get_api_answer(timestamp)
            check_response(api_response)
            try:
                homework = api_response['homeworks'][0]
                send_message(bot, parse_status(homework))
                timestamp = api_response['current_date']
            except IndexError:
                homework_logger.debug('Пока нет ответа от ревьювера')
        except Exception as error:
            homework_logger.error(error)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
