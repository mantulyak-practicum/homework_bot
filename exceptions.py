class VariableMissing(Exception):
    """Вызывается при отсутствии необходимой переменной."""


class HomeworkKeyError(Exception):
    """Вызывается при отсутствии ожидаемых ключей в ответе API."""


class HomeworkApiError(Exception):
    """Вызывается при ошибках при запросе к API."""


class SendMessageError(Exception):
    """Вызывается при ошибках отправки сообщения в ТГ."""


class HomeworkResponseError(Exception):
    """Вызывается при получении неожиданных данных в ответе."""
