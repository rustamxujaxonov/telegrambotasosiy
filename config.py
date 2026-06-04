import os

# Bot token - Railway environment variable'dan olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Kanal ID (obuna tekshiriladigan kanal)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")

# Admin guruh ID (chek ko'riladigan guruh)
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", "-1001234567890"))

# To'lov uchun karta ma'lumotlari
CARD_NUMBER = os.getenv("CARD_NUMBER", "8600 1234 5678 9012")
CARD_OWNER = os.getenv("CARD_OWNER", "Ism Familiya")

# SQLite database fayli (Railway'da persistent volume)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")
DB_PATH = "data/bot.db"

# Viloyatlar ro'yxati
REGIONS = [
    "Toshkent shahri", "Toshkent viloyati", "Samarqand",
    "Buxoro", "Farg'ona", "Andijon", "Namangan",
    "Qashqadaryo", "Surxondaryo", "Jizzax",
    "Sirdaryo", "Navoiy", "Xorazm", "Qoraqalpog'iston"
]

# Premium narxlar (UZS)
PREMIUM_PLANS = {
    "1_day":    {"name": "1 kunlik",  "price": 5000,  "days": 1},
    "3_days":   {"name": "3 kunlik",  "price": 7000,  "days": 3},
    "7_days":   {"name": "1 haftalik","price": 15000, "days": 7},
    "30_days":  {"name": "1 oylik",   "price": 30000, "days": 30},
}
