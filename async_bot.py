import asyncio
from http import HTTPStatus
import aiohttp  # type: ignore
import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from typing import Any
from lab4.constants import (
    OPENWEATHER_API_KEY,
    REQUEST_STRUCTURE,
    OPENWEATHER_URL,
    QUOTES_URL,
    FONTANKA_URL,
    HABR_URL
)

user_states: dict[int, str] = {}


async def send_message(
        session: aiohttp.ClientSession,
        chat_id: int,
        text: str
) -> bool:
    """

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        chat_id (int): id чата
        text (str): текст сообщения

    Returns:
        bool: успешно ли отправлено сообщение
    """
    url = REQUEST_STRUCTURE + 'sendMessage'

    params_json = {
        'chat_id': chat_id,
        'text': text
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = await session.post(url, json=params_json, headers=headers)
    if response.status >= HTTPStatus.BAD_REQUEST:
        return False

    return True


async def get_updates(
        session: aiohttp.ClientSession,
        offset: int | None = None,
        timeout: int | None = 30
) -> list[dict[str, Any]]:
    """Получает обновления в Telegram-боте

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        offset (int | None): id первого не обработанного обновления
        timeout (int | None): время ожидания ответа

    Returns:
        list[dict[str, Any]]: список обновлений
    """
    url = REQUEST_STRUCTURE + 'getUpdates'
    params = {
        'timeout': timeout
    }

    if offset:
        params['offset'] = offset

    response = await session.get(url, timeout=timeout, params=params)

    if response.status == HTTPStatus.OK:
        data = await response.json()
        if data.get('ok'):
            updates: list[dict[str, Any]] = data.get('result', [])
            return updates

    return []


def get_daily_quote() -> str | None:
    """Получает цитату дня с сайта

    Returns:
        str | None: цитата дня
    """
    response = requests.get(QUOTES_URL)

    if response.status_code == HTTPStatus.OK:
        soup = BeautifulSoup(response.text, 'html.parser')
        data = soup.find('div', class_='random__quote')
        if not data:
            return None

        quote_element = data.find('p')
        if not quote_element:
            return None

        quote = quote_element.text
        author_data = data.find('div', class_='field-item even')
        if not author_data:
            return None

        author_element = author_data.find('a')
        if not author_element:
            return None

        author = author_element.text
        formatted_quote = f'"{quote}" {author}'
        return formatted_quote

    return None


async def get_news_fontanka(session: aiohttp.ClientSession) -> str | None:
    """Получается последние новости с сайта ФОНТАНКА.ру

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов

    Returns:
        str: новости с сайта ФОНТАНКА.ру
    """
    response = await session.get(FONTANKA_URL)

    if response.status == HTTPStatus.OK:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.find('ol', class_='content_D5XNy fullHeight_D5XNy')
        if not data:
            return None

        news = data.find_all('div', class_='title_J499q')[:5]
        formatted_news = 'ФОНТАНКА.ру:\n\n'

        for new in news:
            new = new.text
            formatted_news += new + '\n\n'
        return formatted_news

    return None


async def get_news_habr(session: aiohttp.ClientSession) -> str | None:
    """Получается последние новости с сайта Habr

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов

    Returns:
        str: новости с сайта Habr
    """
    response = await session.get(HABR_URL)
    if response.status == HTTPStatus.OK:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')
        data = soup.find('div', class_='tm-articles-list')
        if not data:
            return None
        news = data.find_all('h2', class_='tm-title tm-title_h2')[:5]
        formatted_news = 'Habr:\n\n'
        for new in news:
            new_element = new.find('span')
            if not new_element:
                return None
            new = new_element.text
            formatted_news += new + '\n\n'
        formatted_news = formatted_news.strip()
        return formatted_news

    return None


async def get_weather(
        session: aiohttp.ClientSession,
        city: str
) -> str:
    """Получает текущую погоду для указанного города

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        city (str): название города

    Returns:
        str: Информация о погоде
    """
    params = {
        'q': city,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }

    response = await session.get(OPENWEATHER_URL, params=params)

    if response.status == HTTPStatus.OK:
        data = await response.json()
        message = ''
        country = data.get('sys').get('country')
        message += f'Погода - {city}, {country}:\n'
        description = data.get('weather')[0].get('description')
        message += f'Описание: {description}\n'
        main_weather = data.get('main')
        temp = main_weather.get('temp')
        message += f'Температура: {temp} градусов Цельсия\n'
        feels_like = main_weather.get('feels_like')
        message += f'Ощущается как: {feels_like} градусов Цельсия\n'
        pressure = main_weather.get('pressure')
        message += f'Давление: {pressure} гПа\n'
        humidity = main_weather.get('humidity')
        message += f'Влажность: {humidity}%\n'
        wind_speed = data.get('wind').get('speed')
        message += f'Ветер: {wind_speed} м/с'
    elif response.status == HTTPStatus.NOT_FOUND:
        message = 'Город не найден'
    else:
        message = 'Произошла неизвестная ошибка. Попробуйте позже.'

    return message


async def send_quotes(session: aiohttp.ClientSession, chat_id: int) -> None:
    """Отправляет цитату в Telegram-боте

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        chat_id (int): id чата
    """
    quote = await asyncio.to_thread(get_daily_quote)
    if quote:
        await send_message(session, chat_id, quote)


async def send_headlines(
        session: aiohttp.ClientSession,
        chat_id: int
) -> None:
    """Отправляет новости в Telegram-боте

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        chat_id (int): id чата
    """
    task_fontanka = get_news_fontanka(session)
    task_habr = get_news_habr(session)
    results = await asyncio.gather(task_fontanka, task_habr)
    all_news = ''

    for result in results:
        if result:
            all_news += result + '\n'
    all_news = all_news.strip()
    await send_message(session, chat_id, all_news)


async def ask_city(
        session: aiohttp.ClientSession,
        chat_id: int,
        user_id: int
) -> None:
    """Запрашивает у пользователя город для получения погоды

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        chat_id (int): id чата
        user_id (int): id пользователя
    """
    text: str = 'Пожалуйста, введите название города'
    await send_message(session, chat_id, text)
    user_states[user_id] = 'waiting_for_city'


async def send_weather(
        session: aiohttp.ClientSession,
        chat_id: int,
        user_id: int,
        city: str
) -> None:
    """Отправляет данные о погоде в Telegram-боте

    Args:
        session (aiohttp.ClientSession): сессия для отправки запросов
        chat_id (int): id чата
        user_id (int): id пользователя
        city (str): название города
    """
    weather_data = await get_weather(session, city)
    await send_message(session, chat_id, weather_data)

    del user_states[user_id]


async def main() -> None:
    """Основной цикл работы бота"""
    async with aiohttp.ClientSession() as session:
        offset: int | None = None
        while True:
            updates = await get_updates(session, offset=offset)
            if updates:
                for update in updates:
                    update_id = update['update_id']
                    message = update['message']
                    chat_id = message['chat']['id']
                    user_id = message['from']['id']
                    text: str = message['text']
                    if user_id in user_states:
                        if user_states[user_id] == 'waiting_for_city':
                            await send_weather(session, chat_id, user_id, text)
                    elif text == '/quote':
                        await send_quotes(session, chat_id)
                    elif text == '/headlines':
                        await send_headlines(session, chat_id)
                    elif text == '/weather':
                        await ask_city(session, chat_id, user_id)
                    else:
                        await send_message(session, chat_id, text)
                    offset = update_id + 1

asyncio.run(main())
