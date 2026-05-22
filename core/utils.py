import os
import random
import requests


def generate_tracking_number() -> str:
    """Génère un numéro de suivi aléatoire unique (6 chiffres)."""
    from core.models import Order
    while True:
        n = str(random.randint(100000, 999999))
        if not Order.objects.filter(tracking_number=n).exists():
            return n


def send_telegram(message: str) -> None:
    """Envoie une notification Telegram à Hicham. Silencieux en cas d'erreur."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML',
            },
            timeout=5,
        )
    except Exception:
        pass
