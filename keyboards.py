from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import REGIONS, PREMIUM_PLANS


# ─── OBUNA TUGMASI ──────────────────────────────────────────────────────────────

def subscribe_keyboard(channel_id: str) -> InlineKeyboardMarkup:
    channel = channel_id if channel_id.startswith("@") else f"@{channel_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{channel.lstrip('@')}")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])


# ─── RO'YXATDAN O'TISH ──────────────────────────────────────────────────────────

def gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👦 Yigit", callback_data="gender_male"),
            InlineKeyboardButton(text="👧 Qiz",   callback_data="gender_female"),
        ]
    ])


def regions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for region in REGIONS:
        builder.button(text=region, callback_data=f"region_{region}")
    builder.adjust(2)
    return builder.as_markup()


# ─── ASOSIY MENYU ───────────────────────────────────────────────────────────────

def main_menu_keyboard(is_premium_user: bool = False) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Muloqotchi qidirish")
    
    if is_premium_user:
        builder.button(text="👧 Qiz qidirish")
        builder.button(text="👦 Yigit qidirish")
    else:
        builder.button(text="👑 Qiz qidirish (Premium)")
        builder.button(text="👑 Yigit qidirish (Premium)")
    
    builder.button(text="⚙️ Profil sozlamalari")
    builder.button(text="👤 Mening profilim")
    builder.adjust(1, 2, 2)
    return builder.as_markup(resize_keyboard=True)


def chat_keyboard() -> ReplyKeyboardMarkup:
    """Muloqot davomida tugmalar"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="⏭ Keyingisi")
    builder.button(text="🚪 Chiqish")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def searching_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    return builder.as_markup(resize_keyboard=True)


# ─── PREMIUM ─────────────────────────────────────────────────────────────────────

def premium_plans_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, plan in PREMIUM_PLANS.items():
        text = f"💎 {plan['name']} — {plan['price']:,} UZS"
        builder.button(text=text, callback_data=f"buy_premium_{key}")
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="back_to_menu")]
    ])


# ─── ADMIN TUGMALARI ─────────────────────────────────────────────────────────────

def admin_confirm_keyboard(request_id: int, plan_key: str) -> InlineKeyboardMarkup:
    plan = PREMIUM_PLANS.get(plan_key, {})
    days = plan.get("days", 0)
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✅ {days} kunlik Premium berish",
                callback_data=f"admin_approve_{request_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"admin_reject_{request_id}"
            )
        ]
    ])


# ─── PROFIL SOZLAMALARI ─────────────────────────────────────────────────────────

def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Jinsni o'zgartirish",    callback_data="edit_gender")],
        [InlineKeyboardButton(text="🔢 Yoshni o'zgartirish",    callback_data="edit_age")],
        [InlineKeyboardButton(text="📍 Viloyatni o'zgartirish", callback_data="edit_region")],
        [InlineKeyboardButton(text="🔙 Menyuga qaytish",        callback_data="back_to_menu")],
    ])
