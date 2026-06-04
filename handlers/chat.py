import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user, is_premium,
    add_to_queue, remove_from_queue, find_match,
    create_chat, get_active_chat, end_chat, get_partner_id
)
from keyboards import main_menu_keyboard, chat_keyboard, searching_keyboard
from utils import require_registration

router = Router()
logger = logging.getLogger(__name__)

# Qidiruv holati
class SearchState(StatesGroup):
    searching = State()
    in_chat = State()


# ─── MULOQOTCHI QIDIRISH (BEPUL) ────────────────────────────────────────────────

@router.message(F.text == "🔍 Muloqotchi qidirish")
async def search_any(message: Message, state: FSMContext, bot: Bot):
    user = await get_user(message.from_user.id)
    if not await require_registration(message, user):
        return
    
    # Faol chat mavjudmi?
    active = await get_active_chat(message.from_user.id)
    if active:
        await message.answer("⚠️ Avval joriy suhbatni tugatib keyin yangi qidirish boshlang.\n\n/stop — suhbatni tugatish")
        return
    
    await _start_search(message, state, bot, gender_want="any")


# ─── QIZ YOKI YIGIT QIDIRISH (PREMIUM) ─────────────────────────────────────────

@router.message(F.text.in_(["👑 Qiz qidirish (Premium)", "👑 Yigit qidirish (Premium)"]))
async def search_premium_locked(message: Message):
    from keyboards import premium_plans_keyboard
    await message.answer(
        "👑 <b>Bu funksiya faqat Premium foydalanuvchilar uchun!</b>\n\n"
        "Premium obuna bilan qiz yoki yigit jinsi bo'yicha qidirishingiz mumkin.\n\n"
        "💎 <b>Premium narxlari:</b>",
        reply_markup=premium_plans_keyboard()
    )


@router.message(F.text == "👧 Qiz qidirish")
async def search_female(message: Message, state: FSMContext, bot: Bot):
    user = await get_user(message.from_user.id)
    if not await require_registration(message, user):
        return
    
    premium = await is_premium(message.from_user.id)
    if not premium:
        from keyboards import premium_plans_keyboard
        await message.answer(
            "👑 <b>Bu funksiya faqat Premium foydalanuvchilar uchun!</b>\n\n"
            "💎 <b>Premium narxlari:</b>",
            reply_markup=premium_plans_keyboard()
        )
        return
    
    active = await get_active_chat(message.from_user.id)
    if active:
        await message.answer("⚠️ Avval joriy suhbatni tugatib keyin yangi qidirish boshlang.")
        return
    
    await _start_search(message, state, bot, gender_want="female")


@router.message(F.text == "👦 Yigit qidirish")
async def search_male(message: Message, state: FSMContext, bot: Bot):
    user = await get_user(message.from_user.id)
    if not await require_registration(message, user):
        return
    
    premium = await is_premium(message.from_user.id)
    if not premium:
        from keyboards import premium_plans_keyboard
        await message.answer(
            "👑 <b>Bu funksiya faqat Premium foydalanuvchilar uchun!</b>\n\n"
            "💎 <b>Premium narxlari:</b>",
            reply_markup=premium_plans_keyboard()
        )
        return
    
    active = await get_active_chat(message.from_user.id)
    if active:
        await message.answer("⚠️ Avval joriy suhbatni tugatib keyin yangi qidirish boshlang.")
        return
    
    await _start_search(message, state, bot, gender_want="male")


# ─── QIDIRUV LOGIKASI ────────────────────────────────────────────────────────────

async def _start_search(message: Message, state: FSMContext, bot: Bot, gender_want: str):
    user_id = message.from_user.id
    
    gender_text = {
        "any": "istalgan",
        "male": "👦 yigit",
        "female": "👧 qiz"
    }.get(gender_want, "istalgan")
    
    await message.answer(
        f"🔍 <b>Muloqotchi qidirilmoqda...</b>\n\n"
        f"Qidirish: <b>{gender_text}</b>\n\n"
        f"Iltimos kuting... ⏳",
        reply_markup=searching_keyboard()
    )
    
    await state.set_state(SearchState.searching)
    await state.update_data(gender_want=gender_want)
    
    # Navbatga qo'shish
    await add_to_queue(user_id, gender_want)
    
    # Mos muloqotchi qidirish
    partner_id = await find_match(user_id, gender_want)
    
    if partner_id:
        # Mos topildi!
        await remove_from_queue(user_id)
        await remove_from_queue(partner_id)
        
        chat_id = await create_chat(user_id, partner_id)
        
        await state.set_state(SearchState.in_chat)
        
        # Foydalanuvchi ma'lumotlarini olish
        user = await get_user(user_id)
        partner = await get_user(partner_id)
        premium_self = await is_premium(user_id)
        premium_partner = await is_premium(partner_id)
        
        # O'zimizga xabar
        partner_info = await _build_partner_info(partner, premium_self)
        await message.answer(
            f"✅ <b>Muloqotchi topildi!</b>\n\n"
            f"{partner_info}\n\n"
            f"💬 Endi xabar yozing. Suhbat boshlanmoqda...",
            reply_markup=chat_keyboard()
        )
        
        # Sherigimizga xabar
        user_info = await _build_partner_info(user, premium_partner)
        try:
            await bot.send_message(
                partner_id,
                f"✅ <b>Muloqotchi topildi!</b>\n\n"
                f"{user_info}\n\n"
                f"💬 Endi xabar yozing. Suhbat boshlanmoqda...",
                reply_markup=chat_keyboard()
            )
            # Partner state'ini yangilash
            from aiogram.fsm.context import FSMContext
            from aiogram.fsm.storage.memory import MemoryStorage
        except Exception as e:
            logger.error(f"Partner ga xabar yuborishda xato: {e}")
    else:
        # Navbatda turish — 60 soniya kutish
        asyncio.create_task(_wait_for_match(user_id, message, state, bot, gender_want))


async def _build_partner_info(user, is_premium_viewer: bool) -> str:
    """Muloqotchi haqida ma'lumot (premium bo'lsa to'liq)"""
    if is_premium_viewer and user:
        gender_text = "👦 Yigit" if user["gender"] == "male" else "👧 Qiz"
        return (
            f"👤 <b>Muloqotchi:</b>\n"
            f"📝 Ism: <b>{user['full_name']}</b>\n"
            f"🎂 Yosh: <b>{user['age']}</b>\n"
            f"{gender_text}\n"
            f"📍 Viloyat: <b>{user['region']}</b>"
        )
    else:
        if user:
            gender_emoji = "👦" if user["gender"] == "male" else "👧"
            return f"{gender_emoji} <b>Anonim muloqotchi</b> tayyor"
        return "👤 <b>Anonim muloqotchi</b>"


async def _wait_for_match(user_id: int, message: Message, state: FSMContext, bot: Bot, gender_want: str):
    """Muloqotchi topilguncha cheksiz kutish"""
    
    while True:
        # 1. State holatini tekshirish
        current = await state.get_state()
        if current != SearchState.searching.state:
            await remove_from_queue(user_id)
            return

        # 2. Bazadan mos muloqotchi qidirish
        partner_id = await find_match(user_id, gender_want)
        
        if partner_id:
            # Mos topildi!
            await remove_from_queue(user_id)
            await remove_from_queue(partner_id)
            
            chat_id = await create_chat(user_id, partner_id)
            await state.set_state(SearchState.in_chat)
            
            # Ma'lumotlarni olish
            user = await get_user(user_id)
            partner = await get_user(partner_id)
            premium_self = await is_premium(user_id)
            premium_partner = await is_premium(partner_id)
            
            # O'zimizga xabar
            partner_info = await _build_partner_info(partner, premium_self)
            await message.answer(
                f"✅ <b>Muloqotchi topildi!</b>\n\n{partner_info}\n\n💬 Suhbat boshlandi!",
                reply_markup=chat_keyboard()
            )
            
            # Sherigimizga xabar
            user_info = await _build_partner_info(user, premium_partner)
            try:
                await bot.send_message(
                    partner_id,
                    f"✅ <b>Muloqotchi topildi!</b>\n\n{user_info}\n\n💬 Suhbat boshlandi!",
                    reply_markup=chat_keyboard()
                )
            except Exception as e:
                logger.error(f"Partner ga xabar yuborishda xato: {e}")
            
            return # Siklni tugatamiz

        # 3. Mos topilmasa, 5 soniya kutib, qayta tekshirish
        await asyncio.sleep(5)


# ─── QIDIRUVNI BEKOR QILISH ─────────────────────────────────────────────────────

@router.message(SearchState.searching, F.text == "❌ Bekor qilish")
async def cancel_search(message: Message, state: FSMContext):
    await remove_from_queue(message.from_user.id)
    await state.clear()
    
    premium = await is_premium(message.from_user.id)
    await message.answer(
        "❌ <b>Qidiruv bekor qilindi.</b>",
        reply_markup=main_menu_keyboard(premium)
    )


# ─── CHAT DAVOMIDA XABARLAR ──────────────────────────────────────────────────────

@router.message(SearchState.in_chat, F.text == "⏭ Keyingisi")
async def next_partner(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    partner_id = await get_partner_id(user_id)
    
    await end_chat(user_id)
    
    if partner_id:
        premium_partner = await is_premium(partner_id)
        try:
            await bot.send_message(
                partner_id,
                "👋 <b>Muloqotchi suhbatni tugatdi.</b>\n\n"
                "Yangi muloqotchi qidirmoqchimisiz?",
                reply_markup=main_menu_keyboard(premium_partner)
            )
        except Exception:
            pass
    
    await state.clear()
    
    # Darhol yangi qidiruv
    data = await state.get_data()
    gender_want = data.get("gender_want", "any")
    
    premium = await is_premium(user_id)
    await message.answer("⏭ <b>Yangi muloqotchi qidirilmoqda...</b>", reply_markup=searching_keyboard())
    
    await state.set_state(SearchState.searching)
    await state.update_data(gender_want=gender_want)
    await add_to_queue(user_id, gender_want)
    
    partner_id = await find_match(user_id, gender_want)
    if partner_id:
        await remove_from_queue(user_id)
        await remove_from_queue(partner_id)
        await create_chat(user_id, partner_id)
        await state.set_state(SearchState.in_chat)
        
        user = await get_user(user_id)
        partner = await get_user(partner_id)
        premium_self = await is_premium(user_id)
        premium_partner2 = await is_premium(partner_id)
        
        partner_info = await _build_partner_info(partner, premium_self)
        await message.answer(
            f"✅ <b>Yangi muloqotchi topildi!</b>\n\n{partner_info}\n\n💬 Suhbat boshlandi!",
            reply_markup=chat_keyboard()
        )
        user_info = await _build_partner_info(user, premium_partner2)
        try:
            await bot.send_message(
                partner_id,
                f"✅ <b>Yangi muloqotchi!</b>\n\n{user_info}\n\n💬 Suhbat boshlandi!",
                reply_markup=chat_keyboard()
            )
        except Exception:
            pass
    else:
        import asyncio
        asyncio.create_task(_wait_for_match(user_id, message, state, bot, gender_want))


@router.message(SearchState.in_chat, F.text == "🚪 Chiqish")
async def leave_chat(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    partner_id = await get_partner_id(user_id)
    
    await end_chat(user_id)
    await state.clear()
    
    if partner_id:
        premium_partner = await is_premium(partner_id)
        try:
            await bot.send_message(
                partner_id,
                "🚪 <b>Muloqotchi suhbatni tark etdi.</b>\n\n"
                "Yangi muloqotchi qidirish uchun tugmani bosing.",
                reply_markup=main_menu_keyboard(premium_partner)
            )
        except Exception:
            pass
    
    premium = await is_premium(user_id)
    await message.answer(
        "🚪 <b>Suhbat tugatildi.</b>\n\nAsosiy menyuga qaytdingiz.",
        reply_markup=main_menu_keyboard(premium)
    )


# ─── XABAR ALMASHISH ────────────────────────────────────────────────────────────

@router.message(SearchState.in_chat)
async def relay_message(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    partner_id = await get_partner_id(user_id)
    
    if not partner_id:
        await state.clear()
        premium = await is_premium(user_id)
        await message.answer(
            "⚠️ <b>Suhbat topilmadi.</b> Qaytadan qidiring.",
            reply_markup=main_menu_keyboard(premium)
        )
        return
    
    try:
        if message.text:
            await bot.send_message(partner_id, f"💬 {message.text}")
        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id,
                                  caption=f"🖼 {message.caption or ''}")
        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)
        elif message.video:
            await bot.send_video(partner_id, message.video.file_id,
                                  caption=f"🎥 {message.caption or ''}")
        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.audio:
            await bot.send_audio(partner_id, message.audio.file_id)
        elif message.document:
            await bot.send_document(partner_id, message.document.file_id)
        elif message.video_note:
            await bot.send_video_note(partner_id, message.video_note.file_id)
        else:
            await message.answer("⚠️ Bu turdagi fayl yuborib bo'lmaydi.")
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")
        await state.clear()
        premium = await is_premium(user_id)
        await message.answer(
            "⚠️ <b>Suhbat uzildi.</b> Qaytadan urinib ko'ring.",
            reply_markup=main_menu_keyboard(premium)
        )
