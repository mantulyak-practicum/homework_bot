import logging
import os
import requests

from dotenv import load_dotenv


load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


class TelegramLogHandler(logging.Handler):
    """Класс для отправки логов в Телеграмм."""

    def __init__(self, bot_token, chat_id):
        """Инициализация класса телеграмм-обработчика."""
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.last_message = None

    def emit(self, record):
        """."""
        try:
            log_entry = record.msg
            if log_entry != self.last_message:
                requests.post(
                    self.api_url, data={
                        'chat_id': self.chat_id, 'text': self.format(record)
                    }
                )
                self.last_message = log_entry
        except Exception as e:
            print(f"Ошибка отправки лога в телеграмм: {e}")


telegram_handler = TelegramLogHandler(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
telegram_handler.setLevel(logging.ERROR)
telegram_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
)
