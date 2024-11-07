import logging
from logging.handlers import RotatingFileHandler
import os
import requests
from requests.exceptions import RequestException
import sys
import time

from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiException

from exceptions import (
    VariableMissing,
    HomeworkKeyError,
    HomeworkApiError,
    SendMessageError,
    HomeworkResponseError
)
# Импорт telegram_handler использовался при добавлении хендлера к логгеру.
# Логика про то, что не доложно отсылаться два сообщения была тоже
# реализована в хендлере, так что ТЗ все же было выполнено)
# В этой версии убрал его, сделал отправку в ТГ с помощью send_message()


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


def check_tokens():
    """Проверяет наличие необходимых переменных для работы бота."""
    missing_tokens = [
        token for token in (
            'PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID'
        ) if not globals()[token]
    ]
    if missing_tokens:
        return (
            f'Проверьте доступность переменных: {", ".join(missing_tokens)}.'
        )
    else:
        return False


def send_message(bot, message):
    """Отправляет сообщение message в чат телеграма."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message,)
    except (ApiException, RequestException) as error:
        raise SendMessageError(f'Не удалось отправить сообщение - {error}')
    else:
        logging.debug(
            f'Отправлено сообщение "{message}" в чат {TELEGRAM_CHAT_ID}'
        )


def get_api_answer(timestamp):
    """Возвращает ответ на запрос к api Яндекс в формате словаря Python."""
    try:
        request_kwargs = {
            'url': ENDPOINT,
            'headers': HEADERS,
            'params': {'from_date': timestamp},
        }
        response = requests.get(**request_kwargs)
    except RequestException as error:
        raise HomeworkApiError(
            f'Ошибка запроса к API – {error}. '
            f'Параметры запроса: {request_kwargs}'
        ) from error
    else:
        if response.status_code == 400:
            raise HomeworkApiError(
                f'Неверное значение from_date. {request_kwargs}'
            )
        if response.status_code == 401:
            raise HomeworkApiError(
                f'Неверное значение PRACTICUM_TOKEN. {request_kwargs}'
            )
        if response.status_code != 200:
            raise HomeworkApiError(
                f'Статус ответа API не 200. Код ответа: {response.status_code}'
                f'Параметры запроса: {request_kwargs}'
            )
        return response.json()


def check_response(response):
    """Проверяет что в ответе данные соответствуют ожидаемым типам."""
    if not isinstance(response, dict):
        raise TypeError(
            f'Ответ от API не словарь. Тип ответа – {type(response)}'
        )
    if response.get('homeworks') is None:
        raise HomeworkResponseError(
            'В ответе нет ключа "homeworks".'
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Домашки передаются не списком, '
            f'а {type(response["homeworks"])}'
        )


def parse_status(homework):
    """Извлекает данные из словаря и готовит сообщение для отправки в TG."""
    if 'homework_name' not in homework:
        raise HomeworkKeyError('В ответе отсутствует имя домашки')
    if 'status' not in homework:
        raise HomeworkKeyError('В ответе отсутствует статус домашки')
    if homework.get('status') not in HOMEWORK_VERDICTS:
        raise HomeworkKeyError(
            f'В ответе неожиданный статус домашки: {homework.get("status")}'
        )
    return str(
        f'Изменился статус проверки работы "{homework["homework_name"]}". '
        f'{HOMEWORK_VERDICTS[homework["status"]]}'
    )


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logging.critical(check_tokens())
        sys.exit(check_tokens())
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 86400
    status_message = ''
    while True:
        try:
            api_response = get_api_answer(timestamp)
            check_response(api_response)
            homeworks = api_response['homeworks']
            if len(homeworks):
                new_message = parse_status(homeworks[0])
                if new_message != status_message:
                    send_message(bot, new_message)
                    status_message = new_message
            else:
                logging.debug('В ответе нет данных о домашке')
            timestamp = api_response.get('current_date', timestamp)
        except Exception as error:
            logging.error(
                f'{type(error).__name__} — {error}'
            )
            try:
                if globals().get('error_message') != error:
                    error_message = error
                    send_message(bot, error_message)
            except SendMessageError as error:
                logging.error(f'{error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOGS_PARAM['FORMAT'],
        encoding='utf-8',
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
    main()
