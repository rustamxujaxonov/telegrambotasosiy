import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from config import CHANNEL_ID
from database import get_user
from keyboards import subscribe_keyboard, main_menu_keyboard
from utils import is_subscribed

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    # Kanalga obuna tekshirish
    subscribed = await is_subscribed(bot, user_id, CHANNEL_ID)
    
    if not subscribed:
        channel_link = CHANNEL_ID if CHANNEL_ID.startswith("@") else f"@{CHANNEL_ID}"
        await message.answer(
            f"👋 <b>Salom! AnonymChat botiga xush kelibsiz!</b>\n\n"
            f"🔒 Botdan foydalanish uchun avval kanalimizga obuna bo'ling:\n"
            f"📢 {channel_link}\n\n"
            f"Obuna bo'lgach <b>✅ Tekshirish</b> tugmasini bosing.",
            reply_markup=subscribe_keyboard(CHANNEL_ID)
        )
        return
    
    await check_and_proceed(message.from_user.id, message, bot)


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    subscribed = await is_subscribed(bot, user_id, CHANNEL_ID)
    
    if not subscribed:
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        return
    
    await callback.message.delete()
    await check_and_proceed(user_id, callback.message, bot, from_callback=True, callback=callback)


async def check_and_proceed(user_id: int, message: Message, bot: Bot,
                             from_callback: bool = False, callback=None):
    from aiogram.fsm.context import FSMContext
    
    user = await get_user(user_id)
    
    if user:
        # Ro'yxatdan o'tgan — asosiy menyuga
        from database import is_premium
        premium = await is_premium(user_id)
        
        sender = callback.message if from_callback else message
        await sender.answer(
            f"✅ <b>Xush kelibsiz, {user['full_name']}!</b>\n\n"
            f"Pastdagi menyu orqali muloqot boshlang 👇",
            reply_markup=main_menu_keyboard(premium)
        )
    else:
        # Yangi foydalanuvchi — ro'yxatdan o'tish
        from aiogram.fsm.context import FSMContext
        
        sender = callback.message if from_callback else message
        await sender.answer(
            "🎉 <b>Kanalga obuna bo'ldingiz!</b>\n\n"
            "Endi ro'yxatdan o'ting. Bu tez va oson!\n\n"
            "👇 Jinsingizni tanlang:"
        )
        
        from handlers.registration import start_registration
        await start_registration(sender, user_id)
