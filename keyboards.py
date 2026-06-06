from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Stars ishlash")],
            [KeyboardButton(text="⭐ Stars yechish"), KeyboardButton(text="💰 Hisobim")],
            [KeyboardButton(text="📋 Murojaat"),      KeyboardButton(text="📄 To'lovlar tarixi")],
        ],
        resize_keyboard=True
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="⏳ Kutayotgan so'rovlar")],
            [KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="🔙 Asosiy menyu")],
        ],
        resize_keyboard=True
    )


def confirm_withdraw(wid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{wid}"),
            InlineKeyboardButton(text="❌ Rad etish",  callback_data=f"reject_{wid}"),
        ]
    ])
