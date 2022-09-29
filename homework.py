import time
import requests
#load_dotenv()
from pprint import pprint
from telegram import Bot
from time import sleep
import telegram
from http import HTTPStatus
import logging, sys


logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s, %(lineno)d'
)


PRACTICUM_TOKEN = 'y0_AgAAAAAPwqe-AAYckQAAAADPv9tT-fSiNdLfTqOot84NycAt9p5tu_Q'
TELEGRAM_TOKEN = '5725028117:AAEmV6mZrBP1YAM8-IhQSKSNc3E5YgSechI'
TELEGRAM_CHAT_ID = '1725468162'

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

def send_message(bot, message):
        chat_id = TELEGRAM_CHAT_ID
        bot.send_message(chat_id, message)


def get_api_answer(current_timestamp):
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
    except:
            logging.error('Запрос не отправлен к основному API')
            raise AssertionError
    
def check_response(response):
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



def parse_status(homework):
    if 'status' not in homework:
        logging.error('Отсутствует ключ status')
        raise KeyError('Отсутствует ключ status')
    if  len(homework) == 0:
        logging.error('Отсутствуют данные в homework')
        raise KeyError(('Отсутствуют данные в homework'))
    try:
        name = homework['status']
        name_work = homework.get('homework_name')
        verdict = HOMEWORK_STATUSES[name]
        logging.info(f'Изменился статус проверки работы {name_work}. {HOMEWORK_STATUSES.get(name)}')
        return f'Изменился статус проверки работы "{name_work }". {verdict}'
    except:
        logging.error('Значение ключа status не совпадает с HOMEWORK_STATUSES')
        raise KeyError('Значение ключа status не совпадает с HOMEWORK_STATUSES')
        
    

def check_tokens():
    """Проверка наличия токенов."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN:
        if TELEGRAM_CHAT_ID and ENDPOINT:
            return True
    return False

def main():
    """Основная логика работы бота."""
    old_messenge = ''
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() == False:
        logging.CRITICAL('Отсутстсвуют обязательные переменные')
        exit()
    while (True):
        try:
            current_timestamp = int(time.time())
            api = get_api_answer(current_timestamp)
            list_of_works = check_response(api)
            if len(list_of_works) == 0:  
                logging.info('Работа еще не отправлена')
            else:
                homework = list_of_works[0]
                message = parse_status(homework)
                if  old_messenge !=  message:
                    send_message(bot, message)
                    logging.info('Сообщение отправлено в телеграмм')
                    old_messenge = message
                else:
                    logging.info('Статус работы не изменился')
        except Exception as error:
            LOG = f'Сбой в работе программы: {error}'
            send_message(bot, LOG)
        time.sleep(10)

if __name__ == '__main__':
    main()