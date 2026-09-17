import asyncio
import logging
import sys
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8996747968:AAGiV1p5kHoy-gQ2YDVknlmD2h3snSVe3sl"

SOCIAL_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/social.html"
COMPLAINTS_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/complaints.html"
REGISTER_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/register.html"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_profiles = {}

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Социальная сеть", web_app=WebAppInfo(url=SOCIAL_URL)),
                InlineKeyboardButton(text="🚨 Жалобы", web_app=WebAppInfo(url=COMPLAINTS_URL))
            ],
            [
                InlineKeyboardButton(text="📝 Регистрация персонажа", web_app=WebAppInfo(url=REGISTER_URL))
            ]
        ]
    )
    
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Добро пожаловать! Выберите нужное действие или откройте мини-приложение бланка персонажа:",
        reply_markup=keyboard
    )

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(
        "📖 **Справка по боту:**\n\n"
        "/start — Главное меню и мини-приложения\n"
        "/profile — Посмотреть сохраненную анкету\n"
        "/help — Помощь"
    )

@dp.message(Command("profile"))
async def command_profile_handler(message: Message) -> None:
    user_id = message.from_user.id
    if user_id not in user_profiles:
        await message.answer("У вас еще нет сохраненного персонажа! Откройте /start и заполните анкету в мини-приложении.")
        return
    
    p = user_profiles[user_id]
    text = (
        "👤 **Ваш персонаж:**\n\n"
        f"1. Имя: {p.get('name')}\n"
        f"2. Возраст: {p.get('age')}\n"
        f"3. Пол: {p.get('gender')}\n"
        f"4. Раса: {p.get('race')}\n"
        f"5. Внешность: {p.get('appearance')}\n"
        f"6. Характер: {p.get('character')}\n"
        f"7. Биография: {p.get('bio')}\n"
        f"8. Профессия: {p.get('job')}\n"
        f"9. Навыки: {p.get('skills')}\n"
        f"10. Слабости: {p.get('weaknesses')}\n"
        f"11. Цель: {p.get('goal')}\n"
        f"12. Дополнительно: {p.get('extra')}"
    )
    await message.answer(text)

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        user_profiles[message.from_user.id] = data
        await message.answer(
            "🎉 **Анкета персонажа успешно сохранена!**\n"
            "Вы можете в любой момент посмотреть её командой /profile."
        )
    except Exception as e:
        await message.answer("⚠️ Ошибка при обработке данных анкеты.")

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
    await asyncio.gather(web_server(), dp.start_polling(bot))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
