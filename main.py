import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Токен бота
TOKEN = os.getenv("TOKEN", "8996747968:AAGiV1p5kHoy-gQ2YDVknlmD2h3snSVe3sI")

SOCIAL_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/social.html"
COMPLAINTS_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/complaints.html"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Словарь для хранения анкет пользователей
user_profiles = {}

# Состояния для регистрации персонажа (12 пунктов)
class RegistrationStates(StatesGroup):
    step_1 = State()
    step_2 = State()
    step_3 = State()
    step_4 = State()
    step_5 = State()
    step_6 = State()
    step_7 = State()
    step_8 = State()
    step_9 = State()
    step_10 = State()
    step_11 = State()
    step_12 = State()

# Команда /start - главное меню
@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Социальная сеть", web_app=WebAppInfo(url=SOCIAL_URL)),
                InlineKeyboardButton(text="🚨 Жалобы и Поддержка", web_app=WebAppInfo(url=COMPLAINTS_URL))
            ],
            [
                InlineKeyboardButton(text="📝 Зарегистрировать персонажа", callback_data="start_reg")
            ]
        ]
    )
    
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Добро пожаловать! Выберите нужное действие или мини-приложение ниже:",
        reply_markup=keyboard
    )

# Команда /help
@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(
        "📖 **Справка по боту:**\n\n"
        "/start — Главное меню и мини-приложения\n"
        "/profile — Посмотреть анкету вашего персонажа\n"
        "/help — Помощь по командам"
    )

# Команда /profile — просмотр сохраненного персонажа
@dp.message(Command("profile"))
async def command_profile_handler(message: Message) -> None:
    user_id = message.from_user.id
    if user_id not in user_profiles:
        await message.answer("У вас еще нет зарегистрированного персонажа! Нажмите /start и выберите «Зарегистрировать персонажа».")
        return
    
    p = user_profiles[user_id]
    profile_text = (
        "👤 **Ваш персонаж:**\n\n"
        f"1. Имя: {p.get('p1')}\n"
        f"2. Возраст: {p.get('p2')}\n"
        f"3. Пол: {p.get('p3')}\n"
        f"4. Раса: {p.get('p4')}\n"
        f"5. Внешность: {p.get('p5')}\n"
        f"6. Характер: {p.get('p6')}\n"
        f"7. Биография: {p.get('p7')}\n"
        f"8. Профессия: {p.get('p8')}\n"
        f"9. Навыки: {p.get('p9')}\n"
        f"10. Слабости: {p.get('p10')}\n"
        f"11. Цель: {p.get('p11')}\n"
        f"12. Дополнительно: {p.get('p12')}"
    )
    await message.answer(profile_text)

# Запуск регистрации
@dp.callback_query(F.data == "start_reg")
async def start_registration(callback: Message, state: FSMContext):
    await callback.message.answer("📝 Начинаем создание персонажа (12 шагов).\n\n**Пункт 1/12:** Введите имя персонажа:")
    await state.set_state(RegistrationStates.step_1)
    await callback.answer()

# Шаги регистрации с 1 по 12
@dp.message(RegistrationStates.step_1)
async def reg_step_1(message: Message, state: FSMContext):
    await state.update_data(p1=message.text)
    await message.answer("**Пункт 2/12:** Введите возраст персонажа:")
    await state.set_state(RegistrationStates.step_2)

@dp.message(RegistrationStates.step_2)
async def reg_step_2(message: Message, state: FSMContext):
    await state.update_data(p2=message.text)
    await message.answer("**Пункт 3/12:** Укажите пол персонажа:")
    await state.set_state(RegistrationStates.step_3)

@dp.message(RegistrationStates.step_3)
async def reg_step_3(message: Message, state: FSMContext):
    await state.update_data(p3=message.text)
    await message.answer("**Пункт 4/12:** Укажите расу / национальность:")
    await state.set_state(RegistrationStates.step_4)

@dp.message(RegistrationStates.step_4)
async def reg_step_4(message: Message, state: FSMContext):
    await state.update_data(p4=message.text)
    await message.answer("**Пункт 5/12:** Опишите внешность персонажа:")
    await state.set_state(RegistrationStates.step_5)

@dp.message(RegistrationStates.step_5)
async def reg_step_5(message: Message, state: FSMContext):
    await state.update_data(p5=message.text)
    await message.answer("**Пункт 6/12:** Опишите характер (черты личности):")
    await state.set_state(RegistrationStates.step_6)

@dp.message(RegistrationStates.step_6)
async def reg_step_6(message: Message, state: FSMContext):
    await state.update_data(p6=message.text)
    await message.answer("**Пункт 7/12:** Краткая предыстория (биография):")
    await state.set_state(RegistrationStates.step_7)

@dp.message(RegistrationStates.step_7)
async def reg_step_7(message: Message, state: FSMContext):
    await state.update_data(p7=message.text)
    await message.answer("**Пункт 8/12:** Профессия или текущая деятельность:")
    await state.set_state(RegistrationStates.step_8)

@dp.message(RegistrationStates.step_8)
async def reg_step_8(message: Message, state: FSMContext):
    await state.update_data(p8=message.text)
    await message.answer("**Пункт 9/12:** Сильные стороны и навыки:")
    await state.set_state(RegistrationStates.step_9)

@dp.message(RegistrationStates.step_9)
async def reg_step_9(message: Message, state: FSMContext):
    await state.update_data(p9=message.text)
    await message.answer("**Пункт 10/12:** Слабости или фобии персонажа:")
    await state.set_state(RegistrationStates.step_10)

@dp.message(RegistrationStates.step_10)
async def reg_step_10(message: Message, state: FSMContext):
    await state.update_data(p10=message.text)
    await message.answer("**Пункт 11/12:** Главная цель или мечта персонажа:")
    await state.set_state(RegistrationStates.step_11)

@dp.message(RegistrationStates.step_11)
async def reg_step_11(message: Message, state: FSMContext):
    await state.update_data(p11=message.text)
    await message.answer("**Пункт 12/12:** Дополнительная информация / примечания:")
    await state.set_state(RegistrationStates.step_12)

@dp.message(RegistrationStates.step_12)
async def reg_step_12(message: Message, state: FSMContext):
    user_data = await state.get_data()
    user_data['p12'] = message.text  # сохраняем 12-й пункт
    
    # Сохраняем анкету в общую память по ID пользователя
    user_profiles[message.from_user.id] = user_data
    await state.clear()
    
    result_text = (
        "🎉 **Регистрация успешно завершена и сохранена!**\n"
        "Теперь вы можете посмотреть её в любой момент командой /profile\n\n"
        f"1. Имя: {user_data.get('p1')}\n"
        f"2. Возраст: {user_data.get('p2')}\n"
        f"3. Пол: {user_data.get('p3')}\n"
        f"4. Раса: {user_data.get('p4')}\n"
        f"5. Внешность: {user_data.get('p5')}\n"
        f"6. Характер: {user_data.get('p6')}\n"
        f"7. Биография: {user_data.get('p7')}\n"
        f"8. Профессия: {user_data.get('p8')}\n"
        f"9. Навыки: {user_data.get('p9')}\n"
        f"10. Слабости: {user_data.get('p10')}\n"
        f"11. Цель: {user_data.get('p11')}\n"
        f"12. Дополнительно: {user_data.get('p12')}"
    )
    await message.answer(result_text)

# Веб-сервер для Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main() -> None:
    await asyncio.gather(
        web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
