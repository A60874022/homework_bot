import logging
import os
import time
from http import HTTPStatus
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_TIME: int = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
FIRST_WORK: int = 0
MESSAGE_LENGTH = 0
logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)d'
)

HOMEWORK_STATUSES: Dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def send_message(bot, message: str) -> None:
    """Отправка сообщения в Телеграмм."""
    chat_id = TELEGRAM_CHAT_ID
    bot.send_message(chat_id, message)


def get_api_answer(current_timestamp: int) -> Dict[str, list]:
    """Получение и преобразование в dist информации о текущих работах"""
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    try:
        if homework_statuses.status_code == HTTPStatus.OK:
            logging.info('Запрос отправлен к основному API')
            return homework_statuses.json()
        else:
            logging.error(
                f' Код ответа API: {homework_statuses.status_code}')
            raise OSError(f'Код ответа API: {homework_statuses.status_code}')
    except AssertionError:
        logging.error('Запрос не отправлен к основному API')
        raise AssertionError


def check_response(response: Dict[str, list]) -> list:
    """Возвращает список домашних работ."""
    if 'homeworks' not in response:
        logging.error('Отсутствует ключ homeworks')
        raise TypeError('Отсутствует ключ homeworks')
    if len(response) == 0:
        logging.error('Отсутствуют данные в pesponse')
        raise TypeError('Отсутствуют данные в pesponse')
    if type(response.get('homeworks')) != list:
        logging.error('тип данных homeworks не список')
        raise TypeError('тип данных homeworks не список')
    return response.get('homeworks')


def parse_status(homework: Dict[Any, str]) -> str:
    """Возврашает статус работы, посланной на проверку."""
    if 'status' not in homework:
        logging.error('Отсутствует ключ status')
        raise KeyError('Отсутствует ключ status')
    if len(homework) == MESSAGE_LENGTH:
        logging.error('Отсутствуют данные в homework')
        raise KeyError(('Отсутствуют данные в homework'))
    try:
        name = homework['status']
        name_work = homework.get('homework_name')
        verdict = HOMEWORK_STATUSES[name]
        logging.info(f'Изменился статус работы "{name_work}". {verdict}')
        return f'Изменился статус проверки работы "{name_work}". {verdict}'
    except KeyError:
        logging.error('Status не совпадает с HOMEWORK_STATUSES')
        raise KeyError('Status не совпадает с HOMEWORK_STATUSES')


def check_tokens() -> bool:
    """Проверка наличия критических переменных."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN:
        if TELEGRAM_CHAT_ID and ENDPOINT:
            return True
    return False


def main() -> None:
    """Основная логика работы бота."""
    old_messenge: str = ''
    old_logs = ''
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is False:
        logging.CRITICAL('Отсутстсвуют обязательные переменные')
        exit()
    while (True):
        try:
            current_timestamp = int(time.time())
            api = get_api_answer(current_timestamp)
            list_of_works = check_response(api)
            if len(list_of_works) == MESSAGE_LENGTH:
                logging.info('Работа еще не отправлена')
            else:
                homework = list_of_works[FIRST_WORK]
                message = parse_status(homework)
                if old_messenge != message:
                    send_message(bot, message)
                    logging.info('Сообщение отправлено в телеграмм')
                    old_messenge = message
                else:
                    logging.info('Статус работы не изменился')
        except Exception as error:
            logs = f'Сбой в работе программы: {error}'
            if old_logs != logs:
                logs = f'Сбой в работе программы: {error}'
                send_message(bot, logs)
                old_logs = logs
            logging.info(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
