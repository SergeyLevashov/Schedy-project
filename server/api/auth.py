from urllib.parse import parse_qsl
import hmac, hashlib, json
from typing import TypedDict, Any

from fastapi import Request, HTTPException, status, Depends
from pydantic import BaseModel
from config_reader import config   # BOT_TOKEN берём оттуда


class TelegramUser(BaseModel):
    id: int
    is_bot: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


class WebAppInitData(BaseModel):
    query_id: str
    user: TelegramUser
    auth_date: int
    hash: str


def _check_signature(token: str, init_data: str) -> WebAppInitData:
    """
    Проверка подписи initData по официальной инструкции Telegram:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", "")
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(
        key=bytes("WebAppData", "utf-8"),
        msg=bytes(token, "utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        key=secret_key,
        msg=bytes(data_check_string, "utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("bad signature")

    # Pydantic валидирует и превращает строковые значения в числа/объекты
    return WebAppInitData(**parsed, hash=received_hash)


async def auth(request: Request) -> WebAppInitData:
    """
    FastAPI-dependency, которая:
    1. Берёт заголовок X-Tg-Init-Data
    2. Проверяет подпись
    3. Возвращает разобранный объект WebAppInitData
    """
    init_data = request.headers.get("X-Tg-Init-Data")
    if not init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized"},
        )
    try:
        return _check_signature(config.BOT_TOKEN, init_data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Bad signature"},
        )