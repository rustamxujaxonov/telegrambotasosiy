# 🤖 AnonymChat Bot

Telegram anonim tanishuv boti — Python + aiogram 3 + Railway

---

## 📋 Funksiyalar

| Funksiya | Bepul | Premium |
|---|---|---|
| Kanalga obuna tekshirish | ✅ | ✅ |
| Ro'yxatdan o'tish | ✅ | ✅ |
| Random muloqotchi qidirish | ✅ | ✅ |
| Profil sozlamalari | ✅ | ✅ |
| Qiz/Yigit bo'yicha qidirish | ❌ | ✅ |
| Muloqotchi ma'lumotlarini ko'rish | ❌ | ✅ |

## 💎 Premium Narxlari

| Tarif | Narx |
|---|---|
| 1 kunlik | 5,000 UZS |
| 3 kunlik | 7,000 UZS |
| 1 haftalik | 15,000 UZS |
| 1 oylik | 30,000 UZS |

---

## 🚀 Railway'da Deploy Qilish

### 1. GitHub'ga yuklash

```bash
cd anon_bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/anon-bot.git
git push -u origin main
```

### 2. Railway.app'da yangi loyiha yaratish

1. [railway.app](https://railway.app) ga kiring
2. **New Project** → **Deploy from GitHub repo** tanlang
3. Reponi tanlang
4. **Variables** bo'limida environment variablelarni qo'shing (quyida)

### 3. Environment Variables (Railway → Variables)

```
BOT_TOKEN         = 1234567890:ABCdefGHI...
CHANNEL_ID        = @your_channel
ADMIN_GROUP_ID    = -1001234567890
CARD_NUMBER       = 8600 1234 5678 9012
CARD_OWNER        = Ism Familiya
```

### 4. Volume qo'shish (ma'lumotlar bazasi uchun)

Railway'da **Volumes** bo'limidan:
- Mount path: `/app/data`

> ⚠️ Volume bo'lmasa, bot qayta ishga tushganda barcha ma'lumotlar o'chadi!

---

## 🔧 Mahalliy ishlatish

```bash
# 1. Virtual muhit yaratish
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Kutubxonalar o'rnatish
pip install -r requirements.txt

# 3. .env fayl yaratish
cp .env.example .env
# .env faylni to'ldiring

# 4. Botni ishga tushirish
python bot.py
```

---

## 📁 Fayl Tuzilmasi

```
anon_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── database.py         # Ma'lumotlar bazasi
├── keyboards.py        # Klaviaturalar
├── utils.py            # Yordamchi funksiyalar
├── handlers/
│   ├── __init__.py     # Handlerlar ro'yxati
│   ├── start.py        # Start + obuna
│   ├── registration.py # Ro'yxatdan o'tish
│   ├── menu.py         # Asosiy menyu
│   ├── chat.py         # Muloqot
│   ├── premium.py      # Premium xarid
│   ├── admin.py        # Admin panel
│   └── settings.py     # Profil sozlamalari
├── requirements.txt
├── Procfile
├── railway.toml
└── .env.example
```

---

## ⚙️ Sozlamalar

### Bot uchun kanal admini bo'lish
Bot kanalga obuna tekshirishi uchun **bot kanalga admin** bo'lishi kerak!

1. Kanalingizga boring
2. **Boshqaruvchilar** → **Boshqaruvchi qo'shish**
3. Botni qidiring va qo'shing
4. `Foydalanuvchilarni tekshirish` ruxsati bering

### Admin guruh
1. Telegram'da yangi guruh yarating
2. Botni guruhga qo'shing va **admin** qiling
3. Guruh ID ni aniqlash uchun: `@getmyid_bot` ga xabar yuboring

---

## 📞 Yordam

Muammo yuz bersa, kodni ko'rib chiqing yoki GitHub Issues oching.
