import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, UpdateType # UpdateType ni qo'shdik

from config import BOT_TOKEN
from database import init_db
from handlers import register_all_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    await init_db()
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    register_all_handlers(dp)
    
    logger.info("🤖 Bot ishga tushdi...")
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # allowed_updates qo'shildi - bu Business xatoligini yo'qotadi
    await dp.start_polling(
        bot, 
        allowed_updates=[
            UpdateType.MESSAGE, 
            UpdateType.CALLBACK_QUERY, 
            UpdateType.CHAT_MEMBER, 
            UpdateType.MY_CHAT_MEMBER
        ]
    )

if __name__ == "__main__":
    asyncio.run(main())
