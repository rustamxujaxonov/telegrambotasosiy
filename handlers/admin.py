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
    request_id = int(callback.data.replace("admin_approve_", ""))
    
    request = await get_premium_request(request_id)
    if not request:
        await callback.answer("❌ So'rov topilmadi!", show_alert=True)
        return
    
    if request["status"] != "pending":
        await callback.answer(f"⚠️ Bu so'rov allaqachon {request['status']} holatida!", show_alert=True)
        return
    
    # 1. 'days' o'zgaruvchisini shu yerda aniqlab olamiz
    plan = PREMIUM_PLANS.get(request["plan_key"], {})
    days = plan.get("days", 0)
    
    # 2. Premium berish
    await grant_premium(request["user_id"], days)
    await update_premium_request(request_id, status="approved")
    
    # 3. Foydalanuvchiga xabar
    try:
        await bot.send_message(
            request["user_id"],
            f"🎉 <b>Premium aktivlashtirildi!</b>\n\n"
            f"✅ <b>{plan.get('name', '')} Premium</b> hisobingizga qo'shildi.\n"
            f"📅 Muddat: <b>{days} kun</b>"
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga xabar yuborishda xato: {e}")
    
    # 4. Admin xabarini yangilash (Xato chiqmaydigan versiya)
    admin_name = callback.from_user.full_name
    await callback.message.delete()
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"{callback.message.caption or 'Premium so\'rovi'}\n\n"
             f"✅ <b>TASDIQLANDI</b> — {admin_name} tomonidan\n"
             f"👑 {days} kunlik premium berildi",
        parse_mode="HTML"
    )
    await callback.answer(f"✅ {days} kunlik premium berildi!", show_alert=True)

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
