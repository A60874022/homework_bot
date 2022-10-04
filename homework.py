import logging
import os
import time
from http import HTTPStatus
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from telegram import Bot
from errors import ExceptionDataType, ExceptionStatusCode
load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

RETRY_TIME: int = 600
FIRST_WORK: int = 0

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
    """Получение и преобразование в dist информации о текущих работах."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS, params=params)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise ExceptionStatusCode(f'Статус код'
                                      f'{homework_statuses.status_code}')
        else:
            logging.info('Запрос отправлен к основному API')
            return homework_statuses.json()
    except AssertionError('Ошибка при получении API'):
        logging.error('Ошибка при получении API')


def check_response(response: Dict[str, list]) -> list:
    """Возвращает список домашних работ."""
    if not isinstance(response, Dict):
        raise TypeError('response не словарь')
    if not response:
        raise ExceptionDataType('Словарь response пустой')
    if isinstance(response.get('homeworks'), list):
        return response.get('homeworks')
    else:
        raise TypeError('тип данных homeworks не список')


def parse_status(homework: Dict[Any, str]) -> str:
    """Возврашает статус работы, посланной на проверку."""
    if not isinstance(homework, Dict):
        raise TypeError('Структура данных homework не словарь')
    if not homework:
        raise ExceptionDataType('Словарь homework пустой')
    if homework.get('status') in HOMEWORK_STATUSES:
        name_work = homework.get('homework_name')
        verdict = HOMEWORK_STATUSES.get(homework.get('status'))
        logging.info(f'Изменился статус работы "{name_work}". {verdict}')
        return f'Изменился статус проверки работы "{name_work}". {verdict}'
    else:
        raise KeyError('Status не совпадает с HOMEWORK_STATUSES')


def check_tokens() -> bool:
    """Проверка наличия критических переменных."""
    data = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ENDPOINT]
    return all(data)


def main() -> None:
    """Основная логика работы программы."""
    old_messenge: str = ''
    old_logs = ''
    bot = Bot(token=TELEGRAM_TOKEN)
    if not check_tokens():
        logging.critical('Отсутстсвуют обязательные переменные')
        exit()
    while True:
        try:
            current_timestamp = int(time.time())
            api = get_api_answer(current_timestamp)
            logging.info(f'{api}, {int(time.time())}')
            list_of_works = check_response(api)
            if not list_of_works:
                logging.info('Статус работы не изменился')
            else:
                homework = list_of_works[FIRST_WORK]
                logging.info(f'{homework}, {int(time.time())}')
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
