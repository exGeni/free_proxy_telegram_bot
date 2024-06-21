import asyncio
import logging
from telebot.async_telebot import AsyncTeleBot
from config import TOKEN
from handlers import register_handlers
from import_proxies import periodic_update
from db_utils import (
    init_db,
    create_users_table
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    """Main function to initialize the bot and start polling."""
    await init_db()
    await create_users_table()

    bot = AsyncTeleBot(TOKEN)
    register_handlers(bot)

    asyncio.create_task(periodic_update())
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    asyncio.run(main())