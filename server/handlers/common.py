import asyncio
import logging
import sys
from os import getenv
from aiogram import Bot, Dispatcher, html
from aiogram import Router, F
from aiogram.types import Message, WebAppInfo, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config_reader import config

from keyboards import main_markup
from db import User

router = Router(name="common")



@router.pre_checkout_query()
async def precheck(event: PreCheckoutQuery) -> None:
    await event.answer(True)

@router.message(Command('start'))
async def start(message: Message) -> None:
    """Handle the /start command and create new users."""
    user = await User.filter(id=message.from_user.id).exists()
    if not user:
        await User.create(
            id=message.from_user.id,
            name=message.from_user.first_name
        )

    await message.answer("Привет! Я твой AI-ассистент по расписанию. Нажми кнопку ниже, чтобы открыть приложение.", reply_markup=main_markup)
