import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart

# Токен берется из переменных окружения Render или вставьте сюда строкой
TOKEN = os.getenv("TOKEN", "8996747968:AAGiV1p5kHoy-gQ2YDVknlmD2h3snSVe3sI")

SOCIAL_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/social.html"
COMPLAINTS_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/complaints.html"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Социальная сеть",
                    web_app=WebAppInfo(url=SOCIAL_URL)
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚨 Жалобы и Поддержка",
                    web_app=WebAppInfo(url=COMPLAINTS_URL)
                )
            ]
        ]
    )
    
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\n"
        "Добро пожаловать! Выберите нужное мини-приложение ниже:",
        reply_markup=keyboard
    )

# Простейший веб-сервер для Render, чтобы он не ругался на порты
async def handle(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render передает порт через переменные окружения, по умолчанию ставим 10000
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main() -> None:
    # Запускаем и веб-сервер (для Render), и самого бота (polling) одновременно
    await asyncio.gather(
        web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
