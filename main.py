import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Токен вашего бота от BotFather
BOT_TOKEN = "8996747968:AAGiV1p5kHoy-gQ2YDVknlmD2h3snSVe3sI"

# Ваша рабочая ссылка на хостинге Render
WEB_APP_URL = "https://my-telegram-bot-cwph.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 GreeLand Gram (Инста)", 
                web_app=WebAppInfo(url=f"{WEB_APP_URL}/social.html")
            )
        ],
        [
            InlineKeyboardButton(
                text="🚨 Суд и Жалобы", 
                web_app=WebAppInfo(url=f"{WEB_APP_URL}/complaints.html")
            )
        ],
        [
            InlineKeyboardButton(text="🌐 Зайти в Brookhaven 24/7", url="https://www.roblox.com/games/4924922222/Brookhaven-RP")
        ]
    ])
    
    text = (
        "🌴 **Добро пожаловать в официальный хаб Brookhaven 24/7!**\n\n"
        "• **GreeLand Gram** — делитесь фото, лайкайте и общайтесь в РП-соцсети.\n"
        "• **Суд и Жалобы** — подавайте и рассматривайте репорты на нарушителей.\n\n"
        "Выберите нужное мини-приложение ниже:"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(Command("server"))
async def cmd_server(message: types.Message):
    await message.answer("🟢 **Статус серверов:** Работают стабильно (24/7) 🚀")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
