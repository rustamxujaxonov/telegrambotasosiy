import logging
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

logger = logging.getLogger(__name__)


async def is_subscribed(bot: Bot, user_id: int, channel_id: str) -> bool:
    """Foydalanuvchi kanalga obuna bo'lganini tekshirish"""
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status not in ("left", "kicked", "banned")
    except TelegramBadRequest as e:
        logger.warning(f"Obuna tekshirishda xato (kanal noto'g'ri?): {e}")
        return True  # Xato bo'lsa — o'tkazib yuborish
    except TelegramForbiddenError as e:
        logger.warning(f"Bot kanalga admin emas: {e}")
        return True  # Bot kanal admini bo'lmasa — o'tkazib yuborish
    except Exception as e:
        logger.error(f"is_subscribed xatosi: {e}")
        return True


async def require_registration(message: Message, user) -> bool:
    """Foydalanuvchi ro'yxatdan o'tganini tekshirish"""
    if not user:
        await message.answer(
            "❗ <b>Avval ro'yxatdan o'ting!</b>\n\n"
            "/start — boshlash"
        )
        return False
    return True


def format_premium_plans_text() -> str:
    """Premium tariflar matnini chiqarish"""
    from config import PREMIUM_PLANS
    lines = ["💎 <b>Premium narxlari:</b>\n"]
    for plan in PREMIUM_PLANS.values():
        lines.append(f"• {plan['name']}: <b>{plan['price']:,} UZS</b>")
    return "\n".join(lines)
