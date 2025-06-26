from pathlib import Path

from os.path import join, dirname
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from aiogram import Bot, Dispatcher
from fastapi import FastAPI
from tortoise import Tortoise

ROOT_DIR: Path = Path(__file__).resolve().parent.parent


class Config(BaseSettings):
    BOT_TOKEN: SecretStr
    DB_URL: SecretStr
    OPENAI_API_KEY: SecretStr
    GOOGLE_CLIENT_ID: SecretStr
    GOOGLE_CLIENT_SECRET: SecretStr
    GOOGLE_REDIRECT_URI: str = "https://rnafg-5-35-36-54.a.free.pinggy.link/api/google/oauth2callback"
    
    WEBAPP_URL: str = "https://a7cd-5-35-36-54.ngrok-free.app"
    WEBHOOK_URL: str = "https://rnafg-5-35-36-54.a.free.pinggy.link"
    
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080
    
    model_config = SettingsConfigDict(
        env_file="D:/Schedy-project/server/.env",
        env_file_encoding="utf-8"
    )

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await bot.set_webhook(
        url=f"{config.WEBHOOK_URL}/webhook",
        drop_pending_updates=True,
        allowed_updates=dp.resolve_used_update_types()
    )
    
    await Tortoise.init(TORTOISE_ORM)
    yield
    await Tortoise.close_connections()
    await bot.session.close()

config = Config()

bot = Bot(config.BOT_TOKEN.get_secret_value())
dp = Dispatcher()
app = FastAPI(lifespan=lifespan)

app.router.lifespan_context = lifespan

TORTOISE_ORM = {
    "connections": {"default": config.DB_URL.get_secret_value() },
    "apps": {
        "models": {
            "models": ["db.models.user", "db.models.google_token", "aerich.models"],
            "default_connection": "default",
        }
    },
}
