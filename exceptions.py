class VariableMissing(Exception):
    """Вызывается при отсутствии необходимой переменной."""

    pass


class HomeworkKeyError(Exception):
    """Вызывается при отсутствии ожидаемых ключей в ответе API."""

    pass


class HomeworkApiError(Exception):
    """Вызывается при ошибках при запросе к API."""

    pass
