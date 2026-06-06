# ⭐ Stars Referral Bot

## O'rnatish

```bash
pip install -r requirements.txt
```

## Sozlash

`config.py` faylini oching va quyidagilarni to'ldiring:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # @BotFather dan oling
ADMIN_IDS = [123456789]             # Sizning Telegram ID ingiz
STARS_PER_REFERRAL = 2              # Har taklif uchun stars
MIN_WITHDRAW = 10                   # Minimal yechish
```

## Ishga tushurish

```bash
python bot.py
```

---

## Funksiyalar

### 👤 Foydalanuvchi
| Buyruq / Tugma | Tavsif |
|---|---|
| /start | Ro'yxatdan o'tish, referral qabul qilish |
| 💰 Hisobim | Balans, taklif soni, ID |
| ⭐ Stars ishlash | Taklif havolasini ko'rish |
| ⭐ Stars yechish | Karta raqamiga yechish so'rovi |
| 📄 To'lovlar tarixi | Oxirgi 10 ta to'lov |
| 📋 Murojaat | Admin bilan bog'lanish |

### 🛡 Admin (/admin)
| Tugma | Tavsif |
|---|---|
| 📊 Statistika | Jami foydalanuvchi, stars, so'rovlar |
| ⏳ Kutayotgan so'rovlar | Yechish so'rovlarini ko'rish va tasdiqlash |
| 👥 Foydalanuvchilar | Top 20 foydalanuvchi ro'yxati |
| 📢 Xabar yuborish | Broadcast — barcha foydalanuvchilarga xabar |

---

## Fayl tuzilmasi
```
stars_bot/
├── bot.py           # Asosiy fayl
├── config.py        # Sozlamalar
├── database.py      # SQLite operatsiyalar
├── keyboards.py     # Tugmalar
├── requirements.txt
└── handlers/
    ├── user.py      # Foydalanuvchi handlerlari
    └── admin.py     # Admin handlerlari
```
