import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import UpdateType, ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import register_all_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    # 1. Bazani ishga tushirish
    await init_db()
    
    # 2. Bot obyektini yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # 3. Dispatcher va Storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # 4. Handlerlarni ro'yxatdan o'tkazish
    register_all_handlers(dp)
    
    logger.info("🤖 Bot ishga tushdi...")
    
    # 5. Eskilarini tozalab, yangi pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    
    await dp.start_polling(bot, allowed_updates=[
        UpdateType.MESSAGE, 
        UpdateType.CALLBACK_QUERY, 
        UpdateType.CHAT_MEMBER, 
        UpdateType.MY_CHAT_MEMBER
    ])

if __name__ == "__main__":
    asyncio.run(main())
