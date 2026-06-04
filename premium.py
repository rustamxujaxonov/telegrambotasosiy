import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import PREMIUM_PLANS, CARD_NUMBER, CARD_OWNER, ADMIN_GROUP_ID
from database import get_user, create_premium_request, is_premium
from keyboards import premium_plans_keyboard, back_to_menu_keyboard, main_menu_keyboard

router = Router()
logger = logging.getLogger(__name__)


class PremiumState(StatesGroup):
    waiting_receipt = State()


@router.callback_query(F.data.startswith("buy_premium_"))
async def buy_premium(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.replace("buy_premium_", "")
    plan = PREMIUM_PLANS.get(plan_key)
    
    if not plan:
        await callback.answer("❌ Noto'g'ri tarif!", show_alert=True)
        return
    
    user = await get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Avval ro'yxatdan o'ting!", show_alert=True)
        return
    
    await state.update_data(plan_key=plan_key)
    await state.set_state(PremiumState.waiting_receipt)
    
    await callback.message.edit_text(
        f"💳 <b>{plan['name']} Premium — {plan['price']:,} UZS</b>\n\n"
        f"To'lov uchun karta ma'lumotlari:\n\n"
        f"💳 <b>Karta raqami:</b> <code>{CARD_NUMBER}</code>\n"
        f"👤 <b>Ism Familiya:</b> <code>{CARD_OWNER}</code>\n\n"
        f"📤 <b>To'lovni amalga oshirib, chekni shu yerga tashlang!</b>\n\n"
        f"⚠️ Faqat <b>screenshot (surat)</b> shaklida yuboring.\n"
        f"Tekshirilgach, {plan['days']} kunlik premium beriladi.",
        reply_markup=back_to_menu_keyboard()
    )
    await callback.answer()


@router.message(PremiumState.waiting_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    data = await state.get_data()
    plan_key = data.get("plan_key")
    
    if not plan_key:
        await state.clear()
        return
    
    plan = PREMIUM_PLANS.get(plan_key)
    photo_file_id = message.photo[-1].file_id
    
    # So'rovni saqlash
    request_id = await create_premium_request(user_id, plan_key, photo_file_id)
    
    user = await get_user(user_id)
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
    
    # Admin guruhiga yuborish
    from keyboards import admin_confirm_keyboard
    try:
        admin_msg = await bot.send_photo(
            ADMIN_GROUP_ID,
            photo=photo_file_id,
            caption=(
                f"💰 <b>Yangi Premium So'rov #{request_id}</b>\n\n"
                f"👤 Foydalanuvchi: <b>{user['full_name'] if user else 'Noma lum'}</b>\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"📱 Username: {username}\n"
                f"🎂 Yosh: <b>{user['age'] if user else '?'}</b>\n"
                f"📍 Viloyat: <b>{user['region'] if user else '?'}</b>\n"
                f"💎 Tarif: <b>{plan['name']}</b> — {plan['price']:,} UZS\n"
                f"📅 Muddat: <b>{plan['days']} kun</b>"
            ),
            reply_markup=admin_confirm_keyboard(request_id, plan_key)
        )
        
        # Admin xabar ID sini saqlash
        from database import update_premium_request
        await update_premium_request(request_id, admin_msg_id=admin_msg.message_id)
        
    except Exception as e:
        logger.error(f"Admin guruhiga xabar yuborishda xato: {e}")
        await message.answer(
            "⚠️ Texnik muammo yuz berdi. Keyinroq urinib ko'ring yoki admin bilan bog'laning."
        )
        await state.clear()
        return
    
    await state.clear()
    
    premium = await is_premium(user_id)
    await message.answer(
        f"✅ <b>Chek qabul qilindi!</b>\n\n"
        f"📋 So'rov #{request_id}\n"
        f"💎 Tarif: <b>{plan['name']}</b>\n\n"
        f"⏳ Admin tekshirgandan so'ng <b>{plan['days']} kunlik premium</b> beriladi.\n"
        f"Odatda 5-30 daqiqa ichida.",
        reply_markup=main_menu_keyboard(premium)
    )


@router.message(PremiumState.waiting_receipt)
async def receipt_not_photo(message: Message):
    """Rasm emas narsa yuborilgan"""
    if message.text in ["🔙 Menyuga qaytish"]:
        return
    
    await message.answer(
        "📸 <b>Iltimos, to'lov chekini RASM (screenshot) shaklida yuboring!</b>\n\n"
        "Matn yoki boshqa fayllar qabul qilinmaydi."
    )
