# /utils/telegram_auth.py

import hashlib
import hmac
import json
from typing import Optional
from urllib.parse import parse_qsl, unquote

from fastapi import Header, HTTPException

from config_reader import config
from db.models.user import User


def is_valid_init_data(init_data: str) -> Optional[dict]:
    """Проверяет подлинность данных, полученных от Telegram Web App."""
    try:
        parsed_data = dict(parse_qsl(init_data))
    except ValueError:
        return None

    if "hash" not in parsed_data:
        return None

    init_data_hash = parsed_data.pop("hash")
    
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    
    secret_key = hmac.new("WebAppData".encode(), config.BOT_TOKEN.get_secret_value().encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash == init_data_hash:
        user_data = json.loads(unquote(parsed_data.get("user", "{}")))
        return user_data
    
    return None

async def get_user_from_init_data(x_tg_init_data: str = Header(...)) -> User:
    """
    Зависимость FastAPI для аутентификации пользователя и получения его из БД.
    Используется в эндпоинтах, требующих авторизации через Telegram WebApp.
    """
    user_data = is_valid_init_data(x_tg_init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or missing Telegram InitData")
        
    user, created = await User.get_or_create(
        telegram_id=user_data["id"],
        defaults={
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "username": user_data.get("username"),
        }
    )
    return user