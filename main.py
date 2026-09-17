import asyncio
import io
import json
import logging
import sqlite3

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
    skin_url TEXT,
    bio TEXT,
    signature TEXT,
    status TEXT,
    language TEXT DEFAULT 'en'
)
""")
conn.commit()

# Автоматическое обновление структуры БД
for col_def in ["skin_url TEXT", "signature TEXT", "language TEXT DEFAULT 'en'"]:
    try:
        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
        conn.commit()
    except sqlite3.OperationalError:
        pass

# ==================== ГЕНЕРАЦИЯ ID-КАРТЫ ====================

def generate_id_card(fio: str, dob: str, gender: str, roblox: str, signature: str) -> io.BytesIO:
    img = Image.new('RGB', (600, 350), color='#f4f1ea')
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, 140, 350], fill='#8b0000')
    draw.text((160, 20), "CANADA", fill='#8b0000', font_size=28)
    draw.text((160, 55), "PERSONAL IDENTIFICATION CARD / CARTE D'IDENTITÉ", fill='#555555', font_size=11)
    draw.line([(160, 75), (570, 75)], fill='#8b0000', width=2)

    draw.text((160, 90), "FULL NAME / NOM:", fill='#777777', font_size=10)
    draw.text((160, 105), fio.upper(), fill='#000000', font_size=18)

    draw.text((160, 135), "DATE OF BIRTH / DATE DE NAISSANCE:", fill='#777777', font_size=10)
    draw.text((160, 150), dob, fill='#000000', font_size=14)

    draw.text((360, 135), "SEX / SEXE:", fill='#777777', font_size=10)
    draw.text((360, 150), gender.upper(), fill='#000000', font_size=14)

    draw.text((160, 180), "ROBLOX ID:", fill='#777777', font_size=10)
    draw.text((160, 195), roblox, fill='#000000', font_size=14)

    draw.text((160, 230), "SIGNATURE:", fill='#777777', font_size=10)
    draw.text((160, 245), signature, fill='#000080', font_size=22)

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
        "help": "📖 **Список команд:**\n\n• `/start` — Главное меню\n• `/help` — Справка\n• `/profile` — Профиль персонажа\n• `/delete` — Удалить персонажа и пройти регистрацию заново",
        "status_approved": "✅ Одобрено",
        "status_pending": "⏳ На проверке",
        "status_rejected": "❌ Отклонено"
    },
    "uk": {
        "welcome_lang": "👋 Будь ласка, оберіть мову / Please select your language:",
        "start": "🇨🇦 **Ласкаво просимо до порталу реєстрації громадян Канади!**\n\nНатисніть кнопку нижче, щоб заповнити анкету через міні-додаток:",
        "form_btn": "📝 Заповнити анкету",
        "help_btn": "ℹ️ Допомога / Команди",
        "profile_btn": "👤 Профіль",
        "delete_btn": "🗑 Видалити персонажа",
        "lang_btn": "🌐 Змінити мову",
        "active_char": "✅ У вас є активний персонаж: **{fio}**.",
        "pending_char": "⏳ Ваша анкета для **{fio}** перебуває на перевірці.",
        "no_char": "❌ У вас ще немає зареєстрованого персонажа.",
        "deleted": "🗑 Ваш профіль персонажа успішно видалено!",
        "submitted": "🎉 **Анкету успішно надіслано!**\n\nВашу заявку передано адміністраторам на перевірку.",
        "help": "📖 **Список команд:**\n\n• `/start` — Головне меню\n• `/help` — Довідка\n• `/profile` — Профіль персонажа\n• `/delete` — Видалити персонажа та пройти реєстрацію наново",
        "status_approved": "✅ Схвалено",
        "status_pending": "⏳ На перевірці",
        "status_rejected": "❌ Відхилено"
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
        "help": "📖 **Command List:**\n\n• `/start` — Main Menu\n• `/help` — Help\n• `/profile` — View Profile\n• `/delete` — Delete character & re-register",
        "status_approved": "✅ Approved",
        "status_pending": "⏳ Under Review",
        "status_rejected": "❌ Rejected"
    },
    "kk": {
        "welcome_lang": "👋 Тілді таңдаңыз / Please select your language:",
        "start": "🇨🇦 **Канада азаматтарын тіркеу порталына кош келдіңіз!**\n\nШағын қолданба арқылы сауалнаманы толтыру үшін төмендегі түймені басыңыз:",
        "form_btn": "📝 Сауалнаманы толтыру",
        "help_btn": "ℹ️ Көмек / Пәрмендер",
        "profile_btn": "👤 Профиль",
        "delete_btn": "🗑 Кейіпкерді өшіру",
        "lang_btn": "🌐 Тілді ауыстыру",
        "active_char": "✅ Сізде белсенді кейіпкер бар: **{fio}**.",
        "pending_char": "⏳ **{fio}** үшін сауалнамаңыз тексерілуде.",
        "no_char": "❌ Сізде әлі тіркелген кейіпкер жоқ.",
        "deleted": "🗑 Кейіпкер профилі сәтті өшірілді!",
        "submitted": "🎉 **Сауалнама сәтті жіберілді!**\n\nӨтінішіңіз әкімшілерге тексеруге жіберілді.",
        "help": "📖 **Пәрмендер тізімі:**\n\n• `/start` — Негізгі мәзір\n• `/help` — Анықтама\n• `/profile` — Кейіпкер профилі\n• `/delete` — Кейіпкерді өшіру және қайта тіркелу",
        "status_approved": "✅ Мақұлданды",
        "status_pending": "⏳ Тексерілуде",
        "status_rejected": "❌ Қабылданбады"
    }
}

def get_user_lang(user_id: int) -> str:
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res and res[0] in TEXTS else "en"

def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton(text="🇺🇦 Українська", callback_data="set_lang_uk")
        ],
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"),
            InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="set_lang_kk")
        ]
    ])

# ==================== ХЕНДЛЕРЫ ====================

@router.message(Command("language"))
@router.callback_query(F.data == "change_language")
async def select_language(event: Message | CallbackQuery):
    text = "🌐 **Select Language / Выберите язык / Оберіть мову / Тілді таңдаңыз:**"
    kb = get_lang_keyboard()
    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery):
    lang_code = callback.data.split("_")[2]
    user_id = callback.from_user.id
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang_code, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, language, status) VALUES (?, ?, 'none')", (user_id, lang_code))
    conn.commit()
    await callback.answer("Language updated!")
    await show_main_menu(callback, user_id, lang_code)

async def show_main_menu(event: Message | CallbackQuery, user_id: int, lang: str):
    t = TEXTS[lang]
    cursor.execute("SELECT fio, status FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    localized_webapp_url = f"{WEB_APP_URL}?lang={lang}"

    if user and user[1] in ["approved", "pending"]:
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
    if not row or not row[0]:
        await message.answer(TEXTS["en"]["welcome_lang"], reply_markup=get_lang_keyboard())
    else:
        await show_main_menu(message, user_id, row[0])

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
    t = TEXTS[lang]
    localized_webapp_url = f"{WEB_APP_URL}?lang={lang}"

    cursor.execute("SELECT roblox_nick, fio, birth_date, gender, bio, signature, status, skin_url FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user or not user[1]:
        text = t["no_char"]
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["form_btn"], web_app=WebAppInfo(url=localized_webapp_url))]])
    else:
        status_key = f"status_{user[6]}"
        status_str = t.get(status_key, user[6])

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
    t = TEXTS[lang]
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
    t = TEXTS[lang]

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
        UPDATE users SET username=?, roblox_nick=?, fio=?, birth_date=?, gender=?, skin_url=?, bio=?, signature=?, status='pending'
        WHERE user_id=?
        """, (username, roblox_nick, full_name, dob, gender, skin_url, bio, signature, user_id))
        conn.commit()

        # Карточка для админов всегда на русском языке
        admin_text = (
            f"📋 **Новая анкета на проверку:**\n"
            f"👤 От пользователя: @{username} (ID: `{user_id}`)\n"
            f"🌐 Язык игрока: `{lang}`\n\n"
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

    if user_data:
        card_stream = generate_id_card(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4])
        photo_file = BufferedInputFile(card_stream.read(), filename="canadian_id.png")

        try:
            await bot.send_photo(
                chat_id=target_id,
                photo=photo_file,
                caption="🎉 **Ваша анкета одобрена!**\nВот ваш канадский ID-документ:"
            )
        except Exception:
            pass

    await callback.message.edit_text(callback.message.text + "\n\n✅ **ОДОБРЕНО (ID выдан)**")

@router.callback_query(F.data.startswith("reject_"))
async def ask_reject_reason(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    await state.update_data(target_id=target_id, message_to_edit=callback.message)
    await state.set_state(RejectState.waiting_for_reason)

    await callback.message.reply("✍️ **Введите причину отказа для игрока:**")
    await callback.answer()

@router.message(RejectState.waiting_for_reason)
async def process_reject_reason(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_id = data['target_id']
    admin_msg = data['message_to_edit']
    reason = message.text

    cursor.execute("UPDATE users SET status = 'rejected' WHERE user_id = ?", (target_id,))
    conn.commit()

    try:
        await bot.send_message(
            target_id,
            f"❌ **Ваша анкета отклонена.**\n\n📌 **Причина:** {reason}\n\nВы можете исправить ошибки и подать анкету заново через `/start`."
        )
    except Exception:
        pass

    await admin_msg.edit_text(admin_msg.text + f"\n\n❌ **ОТКЛОНЕНО**\n📌 Причина: {reason}")
    await message.reply("✅ Причина отправлена игроку.")
    await state.clear()

# ==================== ЗАПУСК ====================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
