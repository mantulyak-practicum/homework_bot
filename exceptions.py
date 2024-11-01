class VariableMissing(Exception):
    """Вызывается при отсутствии необходимой переменной."""

    pass


class HomeworkKeyMissing(Exception):
    """Вызывается при отсутствии ожидаемых ключей в ответе API."""

    pass
