import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# Токен вашего бота
API_TOKEN = "8996747968:AAGt-wgqjd2Ao8stQezE_-othXKG3SC3Z54"

# Ссылки на ваши мини-приложения через GitHub Pages
URL_REGISTER = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/register.html"
URL_REPORT = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/complaints.html"
URL_SOCIAL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/social.html"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# 1. Команда /start с выбором языка
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    lang_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
            ]
        ]
    )
    
    await message.answer(
        "🌍 <b>Добро пожаловать в GreeLand RP!</b>\nВыберите ваш язык / Choose your language:",
        parse_mode="HTML",
        reply_markup=lang_keyboard
    )

# Обработка выбора языка и вывод главного меню со всеми тремя Mini Apps
@dp.callback_query(lambda c: c.data in ["lang_ru", "lang_en"])
async def process_language(callback_query: types.CallbackQuery):
    is_ru = callback_query.data == "lang_ru"
    
    if is_ru:
        text = "🌲 <b>Главное меню GreeLand RP</b>\nВыберите нужный раздел ниже:"
        btn_reg = "📝 Регистрация персонажа"
        btn_rep = "⚠️ Подать жалобу"
        btn_soc = "📸 Социальная сеть"
    else:
        text = "🌲 <b>GreeLand RP Main Menu</b>\nChoose a section below:"
        btn_reg = "📝 Character Registration"
        btn_rep = "⚠️ Report / Support"
        btn_soc = "📸 Social Network"
    
    menu_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_reg, web_app=WebAppInfo(url=URL_REGISTER))],
            [InlineKeyboardButton(text=btn_rep, web_app=WebAppInfo(url=URL_REPORT))],
            [InlineKeyboardButton(text=btn_soc, web_app=WebAppInfo(url=URL_SOCIAL))]
        ]
    )
    
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=menu_keyboard)
    await callback_query.answer()

# 2. Обработка кнопок «Одобрить» / «Отклонить» в группе администраторов
@dp.callback_query(lambda c: c.data in ["app_approve", "app_reject"])
async def process_app_buttons(callback_query: types.CallbackQuery):
    message = callback_query.message
    admin_name = callback_query.from_user.full_name
    
    if callback_query.data == "app_approve":
        new_text = message.text + f"\n\n🟢 <b>СТАТУС: ОДОБРЕНО</b>\n👤 Проверил: {admin_name}"
        status_msg = "🎉 <b>Поздравляем! Ваша анкета персонажа в GreeLand RP одобрена администрацией.</b> Добро пожаловать в игру!"
        answer_text = "Анкета успешно одобрена!"
    else:
        new_text = message.text + f"\n\n🔴 <b>СТАТУС: ОТКЛОНЕНО</b>\n👤 Проверил: {admin_name}"
        status_msg = "❌ <b>К сожалению, ваша анкета в GreeLand RP была отклонена.</b> Вы можете подать исправленную анкету заново через меню бота."
        answer_text = "Анкета отклонена."

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message.message_id,
        text=new_text,
        parse_mode="HTML"
    )
    
    try:
        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
            await bot.send_message(target_user_id, status_msg, parse_mode="HTML")
    except Exception as e:
        logging.info(f"Не удалось отправить личное сообщение игроку: {e}")

    await callback_query.answer(answer_text)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
