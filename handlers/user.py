from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import STARS_PER_REFERRAL, MIN_WITHDRAW, ADMIN_IDS, CHANNEL_ID
from keyboards import main_menu, confirm_withdraw

router = Router()


class WithdrawState(StatesGroup):
    amount = State()
    card   = State()


# ── Kanal tekshirish ───────────────────────────────────────────────────────────

async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return False


async def not_subscribed_msg(message: Message, bot: Bot):
    try:
        invite = await bot.create_chat_invite_link(CHANNEL_ID)
        link = invite.invite_link
    except Exception:
        link = "https://t.me/"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=link)],
        [InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_sub")]
    ])
    await message.answer(
        "❌ Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz kerak!\n\n"
        "A'zo bo'lgandan keyin ✅ tugmasini bosing.",
        reply_markup=kb
    )


# ── A'zo bo'ldim callback ──────────────────────────────────────────────────────

@router.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery, bot: Bot):
    if await check_subscription(bot, call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi botdan foydalanishingiz mumkin.", reply_markup=main_menu())
    else:
        await call.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)


# ── /start ─────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id   = message.from_user.id
    username  = message.from_user.username or ""
    full_name = message.from_user.full_name

    # Kanal tekshirish
    if not await check_subscription(bot, user_id):
        await not_subscribed_msg(message, bot)
        return

    # referral parametrini olish
    args   = message.text.split()
    ref_by = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    existing = await db.get_user(user_id)

    if not existing:
        await db.register_user(user_id, username, full_name, ref_by)
        if ref_by and ref_by != user_id:
            ref_user = await db.get_user(ref_by)
            if ref_user:
                await db.add_stars(ref_by, STARS_PER_REFERRAL)
                await db.inc_referral(ref_by)
                try:
                    await bot.send_message(
                        ref_by,
                        f"🎉 Yangi taklif! <b>{full_name}</b> botga qo'shildi.\n"
                        f"Hisobingizga <b>{STARS_PER_REFERRAL} ⭐ STARS</b> qo'shildi!",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

        await message.answer(
            f"👋 Xush kelibsiz, <b>{full_name}</b>!\n\n"
            f"⭐ Do'stlaringizni taklif qiling va har bir taklif uchun "
            f"<b>{STARS_PER_REFERRAL} Stars</b> oling!",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    else:
        await message.answer("🖥 Asosiy menyudasiz!", reply_markup=main_menu())


# ── Kanal tekshirish — barcha tugmalar uchun ──────────────────────────────────

async def sub_check_middleware(message: Message, bot: Bot) -> bool:
    if not await check_subscription(bot, message.from_user.id):
        await not_subscribed_msg(message, bot)
        return False
    return True


# ── Hisobim ────────────────────────────────────────────────────────────────────

@router.message(F.text == "💰 Hisobim")
async def my_account(message: Message, bot: Bot):
    if not await sub_check_middleware(message, bot): return
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing.")
        return

    bot_username = (await bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user['user_id']}"

    await message.answer(
        f"🆔 Sizning ID raqamingiz: <code>{user['user_id']}</code>\n\n"
        f"💰 Balansingiz: <b>{user['balance']} ⭐ STARS</b>\n"
        f"👥 Takliflaringiz: <b>{user['total_refs']} ta</b>\n"
        f"💳 Yechib olgan pullaringiz: <b>{user['total_withdrawn']} ⭐ STARS</b>\n\n"
        f"🔗 Sizning taklif havolangiz:\n<code>{ref_link}</code>",
        parse_mode="HTML"
    )


# ── Stars ishlash ──────────────────────────────────────────────────────────────

@router.message(F.text == "⭐ Stars ishlash")
async def how_to_earn(message: Message, bot: Bot):
    if not await sub_check_middleware(message, bot): return
    bot_username = (await bot.get_me()).username
    user_id = message.from_user.id
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    await message.answer(
        "💡 <b>Stars qanday ishlash mumkin?</b>\n\n"
        f"1️⃣ Quyidagi havolangizni do'stlaringizga yuboring:\n"
        f"<code>{ref_link}</code>\n\n"
        f"2️⃣ Har bir ro'yxatdan o'tgan do'stingiz uchun <b>{STARS_PER_REFERRAL} ⭐ Stars</b> olasiz!\n\n"
        f"3️⃣ {MIN_WITHDRAW} ⭐ Stars to'planganidan keyin yechib olishingiz mumkin.",
        parse_mode="HTML"
    )


# ── Stars yechish ──────────────────────────────────────────────────────────────

@router.message(F.text == "⭐ Stars yechish")
async def withdraw_start(message: Message, state: FSMContext, bot: Bot):
    if not await sub_check_middleware(message, bot): return
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing.")
        return

    if user['balance'] < MIN_WITHDRAW:
        await message.answer(
            f"❌ Balansingiz yetarli emas.\n"
            f"Minimal yechish: <b>{MIN_WITHDRAW} ⭐</b>\n"
            f"Sizda: <b>{user['balance']} ⭐</b>",
            parse_mode="HTML"
        )
        return

    await message.answer(
        f"💳 Nechta Stars yechmoqchisiz?\n"
        f"(Minimal: {MIN_WITHDRAW}, Sizda: {user['balance']} ⭐)\n\n"
        f"Raqamni kiriting:"
    )
    await state.set_state(WithdrawState.amount)


@router.message(WithdrawState.amount)
async def withdraw_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return

    amount = int(message.text)
    user   = await db.get_user(message.from_user.id)

    if amount < MIN_WITHDRAW:
        await message.answer(f"❌ Minimal miqdor: {MIN_WITHDRAW} ⭐")
        return
    if amount > user['balance']:
        await message.answer(f"❌ Balansingizda faqat {user['balance']} ⭐ bor.")
        return

    await state.update_data(amount=amount)
    await message.answer("💳 Karta raqamingizni kiriting (16 raqam):")
    await state.set_state(WithdrawState.card)


@router.message(WithdrawState.card)
async def withdraw_card(message: Message, state: FSMContext, bot: Bot):
    card = message.text.replace(" ", "")
    if not card.isdigit() or len(card) != 16:
        await message.answer("❌ Karta raqami noto'g'ri! 16 ta raqam kiriting.")
        return

    data    = await state.get_data()
    amount  = data['amount']
    user_id = message.from_user.id

    await db.deduct_stars(user_id, amount)
    wid = await db.create_withdrawal(user_id, amount, card)

    await message.answer(
        f"✅ So'rovingiz qabul qilindi!\n\n"
        f"💰 Miqdor: <b>{amount} ⭐ STARS</b>\n"
        f"💳 Karta: <code>{card}</code>\n"
        f"📋 So'rov ID: #{wid}\n\n"
        f"Admin tez orada ko'rib chiqadi.",
        parse_mode="HTML"
    )
    await state.clear()

    user = await db.get_user(user_id)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🔔 <b>Yangi yechish so'rovi #{wid}</b>\n\n"
                f"👤 Foydalanuvchi: <a href='tg://user?id={user_id}'>{user['full_name']}</a>\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"💰 Miqdor: <b>{amount} ⭐</b>\n"
                f"💳 Karta: <code>{card}</code>",
                parse_mode="HTML",
                reply_markup=confirm_withdraw(wid)
            )
        except Exception:
            pass


# ── To'lovlar tarixi ───────────────────────────────────────────────────────────

@router.message(F.text == "📄 To'lovlar tarixi")
async def payment_history(message: Message, bot: Bot):
    if not await sub_check_middleware(message, bot): return
    rows = await db.get_user_withdrawals(message.from_user.id)
    if not rows:
        await message.answer("📭 Hali hech qanday to'lov yo'q.")
        return

    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
    text = "📄 <b>So'nggi to'lovlar:</b>\n\n"
    for r in rows:
        emoji = status_emoji.get(r['status'], "❓")
        text += (
            f"{emoji} #{r['id']} — <b>{r['amount']} ⭐</b>\n"
            f"   💳 {r['card_number']} | {r['created_at'][:10]}\n\n"
        )
    await message.answer(text, parse_mode="HTML")


# ── Murojaat ───────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Murojaat")
async def support(message: Message, bot: Bot):
    if not await sub_check_middleware(message, bot): return
    await message.answer(
        "📋 <b>Murojaat uchun:</b>\n\n"
        "Admin bilan bog'laning: @admin_username\n\n"
        "Yoki xabaringizni yozing, biz tez orada javob beramiz.",
        parse_mode="HTML"
    )
