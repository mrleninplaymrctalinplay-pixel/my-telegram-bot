import asyncio
import io
import json
import logging
import os
import sqlite3

from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from PIL import Image, ImageDraw

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8996747968:AAHdVCmUIASZNhaUj-qp1m-JsRrqIq8udII"
ADMIN_CHAT_ID = -1003913257980
WEB_APP_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/"

logging.basicConfig(level=logging.INFO)
router = Router()

class RejectState(StatesGroup):
    waiting_for_reason = State()

# ==================== БАЗА ДАННЫХ ====================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    roblox_nick TEXT,
    fio TEXT,
    birth_date TEXT,
    gender TEXT,
    skin_url TEXT,
    bio TEXT,
    signature TEXT,
    status TEXT DEFAULT 'none',
    language TEXT DEFAULT 'ru'
)
""")
conn.commit()

# ==================== ГЕНЕРАЦИЯ ID-КАРТЫ ====================

def generate_id_card(fio: str, dob: str, gender: str, roblox: str, signature: str) -> io.BytesIO:
    img = Image.new('RGB', (600, 350), color='#f4f1ea')
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, 140, 350], fill='#8b0000')
    draw.text((160, 20), "CANADA", fill='#8b0000', font_size=28)
    draw.text((160, 55), "PERSONAL IDENTIFICATION CARD / CARTE D'IDENTITÉ", fill='#555555', font_size=11)
    draw.line([(160, 75), (570, 75)], fill='#8b0000', width=2)

    draw.text((160, 90), "FULL NAME / NOM:", fill='#777777', font_size=10)
    draw.text((160, 105), str(fio).upper(), fill='#000000', font_size=18)

    draw.text((160, 135), "DATE OF BIRTH / DATE DE NAISSANCE:", fill='#777777', font_size=10)
    draw.text((160, 150), str(dob), fill='#000000', font_size=14)

    draw.text((360, 135), "SEX / SEXE:", fill='#777777', font_size=10)
    draw.text((360, 150), str(gender).upper(), fill='#000000', font_size=14)

    draw.text((160, 180), "ROBLOX ID:", fill='#777777', font_size=10)
    draw.text((160, 195), str(roblox), fill='#000000', font_size=14)

    draw.text((160, 230), "SIGNATURE:", fill='#777777', font_size=10)
    draw.text((160, 245), str(signature), fill='#000080', font_size=22)

    draw.text((35, 140), "🍁", fill='#ffffff', font_size=70)

    bio_stream = io.BytesIO()
    bio_stream.name = 'id_card.png'
    img.save(bio_stream, 'PNG')
    bio_stream.seek(0)
    return bio_stream

# ==================== ТЕКСТЫ И ЛОКАЛИЗАЦИЯ ====================

TEXTS = {
    "ru": {
        "welcome_lang": "👋 Пожалуйста, выберите язык / Please select your language:",
        "start": "🇨🇦 **Добро пожаловать в портал регистрации граждан Канады!**\n\nНажмите кнопку ниже, чтобы заполнить анкету через мини-приложение:",
        "form_btn": "📝 Заполнить анкету",
        "help_btn": "ℹ️ Помощь / Команды",
        "profile_btn": "👤 Профиль",
        "delete_btn": "🗑 Удалить персонажа",
        "lang_btn": "🌐 Сменить язык",
        "active_char": "✅ У вас есть активный персонаж: **{fio}**.",
        "pending_char": "⏳ Ваша анкета для **{fio}** находится на проверке.",
        "no_char": "❌ У вас пока нет зарегистрированного персонажа.",
        "deleted": "🗑 Ваш профиль персонажа успешно удален!",
        "submitted": "🎉 **Анкета успешно отправлена!**\n\nВаша заявка передана администраторам на проверку.",
        "help": "📖 **Список команд:**\n\n• `/start` — Главное меню\n• `/help` — Справка\n• `/profile` — Профиль персонажа\n• `/delete` — Удалить персонажа и пройти регистрацию заново\n• `/language` — Сменить язык",
        "status_approved": "✅ Одобрено",
        "status_pending": "⏳ На проверке",
        "status_rejected": "❌ Отклонено"
    },
    "en": {
        "welcome_lang": "👋 Please select your language:",
        "start": "🇨🇦 **Welcome to the Canadian Passport & Citizen Registration Portal!**\n\nClick the button below to fill out your character registration form via the Web Application:",
        "form_btn": "📝 Fill Registration Form",
        "help_btn": "ℹ️ Help / Commands",
        "profile_btn": "👤 View Profile",
        "delete_btn": "🗑 Delete Character",
        "lang_btn": "🌐 Change Language",
        "active_char": "✅ You have an active character: **{fio}**.",
        "pending_char": "⏳ Your registration for **{fio}** is under review.",
        "no_char": "❌ You don't have a registered character yet.",
        "deleted": "🗑 Your character profile has been deleted!",
        "submitted": "🎉 **Registration Submitted Successfully!**\n\nYour application has been sent to administrators for verification.",
        "help": "📖 **Command List:**\n\n• `/start` — Main Menu\n• `/help` — Help\n• `/profile` — View Profile\n• `/delete` — Delete character & re-register\n• `/language` — Change language",
        "status_approved": "✅ Approved",
        "status_pending": "⏳ Under Review",
        "status_rejected": "❌ Rejected"
    }
}

def get_user_lang(user_id: int) -> str:
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res and res[0] in TEXTS else "ru"

def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
        ]
    ])

# ==================== ХЕНДЛЕРЫ ЯЗЫКА И МЕНЮ ====================

@router.message(Command("language"))
@router.callback_query(F.data == "change_language")
async def select_language(event: Message | CallbackQuery):
    text = "🌐 **Select Language / Выберите язык:**"
    kb = get_lang_keyboard()
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery):
    lang_code = callback.data.split("_")[2]
    user_id = callback.from_user.id
    cursor.execute("INSERT INTO users (user_id, language, status) VALUES (?, ?, 'none') ON CONFLICT(user_id) DO UPDATE SET language=excluded.language", (user_id, lang_code))
    conn.commit()
    await callback.answer("Language updated!")
    await show_main_menu(callback, user_id, lang_code)

async def show_main_menu(event: Message | CallbackQuery, user_id: int, lang: str):
    t = TEXTS.get(lang, TEXTS["ru"])
    cursor.execute("SELECT fio, status FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    localized_webapp_url = f"{WEB_APP_URL}?lang={lang}"

    if user and user[0] and user[1] in ["approved", "pending"]:
        fio, status = user[0], user[1]
        text = t["active_char"].format(fio=fio) if status == "approved" else t["pending_char"].format(fio=fio)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["profile_btn"], callback_data="show_profile")],
            [InlineKeyboardButton(text=t["help_btn"], callback_data="show_help")],
            [InlineKeyboardButton(text=t["lang_btn"], callback_data="change_language")],
            [InlineKeyboardButton(text=t["delete_btn"], callback_data="user_delete_self")]
        ])
    else:
        text = t["start"]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["form_btn"], web_app=WebAppInfo(url=localized_webapp_url))],
            [InlineKeyboardButton(text=t["help_btn"], callback_data="show_help")],
            [InlineKeyboardButton(text=t["lang_btn"], callback_data="change_language")]
        ])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, status, language) VALUES (?, 'none', 'ru')", (user_id,))
        conn.commit()
        await message.answer(TEXTS["ru"]["welcome_lang"], reply_markup=get_lang_keyboard())
    else:
        await show_main_menu(message, user_id, row[0] or "ru")

@router.callback_query(F.data == "go_main_menu")
async def process_go_main_menu(callback: CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    await show_main_menu(callback, callback.from_user.id, lang)

@router.message(Command("help"))
@router.callback_query(F.data == "show_help")
async def cmd_help(event: Message | CallbackQuery):
    lang = get_user_lang(event.from_user.id)
    text = TEXTS[lang]["help"]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Menu", callback_data="go_main_menu")]])
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.message(Command("profile"))
@router.callback_query(F.data == "show_profile")
async def show_profile_handler(event: Message | CallbackQuery):
    user_id = event.from_user.id
    lang = get_user_lang(user_id)
    t = TEXTS.get(lang, TEXTS["ru"])
    localized_webapp_url = f"{WEB_APP_URL}?lang={lang}"

    cursor.execute("SELECT roblox_nick, fio, birth_date, gender, bio, signature, status, skin_url FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or not user[1]:
        text = t["no_char"]
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["form_btn"], web_app=WebAppInfo(url=localized_webapp_url))]])
    else:
        status_str = t.get(f"status_{user[6]}", user[6])
        text = (
            f"👤 **Профиль персонажа**\n"
            f"Статус: **{status_str}**\n\n"
            f"🎮 **Ник в Roblox:** {user[0]}\n"
            f"📛 **Имя и Фамилия:** {user[1]}\n"
            f"📅 **Дата рождения:** {user[2]}\n"
            f"⚧ **Пол:** {user[3]}\n"
            f"🖼 **Скин:** {user[7]}\n"
            f"📖 **Биография:** {user[4]}\n"
            f"✍️ **Подпись:** `{user[5]}`"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["delete_btn"], callback_data="user_delete_self")],
            [InlineKeyboardButton(text="◀️ Menu", callback_data="go_main_menu")]
        ])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.message(Command("delete"))
@router.callback_query(F.data == "user_delete_self")
async def cmd_delete_character(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    lang = get_user_lang(user_id)
    t = TEXTS.get(lang, TEXTS["ru"])
    localized_webapp_url = f"{WEB_APP_URL}?lang={lang}"

    await state.clear()
    cursor.execute("UPDATE users SET roblox_nick=NULL, fio=NULL, birth_date=NULL, gender=NULL, skin_url=NULL, bio=NULL, signature=NULL, status='none' WHERE user_id = ?", (user_id,))
    conn.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["form_btn"], web_app=WebAppInfo(url=localized_webapp_url))]])
    if isinstance(event, Message):
        await event.answer(t["deleted"], reply_markup=kb)
    else:
        await event.message.edit_text(t["deleted"], reply_markup=kb)

# ==================== ПРИЕМ ДАННЫХ ИЗ WEB APP ====================

@router.message(lambda msg: bool(msg.web_app_data))
async def handle_web_app_data(message: Message, bot: Bot):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    t = TEXTS.get(lang, TEXTS["ru"])

    try:
        data = json.loads(message.web_app_data.data)
        username = message.from_user.username or "N/A"

        roblox_nick = data.get("robloxNick", "N/A")
        full_name = data.get("fullName", "N/A")
        dob = data.get("dob", "N/A")
        gender = data.get("gender", "N/A")
        skin_url = data.get("skinUrl", "N/A")
        bio = data.get("bio", "N/A")
        signature = data.get("signature", "N/A")

        cursor.execute("""
        INSERT INTO users (user_id, username, roblox_nick, fio, birth_date, gender, skin_url, bio, signature, status, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            roblox_nick=excluded.roblox_nick,
            fio=excluded.fio,
            birth_date=excluded.birth_date,
            gender=excluded.gender,
            skin_url=excluded.skin_url,
            bio=excluded.bio,
            signature=excluded.signature,
            status='pending'
        """, (user_id, username, roblox_nick, full_name, dob, gender, skin_url, bio, signature, lang))
        conn.commit()

        admin_text = (
            f"📋 **Новая анкета на проверку:**\n"
            f"👤 От пользователя: @{username} (ID: `{user_id}`)\n\n"
            f"🎮 **Ник в Roblox:** {roblox_nick}\n"
            f"📛 **Имя и Фамилия:** {full_name}\n"
            f"📅 **Дата рождения:** {dob}\n"
            f"⚧ **Пол:** {gender}\n"
            f"🖼 **Ссылка на скин:** {skin_url}\n"
            f"📖 **Биография:** {bio}\n"
            f"✍️ **Официальная подпись:** `{signature}`"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")
        ]])

        await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_markup=kb, parse_mode="Markdown")
        await message.answer(t["submitted"], parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка обработки: {e}")

# ==================== ОДОБРЕНИЕ И ОТКЛОНЕНИЕ ====================

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])

    cursor.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (target_id,))
    conn.commit()

    cursor.execute("SELECT fio, birth_date, gender, roblox_nick, signature FROM users WHERE user_id = ?", (target_id,))
    user_data = cursor.fetchone()

    if user_data and user_data[0]:
        card_stream = generate_id_card(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4])
        photo_file = BufferedInputFile(card_stream.read(), filename="canadian_id.png")

        try:
            await bot.send_photo(
                chat_id=target_id,
                photo=photo_file,
                caption="🎉 **Ваша анкета одобрена!**\nВот ваш канадский ID-документ:"
            )
        except Exception as e:
            logging.error(f"Ошибка отправки фото пользователю {target_id}: {e}")
            await bot.send_message(target_id, "🎉 **Ваша анкета одобрена!**")

    await callback.message.edit_text(callback.message.text + "\n\n✅ **ОДОБРЕНО**")

# ==================== ЗАПУСК ====================

async def handle_health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
