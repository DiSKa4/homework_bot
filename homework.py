import os

import logging
import requests
import telegram
import time

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s - %(name)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)


class EmptyDictionary(Exception):
    """Пустой словарь."""

    pass


class StatusErrors(Exception):
    """Нет статуса."""

    pass


class AnswerNot200(Exception):
    """Ответ сервера не равен 200."""

    pass


class Emptyvalue(Exception):
    """Пустое значение."""

    pass


def send_message(bot, message):
    """Отправка сообщения."""

    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info(
        f'Сообщение в Telegram отправлено: {message}')


def get_api_answer(current_timestamp):
    """Получение данных ответа API."""

    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, params=params, headers=HEADERS)
    if response.status_code != 200:
        logger.error('ошибка ENDPOINT')
        raise AnswerNot200
    return(response.json())


def check_response(response):
    """Проверяем данные в response."""

    if response['homeworks'] is None:
        logger.error('Ошибка homeworks')
        raise EmptyDictionary
    if response['homeworks'] == []:
        return {}
    response['homeworks'][0].get('status')
    return response['homeworks']


def parse_status(homework):
    """Анализируем изменения статуса."""

    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status is None:
        logger.error('Ошибка status')
        StatusErrors(
            'Ошибка пустое значение status: ', homework_status)
    if homework_name is None:
        logger.error('Ошибка homeworks')
        Emptyvalue(
            'Ошибка пустое значение homework_name: ', homework_name)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем токены."""

    tokens_msg = (
        'Отсутствует обязательная переменная окружения:')
    token_response = True
    if PRACTICUM_TOKEN is None:
        token_response = False
        logger.critical(tokens_msg)
    if TELEGRAM_CHAT_ID is None:
        token_response = False
        logger.critical(tokens_msg)
    if TELEGRAM_TOKEN is None:
        token_response = False
        logger.critical(tokens_msg)
    return token_response


def main():
    """Основная логика работы бота."""

    if not check_tokens():
        return False
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = 'reviewing'
    errors = True
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework and status != homework['status']:
                message = parse_status(homework)
                send_message(bot, message)
                logger.info('Изменений нет')
                status = homework['status']
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if errors:
                errors = False
                send_message(bot, message)
                logger.critical(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
