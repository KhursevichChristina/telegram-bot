from dotenv import load_dotenv  # type: ignore
import os

"""Модуль констант для Telegram-бота"""

load_dotenv()

TOKEN = os.getenv('TOKEN')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
REQUEST_STRUCTURE = f'https://api.telegram.org/bot{TOKEN}/'
OPENWEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
QUOTES_URL = 'https://citaty.info/'
FONTANKA_URL = 'https://www.fontanka.ru/'
HABR_URL = 'https://habr.com/ru/news/'
