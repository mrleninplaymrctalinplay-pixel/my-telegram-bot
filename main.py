import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8996747968:AAGEBSeyRMDEzS-dbkVRIev28Yk8-RJNZOA"
ADMIN_CHAT_ID = -1003913257980
# ====================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# ---------------- База данных SQLite ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            callsign TEXT,
            age TEXT,
            gender TEXT,
            fraction TEXT,
            biography TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def save_character(data: dict):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO characters 
        (user_id, username, full_name, callsign, age, gender, fraction, biography, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        data['user_id'],
        data['username'],
        data['full_name'],
        data['callsign'],
        data['age'],
        data['gender'],
        data['fraction'],
        data['biography']
    ))
    conn.commit()
    conn.close()

def update_status(user_id: int, status: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE characters SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

def get_character(user_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, callsign, age, gender, fraction, biography, status FROM characters WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# ---------------- FSM Состояния ----------------
class Registration(StatesGroup):
    full_name = State()
    callsign = State()
    age = State()
    gender = State()
    fraction = State()
    biography = State()

# ---------------- Хэндлеры ----------------
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    row = get_character(message.from_user.id)
    if row:
        status = row[6]
        if status == 'approved':
            await message.answer("✅ Ваша анкета уже одобрена!")
            return
        elif status == 'pending':
            await message.answer("⏳ Ваша анкета находится на рассмотрении администрации.")
            return

    await state.clear()
    await message.answer("Привет! Начинаем регистрацию персонажа.\n\nШаг 1/6: Введите ФИО вашего персонажа:")
    await state.set_state(Registration.full_name)

@router.message(Registration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Шаг 2/6: Введите позывной персонажа:")
    await state.set_state(Registration.callsign)

@router.message(Registration.callsign)
async def process_callsign(message: Message, state: FSMContext):
    await state.update_data(callsign=message.text)
    await message.answer("Шаг 3/6: Укажите возраст персонажа:")
    await state.set_state(Registration.age)

@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Шаг 4/6: Укажите пол персонажа:")
    await state.set_state(Registration.gender)

@router.message(Registration.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Шаг 5/6: Укажите фракцию/группировку:")
    await state.set_state(Registration.fraction)

@router.message(Registration.fraction)
async def process_fraction(message: Message, state: FSMContext):
    await state.update_data(fraction=message.text)
    await message.answer("Шаг 6/6: Напишите краткую биографию персонажа:")
    await state.set_state(Registration.biography)

@router.message(Registration.biography)
async def process_biography(message: Message, state: FSMContext):
    await state.update_data(biography=message.text)
    user_data = await state.get_data()
    
    user_data['user_id'] = message.from_user.id
    user_data['username'] = message.from_user.username or "Отсутствует"

    save_character(user_data)
    await state.clear()

    await message.answer("📋 Ваша анкета отправлена на проверку администраторам!")

    card_text = (
        f"📝 <b>Новая анкета персонажа!</b>\n\n"
        f"👤 <b>Игрок:</b> @{user_data['username']} (ID: <code>{user_data['user_id']}</code>)\n"
        f"🏷 <b>ФИО:</b> {user_data['full_name']}\n"
        f"🎙 <b>Позывной:</b> {user_data['callsign']}\n"
        f"🎂 <b>Возраст:</b> {user_data['age']}\n"
        f"⚧ <b>Пол:</b> {user_data['gender']}\n"
        f"🏴 <b>Фракция:</b> {user_data['fraction']}\n\n"
        f"📖 <b>Биография:</b>\n{user_data['biography']}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_data['user_id']}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_data['user_id']}")
        ]
    ])

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=card_text, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data.startswith("approve_"))
async def approve_character(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    update_status(user_id, "approved")
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n🟢 <b>ОДОБРЕНО</b> администратором @{callback.from_user.username or callback.from_user.first_name}",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(user_id, "🎉 Ваша анкета персонажа успешно одобрена администрацией!")
    except Exception:
        pass
        
    await callback.answer("Анкета одобрена")

@router.callback_query(F.data.startswith("reject_"))
async def reject_character(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    update_status(user_id, "rejected")
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n🔴 <b>ОТКЛОНЕНО</b> администратором @{callback.from_user.username or callback.from_user.first_name}",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(user_id, "❌ Ваша анкета персонажа была отклонена администрацией.")
    except Exception:
        pass
        
    await callback.answer("Анкета отклонена")

# ---------------- Запуск ----------------
async def main():
    init_db()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

