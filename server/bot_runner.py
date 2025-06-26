import asyncio
import logging

from handlers import setup_routers as setup_bot_routers
from config_reader import bot, dp, TORTOISE_ORM
from tortoise import Tortoise

async def main() -> None:
    dp.include_router(setup_bot_routers())

    await Tortoise.init(TORTOISE_ORM)
    await Tortoise.generate_schemas()

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot started polling")
    try:
        await dp.start_polling(bot)
    finally:
        await Tortoise.close_connections()
        await bot.session.close()
        logging.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())