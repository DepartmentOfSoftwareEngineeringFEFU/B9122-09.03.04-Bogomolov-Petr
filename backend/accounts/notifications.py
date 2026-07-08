"""Отправка push-уведомлений пользователям в Telegram (TG_04, FR_T5, FR_S3).

Работает синхронно поверх Telegram Bot API. При отсутствии токена или сбое
сети уведомление тихо не отправляется и не прерывает вызывающий код —
push-канал является дополнительным, а не обязательным для работы системы.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = 'https://api.telegram.org/bot{token}/sendMessage'


def send_telegram_message(telegram_id, text):
    if not telegram_id:
        return False
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token or token == 'your_bot_token_here':
        logger.debug('TELEGRAM_BOT_TOKEN не задан — уведомление не отправлено')
        return False
    try:
        resp = requests.post(
            TELEGRAM_API_URL.format(token=token),
            json={'chat_id': telegram_id, 'text': text, 'parse_mode': 'HTML'},
            timeout=5,
        )
        return resp.status_code == 200
    except requests.RequestException:
        logger.warning('Не удалось отправить Telegram-уведомление пользователю %s', telegram_id)
        return False


def notify_users(users, text):
    """Уведомляет всех пользователей из списка/queryset, у кого привязан telegram_id."""
    sent = 0
    for user in users:
        if getattr(user, 'telegram_id', None) and send_telegram_message(user.telegram_id, text):
            sent += 1
    return sent
