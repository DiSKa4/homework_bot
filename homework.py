import logging
import os
import time
from http import HTTPStatus

import json
import requests
import telegram
from dotenv import load_dotenv

import exceptions

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


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(
            f'Сообщение в Telegram отправлено: {message}')
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение {error}', exc_info=True)
        raise exceptions.SendMessage(error)


def get_api_answer(current_timestamp):
    """Получение данных ответа API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, params=params, headers=HEADERS)
    except requests.exceptions.RequestException as error:
        logger.error('Ошибка URL')
        raise requests.exceptions.RequestException(error)
    if response.status_code != HTTPStatus.OK:
        logger.error('ошибка ENDPOINT')
        raise exceptions.AnswerNot200
    try:
        return(response.json())
    except json.decoder.JSONDecodeError:
        print("не JSON")


def check_response(response):
    """Проверяем данные в response."""
    try:
        homework = response['homeworks']
    except KeyError as error:
        logger.error(f'Нет ключа {error}')
        raise KeyError('Ключ отсутсвует')
    if not homework:
        error_msg = ('В списке нет домашки')
        logger.error(error_msg)
        raise exceptions.ApiResponse(error_msg)
    if len(homework) == 0:
        error_msg = ('Пусто,ничего не отправлено')
        logger.error(error_msg)
        raise exceptions.ApiResponse(error_msg)
    if not isinstance(homework, list):
        error_message = ('Домашка выводятся не списком')
        logger.error(error_message)
        raise exceptions.ApiResponse(error_message)
    return homework


def parse_status(homework):
    """Анализируем изменения статуса."""
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        logger.error('Ошибка homeworks')
        raise KeyError(f'В словаре нет ключа homework_name {error}')
    try:
        homework_status = homework['status']
    except KeyError as error:
        logger.error('Ошибка status')
        raise KeyError(f'В словаре нет ключа status{error}')
    verdict = HOMEWORK_STATUSES[homework_status]
    if verdict is None:
        logger.error('Отсутсвует статус проверки')
        raise exceptions.StatusMissing
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
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                homework = homework[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logger.info('Изменений нет')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
