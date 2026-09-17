import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8996747968:AAHdVCmUIASZNhaUj-qp1m-JsRrqIq8udII"
ADMIN_CHAT_ID = 644112527

logging.basicConfig(level=logging.INFO)

# ==================== БАЗА ДАННЫХ ====================
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    fio TEXT,
    gender TEXT,
    birth_date TEXT,
    citizenship TEXT,
    fraction TEXT,
    bio TEXT,
    social_status TEXT,
    photo TEXT,
    signature TEXT,
    document_type TEXT,
    issue_reason TEXT,
    delivery_type TEXT,
    status TEXT
)
""")
conn.commit()

# ==================== СОСТОЯНИЯ (12 шагов) ====================
class Registration(StatesGroup):
    step1_fio = State()
    step2_gender = State()
    step3_birth_date = State()
    step4_citizenship = State()
    step5_fraction = State()
    step6_bio = State()
    step7_social_status = State()
    step8_photo = State()
    step9_signature = State()
    step10_doc_type = State()
    step11_issue_reason = State()
    step12_delivery_type = State()

router = Router()

# ==================== СПРАВКА И КОМАНДЫ ====================

HELP_TEXT = (
    "📖 **Список доступных команд:**\n\n"
    "• `/start` — Запустить бота и открыть главное меню\n"
    "• `/help` — Показать эту справку по командам\n"
    "• `/profile` — Посмотреть карточку своего РП-персонажа\n"
    "• `/delete` или `/reset` — Удалить персонажа и сбросить анкету"
)

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT)

@router.callback_query(F.data == "show_help")
async def process_show_help(callback: CallbackQuery):
    await callback.message.answer(HELP_TEXT)

# ==================== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ====================

async def get_profile_data(user_id: int):
    cursor.execute("""
    SELECT fio, gender, birth_date, citizenship, fraction, bio, 
           social_status, photo, signature, document_type, issue_reason, delivery_type, status 
    FROM users WHERE user_id = ?
    """, (user_id,))
    return cursor.fetchone()

@router.message(Command("profile"))
@router.callback_query(F.data == "show_profile")
async def show_profile_handler(event: Message | CallbackQuery):
    user_id = event.from_user.id
    user = await get_profile_data(user_id)

    if not user:
        text = "❌ У вас пока нет созданного персонажа. Нажмите /start, чтобы зарегистрироваться."
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🚀 Начать регистрацию", callback_data="start_registration")
        ]])
    else:
        status_map = {"approved": "✅ Одобрена", "pending": "⏳ На проверке", "rejected": "❌ Отклонена"}
        status_str = status_map.get(user[12], "Неизвестно")

        text = (
            f"👤 **Карточка РП-персонажа** (Статус: {status_str})\n\n"
            f"1. **ФИО:** {user[0]}\n"
            f"2. **Пол:** {user[1]}\n"
            f"3. **Дата рождения:** {user[2]}\n"
            f"4. **Гражданство:** {user[3]}\n"
            f"5. **Фракция:** {user[4]}\n"
            f"6. **Биография:** {user[5]}\n"
            f"7. **Социальный статус:** {user[6]}\n"
            f"8. **Фото/Внешность:** {user[7]}\n"
            f"9. **Личная подпись:** {user[8]}\n"
            f"10. **Тип документа:** {user[9]}\n"
            f"11. **Причина выдачи:** {user[10]}\n"
            f"12. **Способ получения:** {user[11]}"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить персонажа", callback_data="user_delete_self")],
            [InlineKeyboardButton(text="◀️ В главное меню", callback_data="go_main_menu")]
        ])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)

# ==================== ОБРАБОТЧИКИ СБРОСА И УДАЛЕНИЯ ====================

@router.message(Command("delete"))
@router.message(Command("reset"))
async def cmd_delete_character(message: Message, state: FSMContext):
    await state.clear()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (message.from_user.id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚀 Начать регистрацию", callback_data="start_registration")
    ]])
    await message.answer(
        "🗑 Ваш РП-персонаж был успешно удалён!\n\nВы можете зарегистрировать нового персонажа с чистого листа.",
        reply_markup=kb
    )

@router.callback_query(F.data == "user_delete_self")
async def process_user_delete_self(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (callback.from_user.id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚀 Начать регистрацию", callback_data="start_registration")
    ]])
    await callback.message.edit_text(
        "🗑 Ваш РП-персонаж успешно удалён.\n\nВы можете начать регистрацию заново:",
        reply_markup=kb
    )

# ==================== СТАРТ И АНКЕТА ====================

@router.message(CommandStart())
@router.callback_query(F.data == "go_main_menu")
async def cmd_start(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    cursor.execute("SELECT fio, status FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        fio, status = user
        if status == "approved":
            text = f"✅ У вас уже есть одобренный персонаж: **{fio}**."
        else:
            text = f"⏳ Ваша анкета персонажа **{fio}** находится на рассмотрении."

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Профиль (Моя анкета)", callback_data="show_profile")],
            [InlineKeyboardButton(text="ℹ️ Помощь / Команды", callback_data="show_help")],
            [InlineKeyboardButton(text="🗑 Удалить персонажа", callback_data="user_delete_self")]
        ])
    else:
        text = (
            "👋 Добро пожаловать в бота регистрации канадского паспорта!\n\n"
            f"{HELP_TEXT}\n\n"
            "Нажмите кнопку **«🚀 Начать регистрацию»** ниже, чтобы перейти к заполнению анкеты из 12 шагов:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Начать регистрацию", callback_data="start_registration")],
            [InlineKeyboardButton(text="ℹ️ Помощь / Команды", callback_data="show_help")]
        ])

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)

@router.callback_query(F.data == "start_registration")
async def start_registration_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.step1_fio)
    await callback.message.answer("📋 Начинаем регистрацию канадского паспорта.\n\n**Шаг 1/12:** Введите Ф.И.О вашего РП-персонажа:")

@router.message(Registration.step1_fio)
async def process_step1(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(Registration.step2_gender)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мужской", callback_data="gender_m")],
        [InlineKeyboardButton(text="Женский", callback_data="gender_f")]
    ])
    await message.answer("**Шаг 2/12:** Выберите пол персонажа:", reply_markup=kb)

@router.callback_query(Registration.step2_gender)
async def process_step2(callback: CallbackQuery, state: FSMContext):
    gender = "Мужской" if callback.data == "gender_m" else "Женский"
    await state.update_data(gender=gender)
    await callback.message.edit_text(f"Пол: {gender}")
    
    await state.set_state(Registration.step3_birth_date)
    await callback.message.answer("**Шаг 3/12:** Укажите дату рождения (например, 15.05.1995):")

@router.message(Registration.step3_birth_date)
async def process_step3(message: Message, state: FSMContext):
    await state.update_data(birth_date=message.text)
    await state.set_state(Registration.step4_citizenship)
    await message.answer("**Шаг 4/12:** Укажите гражданство:")

@router.message(Registration.step4_citizenship)
async def process_step4(message: Message, state: FSMContext):
    await state.update_data(citizenship=message.text)
    await state.set_state(Registration.step5_fraction)
    await message.answer("**Шаг 5/12:** Укажите фракцию/группировку:")

@router.message(Registration.step5_fraction)
async def process_step5(message: Message, state: FSMContext):
    await state.update_data(fraction=message.text)
    await state.set_state(Registration.step6_bio)
    await message.answer("**Шаг 6/12:** Напишите краткую биографию персонажа:")

@router.message(Registration.step6_bio)
async def process_step6(message: Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await state.set_state(Registration.step7_social_status)
    await message.answer("**Шаг 7/12:** Укажите социальный статус:")

@router.message(Registration.step7_social_status)
async def process_step7(message: Message, state: FSMContext):
    await state.update_data(social_status=message.text)
    await state.set_state(Registration.step8_photo)
    await message.answer("**Шаг 8/12:** Отправьте ссылку на фото персонажа или опишите его внешность:")

@router.message(Registration.step8_photo)
async def process_step8(message: Message, state: FSMContext):
    await state.update_data(photo=message.text)
    await state.set_state(Registration.step9_signature)
    await message.answer("**Шаг 9/12:** Введите личную подпись персонажа:")

@router.message(Registration.step9_signature)
async def process_step9(message: Message, state: FSMContext):
    await state.update_data(signature=message.text)
    await state.set_state(Registration.step10_doc_type)
    await message.answer("**Шаг 10/12:** Укажите тип документа (например, Паспорт Канады):")

@router.message(Registration.step10_doc_type)
async def process_step10(message: Message, state: FSMContext):
    await state.update_data(doc_type=message.text)
    await state.set_state(Registration.step11_issue_reason)
    await message.answer("**Шаг 11/12:** Укажите причину выдачи (Первичное получение / Замена):")

@router.message(Registration.step11_issue_reason)
async def process_step11(message: Message, state: FSMContext):
    await state.update_data(issue_reason=message.text)
    await state.set_state(Registration.step12_delivery_type)
    await message.answer("**Шаг 12/12:** Укажите способ получения (Лично в МФЦ / Почта):")

@router.message(Registration.step12_delivery_type)
async def process_step12(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(delivery_type=message.text)
    data = await state.get_data()
    
    user_id = message.from_user.id
    username = message.from_user.username or "нет"

    cursor.execute("""
    INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, username, data["fio"], data["gender"], data["birth_date"],
        data["citizenship"], data["fraction"], data["bio"], data["social_status"],
        data["photo"], data["signature"], data["doc_type"], data["issue_reason"],
        data["delivery_type"], "pending"
    ))
    conn.commit()

    admin_text = (
        f"📋 **Новая анкета (12/12):**\n"
        f"👤 От: @{username} (ID: {user_id})\n\n"
        f"1. ФИО: {data['fio']}\n"
        f"2. Пол: {data['gender']}\n"
        f"3. Дата рождения: {data['birth_date']}\n"
        f"4. Гражданство: {data['citizenship']}\n"
        f"5. Фракция: {data['fraction']}\n"
        f"6. Биография: {data['bio']}\n"
        f"7. Соц. статус: {data['social_status']}\n"
        f"8. Фото: {data['photo']}\n"
        f"9. Подпись: {data['signature']}\n"
        f"10. Тип документа: {data['doc_type']}\n"
        f"11. Причина: {data['issue_reason']}\n"
        f"12. Доставка: {data['delivery_type']}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")
    ]])

    await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_markup=kb)
    await message.answer("📋 Ваша анкета (12 шагов) отправлена на проверку администраторам!")
    await state.clear()

# ==================== ДЕЙСТВИЯ АДМИНИСТРАТОРА ====================

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (target_id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🗑 Удалить карту", callback_data=f"admin_delete_{target_id}")
    ]])

    await bot.send_message(target_id, "🎉 Ваша анкета персонажа успешно одобрена администрацией!")
    await callback.message.edit_text(callback.message.text + "\n\n✅ **ОДОБРЕНО**", reply_markup=kb)

@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status = 'rejected' WHERE user_id = ?", (target_id,))
    conn.commit()
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🗑 Удалить из базы", callback_data=f"admin_delete_{target_id}")
    ]])

    await bot.send_message(target_id, "❌ Ваша анкета была отклонена администрацией.")
    await callback.message.edit_text(callback.message.text + "\n\n❌ **ОТКЛОНЕНО**", reply_markup=kb)

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[2])
    cursor.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
    conn.commit()

    await bot.send_message(target_id, "ℹ️ Ваш персонаж был удалён администратором. Вы можете создать нового через /start.")
    await callback.message.edit_text(callback.message.text + "\n\n🗑 **ПЕРСОНАЖ УДАЛЕН АДМИНИСТРАТОРОМ**")

# ==================== ЗАПУСК ====================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
