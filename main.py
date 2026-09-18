import os
import random
import logging
import requests
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ВАШ_ТОКЕН_БОТА")
ADMIN_GROUP_ID = int(os.environ.get("ADMIN_GROUP_ID", "-100XXXXXXXXXX"))

app_bot = Flask(__name__)

# Хранилища для ожидания причины отклонения: {admin_id: target_user_id}
PENDING_REJECT_PASSPORT = {}
PENDING_REJECT_COMPLAINT = {}

@app_bot.route('/api/submit', methods=['POST'])
def handle_miniapp_submit():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    form_type = data.get('type')
    user_id = data.get('user_id')
    content = data.get('content')

    if form_type == 'passport':
        keyboard = [
            [
                InlineKeyboardButton("✅ Одобрить", callback_data=f"pass_app_{user_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"pass_rej_{user_id}")
            ]
        ]
        text_to_admin = f"📋 **Новая заявка на паспорт / персонажа:**\n\n{content}"

    elif form_type == 'complaint':
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять / Одобрить", callback_data=f"comp_app_{user_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"comp_rej_{user_id}")
            ]
        ]
        text_to_admin = f"⚖️ **Новое обращение с форума (Жалобы):**\n\n{content}"
    else:
        return jsonify({"status": "error", "message": "Unknown type"}), 400

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_GROUP_ID,
        "text": text_to_admin,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Telegram API error"}), 500


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    admin_id = query.from_user.id

    # 1. Паспорта
    if data.startswith("pass_app_"):
        target_user_id = int(data.split("_")[2])
        static_id = random.randint(1000, 9999)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ **Ваш паспорт и регистрация персонажа одобрены!**\n\n"
                     f"🪪 **Ваш игровой Static ID:** `{static_id}`\n"
                     f"🟢 Добро пожаловать в штат GreeLand RP!",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки игроку: {e}")

        await query.edit_message_text(
            text=f"{query.message.text}\n\n<b>[СТАТУС: ОДОБРЕНО]</b> Выдан Static ID: <code>{static_id}</code>",
            parse_mode="HTML"
        )

    elif data.startswith("pass_rej_"):
        target_user_id = int(data.split("_")[2])
        PENDING_REJECT_PASSPORT[admin_id] = target_user_id
        await query.message.reply_text("✍️ Введите причину отклонения паспорта следующим сообщением:")

    # 2. Жалобы и форум
    elif data.startswith("comp_app_"):
        target_user_id = int(data.split("_")[2])
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="✅ Ваша жалоба / обращение на форуме была рассмотрена и **одобрена администрацией**!",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки игроку: {e}")

        await query.edit_message_text(
            text=f"{query.message.text}\n\n<b>[СТАТУС: ОДОБРЕНО / ПРИНЯТО]</b>",
            parse_mode="HTML"
        )

    elif data.startswith("comp_rej_"):
        target_user_id = int(data.split("_")[2])
        PENDING_REJECT_COMPLAINT[admin_id] = target_user_id
        await query.message.reply_text("✍️ Введите причину отклонения жалобы / темы следующим сообщением:")


async def admin_text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    text = update.message.text

    if admin_id in PENDING_REJECT_PASSPORT:
        target_user_id = PENDING_REJECT_PASSPORT.pop(admin_id)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ **Ваша заявка на регистрацию персонажа была отклонена.**\n\n📌 **Причина:** {text}",
                parse_mode="Markdown"
            )
            await update.message.reply_text("✅ Уведомление об отклонении паспорта отправлено.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка: {e}")

    elif admin_id in PENDING_REJECT_COMPLAINT:
        target_user_id = PENDING_REJECT_COMPLAINT.pop(admin_id)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ **Ваша тема / жалоба на форуме была отклонена.**\n\n📌 **Причина:** {text}",
                parse_mode="Markdown"
            )
            await update.message.reply_text("✅ Уведомление об отклонении жалобы отправлено.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка: {e}")


def main():
    if TELEGRAM_TOKEN == "ВАШ_ТОКЕН_БОТА":
        logger.error("Укажите правильный TELEGRAM_TOKEN!")
        return

    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    telegram_app.add_handler(CallbackQueryHandler(button_callback_handler))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_message_handler))

    port = int(os.environ.get("PORT", 5000))
    
    import threading
    def run_flask():
        app_bot.run(host="0.0.0.0", port=port)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    logger.info("Бот и сервер запущены!")
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
