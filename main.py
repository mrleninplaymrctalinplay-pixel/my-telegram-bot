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
BOT_TOKEN = "8996747968:AAGEbSeyRMDEzS-dbkVRIev28Yk8-RJNZOA"
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
        CREATE TABLE IF NOT EXISTS passport_apps (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            birth_data TEXT,
            nationality TEXT,
            birth_place_params TEXT,
            marks TEXT,
            character_trait TEXT,
            marital_status TEXT,
            residence TEXT,
            blood_type TEXT,
            diseases TEXT,
            photo_id TEXT,
            signature TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def save_application(data: dict):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO passport_apps 
        (user_id, username, full_name, birth_data, nationality, birth_place_params, marks, character_trait, marital_status, residence, blood_type, diseases, photo_id, signature, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        data['user_id'],
        data['username'],
        data['full_name'],
        data['birth_data'],
        data['nationality'],
        data['birth_place_params'],
        data['marks'],
        data['character_trait'],
        data['marital_status'],
        data['residence'],
        data['blood_type'],
        data['diseases'],
        data['photo_id'],
        data['signature']
    ))
    conn.commit()
    conn.close()

def update_status(user_id: int, status: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE passport_apps SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

def get_application(user_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM passport_apps WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# ---------------- FSM Состояния ----------------
class PassportForm(StatesGroup):
    full_name = State()
    birth_data = State()
    nationality = State()
    birth_place_params = State()
    marks = State()
    character_trait = State()
    marital_status = State()
    residence = State()
    blood_type = State()
    diseases = State()
    photo_id = State()
    signature = State()

# ---------------- Хэндлеры ----------------
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    row = get_application(message.from_user.id)
    if row:
        status = row[0]
        if status == 'approved':
            await message.answer("✅ Ваш канадский паспорт уже оформлен!")
            return
        elif status == 'pending':
            await message.answer("⏳ Ваша заявка на паспорт находится на рассмотрении МФЦ.")
            return

    await state.clear()
    await message.answer("🇨🇦 <b>Заявление на получение канадского паспорта (МФЦ)</b>\n\nШаг 1/12: Введите Ф.И.О вашего РП-персонажа:", parse_mode="HTML")
    await state.set_state(PassportForm.full_name)

@router.message(PassportForm.full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Шаг 2/12: Укажите дату рождения в формате «ДД-ММ-ГГ» и пол персонажа:")
    await state.set_state(PassportForm.birth_data)

@router.message(PassportForm.birth_data)
async def process_birth_data(message: Message, state: FSMContext):
    await state.update_data(birth_data=message.text)
    await message.answer("Шаг 3/12: Укажите национальность и происхождение персонажа:")
    await state.set_state(PassportForm.nationality)

@router.message(PassportForm.nationality)
async def process_nationality(message: Message, state: FSMContext):
    await state.update_data(nationality=message.text)
    await message.answer("Шаг 4/12: Укажите место рождения (город/страна), а также рост, вес и цвет глаз:")
    await state.set_state(PassportForm.birth_place_params)

@router.message(PassportForm.birth_place_params)
async def process_birth_place_params(message: Message, state: FSMContext):
    await state.update_data(birth_place_params=message.text)
    await message.answer("Шаг 5/12: Особые приметы (татуировки, шрамы, дефекты речи, если есть):")
    await state.set_state(PassportForm.marks)

@router.message(PassportForm.marks)
async def process_marks(message: Message, state: FSMContext):
    await state.update_data(marks=message.text)
    await message.answer("Шаг 6/12: Краткий характер персонажа (спокойный, агрессивный, хитрый и т.д.):")
    await state.set_state(PassportForm.character_trait)

@router.message(PassportForm.character_trait)
async def process_character_trait(message: Message, state: FSMContext):
    await state.update_data(character_trait=message.text)
    await message.answer("Шаг 7/12: Семейное положение («Холост» / «Замужем» / «В браке с...»):")
    await state.set_state(PassportForm.marital_status)

@router.message(PassportForm.marital_status)
async def process_marital_status(message: Message, state: FSMContext):
    await state.update_data(marital_status=message.text)
    await message.answer("Шаг 8/12: Текущее место проживания в городе (если пока нет дома, пишите: Отель):")
    await state.set_state(PassportForm.residence)

@router.message(PassportForm.residence)
async def process_residence(message: Message, state: FSMContext):
    await state.update_data(residence=message.text)
    await message.answer("Шаг 9/12: Группа крови и резус-фактор вашего персонажа:")
    await state.set_state(PassportForm.blood_type)

@router.message(PassportForm.blood_type)
async def process_blood_type(message: Message, state: FSMContext):
    await state.update_data(blood_type=message.text)
    await message.answer("Шаг 10/12: Наличие хронических заболеваний или аллергий (для медиков):")
    await state.set_state(PassportForm.diseases)

@router.message(PassportForm.diseases)
async def process_diseases(message: Message, state: FSMContext):
    await state.update_data(diseases=message.text)
    await message.answer("Шаг 11/12: Отправьте фото персонажа на белом фоне (крупным планом, без масок):")
    await state.set_state(PassportForm.photo_id)

@router.message(PassportForm.photo_id, F.photo)
async def process_photo_id(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_file_id)
    await message.answer("Шаг 12/12: Четкое фото подписи или напишите подпись текстом в кавычках:")
    await state.set_state(PassportForm.signature)

@router.message(PassportForm.photo_id)
async def process_photo_id_invalid(message: Message):
    await message.answer("⚠️ Пожалуйста, отправьте именно фотографию персонажа!")

@router.message(PassportForm.signature)
async def process_signature(message: Message, state: FSMContext):
    if message.photo:
        sig_val = f"PHOTO:{message.photo[-1].file_id}"
    else:
        sig_val = message.text

    await state.update_data(signature=sig_val)
    user_data = await state.get_data()
    
    user_data['user_id'] = message.from_user.id
    user_data['username'] = message.from_user.username or "Отсутствует"

    save_application(user_data)
    await state.clear()

    await message.answer("📋 Ваша заявка на оформление паспорта отправлена в МФЦ!")

    card_text = (
        f"🇨🇦 <b>Заявление на Канадский Паспорт</b>\n\n"
        f"👤 <b>Игрок:</b> @{user_data['username']} (ID: <code>{user_data['user_id']}</code>)\n"
        f"🏷 <b>Ф.И.О:</b> {user_data['full_name']}\n"
        f"🎂 <b>Дата рождения и пол:</b> {user_data['birth_data']}\n"
        f"🌍 <b>Национальность:</b> {user_data['nationality']}\n"
        f"📍 <b>Место рождения/рост/вес/глаза:</b> {user_data['birth_place_params']}\n"
        f"🔍 <b>Особые приметы:</b> {user_data['marks']}\n"
        f"🧠 <b>Характер:</b> {user_data['character_trait']}\n"
        f"💍 <b>Семейное положение:</b> {user_data['marital_status']}\n"
        f"🏠 <b>Проживание:</b> {user_data['residence']}\n"
        f"🩸 <b>Группа крови:</b> {user_data['blood_type']}\n"
        f"🏥 <b>Заболевания/Аллергии:</b> {user_data['diseases']}\n"
    )

    if not sig_val.startswith("PHOTO:"):
        card_text += f"✍️ <b>Подпись:</b> {sig_val}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить паспорт", callback_data=f"approve_{user_data['user_id']}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_data['user_id']}")
        ]
    ])

    # Отправляем карточку с главным фото
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=user_data['photo_id'],
        caption=card_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

    # Если подпись прислали картинкой — отправляем следом
    if sig_val.startswith("PHOTO:"):
        photo_sig_id = sig_val.replace("PHOTO:", "")
        await bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo_sig_id,
            caption=f"✍️ Подпись персонажа @{user_data['username']}"
        )

@router.callback_query(F.data.startswith("approve_"))
async def approve_character(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    update_status(user_id, "approved")
    
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n🟢 <b>ОДОБРЕНО</b> сотрудником МФЦ @{callback.from_user.username or callback.from_user.first_name}",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(user_id, "🎉 Ваш канадский паспорт успешно оформлен МФЦ!")
    except Exception:
        pass
        
    await callback.answer("Заявка одобрена")

@router.callback_query(F.data.startswith("reject_"))
async def reject_character(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    update_status(user_id, "rejected")
    
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n🔴 <b>ОТКЛОНЕНО</b> сотрудником МФЦ @{callback.from_user.username or callback.from_user.first_name}",
        parse_mode="HTML"
    )
    
    try:
        await bot.send_message(user_id, "❌ Ваша заявка на оформление паспорта была отклонена МФЦ.")
    except Exception:
        pass
        
    await callback.answer("Заявка отклонена")

# ---------------- Запуск ----------------
async def main():
    init_db()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

