import asyncio
import json
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8996747968:AAHdVCmUIASZNhaUj-qp1m-JsRrqIq8udII"
ADMIN_CHAT_ID = 644112527

# Ваша ссылка на GitHub Pages из раздела Settings -> Pages
WEB_APP_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/"

logging.basicConfig(level=logging.INFO)

# ==================== БАЗА ДАННЫХ ====================
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    roblox_nick TEXT,
    fio TEXT,
    birth_date TEXT,
    gender TEXT,
    bio TEXT,
    status TEXT
)
""")
conn.commit()

router = Router()

# ==================== СПРАВКА И КОМАНДЫ ====================

HELP_TEXT = (
    "📖 **Command List / Список команд:**\n\n"
    "• `/start` — Open main menu / Открыть главное меню\n"
    "• `/help` — Show command list / Показать справку\n"
    "• `/profile` — View character profile / Посмотреть профиль\n"
    "• `/delete` — Reset character & re-register / Сбросить и заново зарегистрироваться"
)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="Markdown")

@router.callback_query(F.data == "show_help")
async def process_show_help(callback: CallbackQuery):
    await callback.message.answer(HELP_TEXT, parse_mode="Markdown")

# ==================== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ====================

@router.message(Command("profile"))
@router.callback_query(F.data == "show_profile")
async def show_profile_handler(event: Message | CallbackQuery):
    user_id = event.from_user.id
    cursor.execute("""
    SELECT roblox_nick, fio, birth_date, gender, bio, status 
    FROM users WHERE user_id = ?
    """, (user_id,))
    user = cursor.fetchone()

    if not user:
        text = "❌ You don't have a registered character yet. Click below to start:"
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="📝 Register Character (Web App)", 
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ]])
    else:
        status_map = {
            "approved": "✅ Approved / Одобрено", 
            "pending": "⏳ Under Review / На проверке", 
            "rejected": "❌ Rejected / Отклонено"
        }
        status_str = status_map.get(user[5], "Unknown")

        text = (
            f"👤 **Canadian ID Character Profile**\n"
            f"Status: **{status_str}**\n\n"
            f"🎮 **Roblox Username:** {user[0]}\n"
            f"📛 **Full Name:** {user[1]}\n"
            f"📅 **Date of Birth:** {user[2]}\n"
            f"⚧ **Gender:** {user[3]}\n"
            f"📖 **Biography:** {user[4]}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Delete Character", callback_data="user_delete_self")],
            [InlineKeyboardButton(text="◀️ Main Menu", callback_data="go_main_menu")]
        ])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# ==================== ОБРАБОТЧИКИ СБРОСА И УДАЛЕНИЯ ====================

@router.message(Command("delete"))
@router.message(Command("reset"))
async def cmd_delete_character(message: Message, state: FSMContext):
    await state.clear()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📝 Start Registration", 
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]])
    await message.answer(
        "🗑 Your RP character profile has been deleted!\n"
        "You can now submit a new registration.",
        reply_markup=kb
    )

@router.callback_query(F.data == "user_delete_self")
async def process_user_delete_self(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (callback.from_user.id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📝 Start Registration", 
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    ]])
    await callback.message.edit_text(
        "🗑 Your RP character profile has been deleted.\n\n"
        "Click below to fill out the form again:",
        reply_markup=kb
    )

# ==================== СТАРТ И ВЕБ-АПП ====================

@router.message(CommandStart())
@router.callback_query(F.data == "go_main_menu")
async def cmd_start(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    cursor.execute("SELECT fio, status FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        fio, status = user
        if status == "approved":
            text = f"✅ You have an active character: **{fio}**."
        else:
            text = f"⏳ Your character registration for **{fio}** is under review."

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 View Profile", callback_data="show_profile")],
            [InlineKeyboardButton(text="ℹ️ Help / Commands", callback_data="show_help")],
            [InlineKeyboardButton(text="🗑 Delete Character", callback_data="user_delete_self")]
        ])
    else:
        text = (
            "🇨🇦 **Welcome to the Canadian Passport & Citizen Registration Portal!**\n\n"
            "Click the button below to fill out your character registration form via the Web Application:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📝 Fill Registration Form", 
                web_app=WebAppInfo(url=WEB_APP_URL)
            )],
            [InlineKeyboardButton(text="ℹ️ Help / Commands", callback_data="show_help")]
        ])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

# ==================== ПРИЕМ ДАННЫХ ИЗ WEB APP ====================

@router.message(F.web_app_data)
async def handle_web_app_data(message: Message, bot: Bot):
    try:
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        username = message.from_user.username or "N/A"

        roblox_nick = data.get("robloxNick", "N/A")
        full_name = data.get("fullName", "N/A")
        dob = data.get("dob", "N/A")
        gender = data.get("gender", "N/A")
        bio = data.get("bio", "N/A")

        cursor.execute("""
        INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, roblox_nick, full_name, dob, gender, bio, "pending"))
        conn.commit()

        # Отправка анкеты админу
        admin_text = (
            f"📋 **New Registration Submitted via Web App:**\n"
            f"👤 From: @{username} (ID: `{user_id}`)\n\n"
            f"🎮 **Roblox Username:** {roblox_nick}\n"
            f"📛 **Full Name:** {full_name}\n"
            f"📅 **Date of Birth:** {dob}\n"
            f"⚧ **Gender:** {gender}\n"
            f"📖 **Biography:** {bio}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user_id}")
        ]])

        await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_markup=kb, parse_mode="Markdown")
        await message.answer(
            "🎉 **Registration Submitted Successfully!**\n\n"
            "Your application has been sent to administrators for verification.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Error processing Web App submission: {e}")

# ==================== ДЕЙСТВИЯ АДМИНИСТРАТОРА ====================

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (target_id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🗑 Delete Record", callback_data=f"admin_delete_{target_id}")
    ]])

    await bot.send_message(target_id, "🎉 Your Canadian character registration has been approved!")
    await callback.message.edit_text(callback.message.text + "\n\n✅ **APPROVED**", reply_markup=kb)

@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status = 'rejected' WHERE user_id = ?", (target_id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🗑 Delete Record", callback_data=f"admin_delete_{target_id}")
    ]])

    await bot.send_message(target_id, "❌ Your character registration application was rejected.")
    await callback.message.edit_text(callback.message.text + "\n\n❌ **REJECTED**", reply_markup=kb)

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[2])
    cursor.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
    conn.commit()

    await bot.send_message(target_id, "ℹ️ Your profile was deleted by an admin. You can register again via /start.")
    await callback.message.edit_text(callback.message.text + "\n\n🗑 **DELETED BY ADMIN**")

# ==================== ЗАПУСК ====================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
