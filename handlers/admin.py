from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS
from keyboards import admin_menu, main_menu

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class BroadcastState(StatesGroup):
    text = State()


# ── Admin panel kirish ─────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("⚙️ Admin panel", reply_markup=admin_menu())


# ── Statistika ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    if not is_admin(message.from_user.id):
        return

    row, pending = await db.get_stats()
    await message.answer(
        f"📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{row['total']}</b>\n"
        f"⭐ Jami stars: <b>{row['stars'] or 0}</b>\n"
        f"⏳ Kutayotgan so'rovlar: <b>{pending['cnt']}</b>",
        parse_mode="HTML"
    )


# ── Kutayotgan so'rovlar ───────────────────────────────────────────────────────

@router.message(F.text == "⏳ Kutayotgan so'rovlar")
async def pending_withdrawals(message: Message):
    if not is_admin(message.from_user.id):
        return

    rows = await db.get_pending_withdrawals()
    if not rows:
        await message.answer("✅ Hozircha kutayotgan so'rov yo'q.")
        return

    from keyboards import confirm_withdraw
    for r in rows:
        user = await db.get_user(r['user_id'])
        name = user['full_name'] if user else str(r['user_id'])
        await message.answer(
            f"🔔 <b>So'rov #{r['id']}</b>\n"
            f"👤 {name} (<code>{r['user_id']}</code>)\n"
            f"💰 {r['amount']} ⭐\n"
            f"💳 {r['card_number']}\n"
            f"🕐 {r['created_at'][:16]}",
            parse_mode="HTML",
            reply_markup=confirm_withdraw(r['id'])
        )


# ── Approve / Reject callback ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("approve_"))
async def approve_withdrawal(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return

    wid = int(call.data.split("_")[1])
    rows = await db.get_pending_withdrawals()
    target = next((r for r in rows if r['id'] == wid), None)

    if not target:
        await call.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_withdrawal_status(wid, "approved")
    await call.message.edit_text(
        call.message.text + "\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )
    await call.answer("✅ Tasdiqlandi!")

    try:
        await bot.send_message(
            target['user_id'],
            f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"💰 {target['amount']} ⭐ Stars\n"
            f"💳 {target['card_number']}\n\n"
            f"Pul tez orada kartangizga o'tkaziladi.",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject_"))
async def reject_withdrawal(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        return

    wid = int(call.data.split("_")[1])
    rows = await db.get_pending_withdrawals()
    target = next((r for r in rows if r['id'] == wid), None)

    if not target:
        await call.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_withdrawal_status(wid, "rejected")
    # Balansni qaytarish
    await db.add_stars(target['user_id'], target['amount'])

    await call.message.edit_text(
        call.message.text + "\n\n❌ <b>RAD ETILDI</b>",
        parse_mode="HTML"
    )
    await call.answer("❌ Rad etildi, stars qaytarildi.")

    try:
        await bot.send_message(
            target['user_id'],
            f"❌ <b>To'lov so'rovingiz rad etildi.</b>\n\n"
            f"💰 {target['amount']} ⭐ Stars balansingizga qaytarildi.",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ── Foydalanuvchilar ro'yxati ──────────────────────────────────────────────────

@router.message(F.text == "👥 Foydalanuvchilar")
async def users_list(message: Message):
    if not is_admin(message.from_user.id):
        return

    users = await db.get_all_users()
    text  = f"👥 <b>Foydalanuvchilar (top 20):</b>\n\n"
    for i, u in enumerate(users[:20], 1):
        text += (
            f"{i}. <a href='tg://user?id={u['user_id']}'>{u['full_name']}</a> "
            f"| ⭐{u['balance']} | 👥{u['total_refs']}\n"
        )
    await message.answer(text, parse_mode="HTML")


# ── Broadcast ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("📢 Barcha foydalanuvchilarga yuboriladigan xabarni yozing:")
    await state.set_state(BroadcastState.text)


@router.message(BroadcastState.text)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    users   = await db.get_all_users()
    success = 0
    failed  = 0

    await message.answer(f"⏳ {len(users)} ta foydalanuvchiga yuborilmoqda...")

    for u in users:
        try:
            await bot.send_message(u['user_id'], message.text, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ Yuborildi: <b>{success}</b>\n❌ Xato: <b>{failed}</b>",
        parse_mode="HTML"
    )
    await state.clear()


# ── Asosiy menyu ───────────────────────────────────────────────────────────────

@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🖥 Asosiy menyudasiz!", reply_markup=main_menu())
