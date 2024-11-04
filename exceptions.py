class VariableMissing(Exception):
    """Вызывается при отсутствии необходимой переменной."""


class HomeworkKeyError(Exception):
    """Вызывается при отсутствии ожидаемых ключей в ответе API."""


class HomeworkApiError(Exception):
    """Вызывается при ошибках при запросе к API."""
