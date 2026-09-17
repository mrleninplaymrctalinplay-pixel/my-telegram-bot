import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Токен вашего бота от BotFather
BOT_TOKEN = "8996747968:AAHdVCmUIASZNhaUj-qp1m-JsRrqIq8udII"

# Ваша официальная ссылка на хостинге Render
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
        "• **GreeLand Gram** — делитесь фото, лайкайте и общайтесь.\n"
        "• **Суд и Жалобы** — подавайте репорты на нарушителей РП.\n\n"
        "Выбирайте нужный раздел ниже:"
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
