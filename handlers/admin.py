import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.filters import Filter

from config import ADMIN_GROUP_ID, PREMIUM_PLANS
from database import (
    get_premium_request, update_premium_request,
    grant_premium, get_user, is_premium
)
from keyboards import main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


class AdminGroupFilter(Filter):
    """Faqat admin guruhidagi callbacklarni qabul qilish"""
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.message.chat.id == ADMIN_GROUP_ID

@router.callback_query(AdminGroupFilter(), F.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery, bot: Bot):
    # ... yuqoridagi kodlar o'zgarishsiz ...

    # Admin xabarini yangilash (YANGILANGAN QISM)
    admin_name = callback.from_user.full_name
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=callback.message.caption + f"\n\n✅ <b>TASDIQLANDI</b> — {admin_name} tomonidan\n"
                                          f"👑 {days} kunlik premium berildi",
        reply_markup=None
    )
    await callback.answer(f"✅ {days} kunlik premium berildi!", show_alert=True)
    logger.info(f"Admin {callback.from_user.id} #{request_id} so'rovni tasdiqladi")


@router.callback_query(AdminGroupFilter(), F.data.startswith("admin_reject_"))
async def admin_reject(callback: CallbackQuery, bot: Bot):
    # ... yuqoridagi kodlar o'zgarishsiz ...

    # Admin xabarini yangilash (YANGILANGAN QISM)
    admin_name = callback.from_user.full_name
    await bot.edit_message_caption(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        caption=callback.message.caption + f"\n\n❌ <b>RAD ETILDI</b> — {admin_name} tomonidan",
        reply_markup=None
    )
    await callback.answer("❌ So'rov rad etildi!", show_alert=True)
    logger.info(f"Admin {callback.from_user.id} #{request_id} so'rovni rad etdi")
