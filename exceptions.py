class StatusErrors(Exception):
    """Нет статуса."""

    pass


class AnswerNot200(Exception):
    """Ответ сервера не равен 200."""

    pass


class Emptyvalue(Exception):
    """Пустое значение."""

    pass


class SendMessage(Exception):
    """Отправка сообщений"""

    pass


class ApiResponse(Exception):
    """Проверка API"""

    pass


class ResponseTypeException(Exception):
    """Ошибка типа ответа"""

    pass
