import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from http import HTTPStatus
from typing import Any
from lab4.constants import (
    REQUEST_STRUCTURE,
    QUOTES_URL,
)


def send_message(chat_id: int, text: str) -> bool:
    """Отправка сообщения Telegram-ботом

    Args:
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

    response = requests.post(url, json=params_json, headers=headers)
    if response.status_code >= HTTPStatus.BAD_REQUEST:
        return False

    return True


def get_updates(
        offset: int | None = None,
        timeout: int | None = 30
) -> list[dict[str, Any]]:
    """Получает обновления в Telegram-боте

    Args:
        offset (int | None): id первого не обработанного обновления
        timeout (int | None): время ожидания ответа
    Returns:
        list[dict[str, Any]] | None: список обновлений
    """
    url = REQUEST_STRUCTURE + 'getUpdates'
    params = {
        'timeout': timeout
    }
    if offset:
        params['offset'] = offset

    response = requests.get(url, timeout=timeout, params=params)

    if response.status_code == HTTPStatus.OK:
        data: dict[str, Any] = response.json()
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
        quote_data = data.find('p')
        author_data = data.find('div', class_='field-item even')
        if (not quote_data) or (not author_data):
            return None
        quote = quote_data.text
        author = author_data.find('a')
        if not author:
            return None
        author_name = author.text
        formatted_quote = f'"{quote}" {author_name}'
        return formatted_quote
    return None


def echo_bot() -> None:
    """Основной цикл работы эхо-бота"""
    offset: int | None = None

    while True:
        updates = get_updates(offset=offset)
        if updates:
            for update in updates:
                update_id: int = update['update_id']
                if 'message' in update:
                    message = update['message']
                    chat_id: int = message['chat']['id']
                    if 'text' in message:
                        text: str | None = message['text']
                        if text:
                            if text.strip() == '/quote':
                                quote: str | None = get_daily_quote()
                                if quote:
                                    send_message(chat_id, quote)
                            else:
                                send_message(chat_id, text)
                offset = update_id + 1


echo_bot()
