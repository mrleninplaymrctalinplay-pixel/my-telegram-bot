import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.filters import CommandStart

# Вставьте сюда токен вашего бота от BotFather
TOKEN = "8996747968:AAGiV1p5kHoy-gQ2YDVknlmD2h3snSVe3sI"

# Ссылки на ваши мини-приложения на GitHub Pages
SOCIAL_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/social.html"
COMPLAINTS_URL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/complaints.html"

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Создаем клавиатуру с кнопками для Mini Apps
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

async def main() -> None:
    # Запуск опроса серверов Telegram (Polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
