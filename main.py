import logging
from aiogram import Bot, Dispatcher, executor, types

# Токен вашего бота
API_TOKEN = "8996747968:AAGiV1p5kHoy-gQ2YDVknlmD2h3snSVe3sI"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Приветственное сообщение при старте бота в личке
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Бот GreeLand успешно запущен и готов к работе.")

# Обработка нажатия кнопок «Одобрить» / «Отклонить» под анкрой в группе
@dp.callback_query_handler(lambda c: c.data in ["app_approve", "app_reject"])
async def process_app_buttons(callback_query: types.CallbackQuery):
    message = callback_query.message
    admin_name = callback_query.from_user.full_name
    
    if callback_query.data == "app_approve":
        new_text = message.text + f"\n\n🟢 <b>СТАТУС: ОДОБРЕНО</b>\n👤 Проверил: {admin_name}"
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=new_text,
            parse_mode="HTML"
        )
        await bot.answer_callback_query(callback_query.id, "Анкета успешно одобрена!")
        
    elif callback_query.data == "app_reject":
        new_text = message.text + f"\n\n🔴 <b>СТАТУС: ОТКЛОНЕНО</b>\n👤 Проверил: {admin_name}"
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=new_text,
            parse_mode="HTML"
        )
        await bot.answer_callback_query(callback_query.id, "Анкета отклонена.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
