import os
import random
import logging
import json
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8996747968:AAGt-wgqjd2Ao8stQezE_-othXKG3SC3Z54"
ADMIN_GROUP_ID = -1003913257980

app_bot = Flask(__name__)

PENDING_REJECT_PASSPORT = {}
PENDING_REJECT_COMPLAINT = {}

# --- КОМАНДЫ ПОЛЬЗОВАТЕЛЕЙ ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Привет, {user_name}! 👋\n\n"
        f"Добро пожаловать в официальный бот проекта <b>GreeLand RP</b>.\n"
        f"Используйте команды:\n"
        f"• /menu — Главное меню\n"
        f"• /profile — Ваш профиль и данные персонажа\n"
        f"• /help — Помощь по проекту\n"
        f"• /delete — Удалить текущего РП персонажа",
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 <b>Справка по проекту GreeLand RP:</b>\n\n"
        "1. Для регистрации персонажа и получения паспорта используйте форму регистрации.\n"
        "2. Для подачи жалоб или предложений используйте форумный раздел (Жалобы).\n"
        "3. По всем вопросам обращайтесь к администрации.",
        parse_mode="HTML"
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 <b>Главное меню GreeLand RP:</b>\n\n"
        "Выберите интересующий вас раздел или воспользуйтесь веб-приложением.",
        parse_mode="HTML"
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👤 <b>Ваш профиль:</b>\n\n"
        f"• Имя: {user.first_name}\n"
        f"• Telegram ID: <code>{user.id}</code>\n"
        f"• Статус: Игрок GreeLand RP",
        parse_mode="HTML"
    )

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ <b>Удаление персонажа:</b>\n\n"
        "Вы действительно хотите удалить своего РП персонажа и сбросить Static ID? "
        "Для подтверждения обратитесь к администрации или используйте внутриигровой функционал.",
        parse_mode="HTML"
    )


# --- API ДЛЯ МИНИ-ПРИЛОЖЕНИЙ ---

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
        text_to_admin = f"📋 <b>Новая заявка на паспорт / персонажа:</b>\n\n{content}"

    elif form_type == 'complaint':
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять / Одобрить", callback_data=f"comp_app_{user_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"comp_rej_{user_id}")
            ]
        ]
        text_to_admin = f"⚖️ <b>Новое обращение с форума (Жалобы):</b>\n\n{content}"
    else:
        return jsonify({"status": "error", "message": "Unknown type"}), 400

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_GROUP_ID,
        "text": text_to_admin,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Telegram API error: {e}")

    return jsonify({"status": "error", "message": "Telegram API error"}), 500


# --- ОБРАБОТЧИКИ КНОПОК И АДМИНКИ ---

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    admin_id = query.from_user.id

    if data.startswith("pass_app_"):
        target_user_id = int(data.split("_")[2])
        static_id = random.randint(1000, 9999)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ <b>Ваш паспорт и регистрация персонажа одобрены!</b>\n\n"
                     f"🪪 <b>Ваш игровой Static ID:</b> <code>{static_id}</code>\n"
                     f"🟢 Добро пожаловать в штат GreeLand RP!",
                parse_mode="HTML"
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

    elif data.startswith("comp_app_"):
        target_user_id = int(data.split("_")[2])
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="✅ Ваша жалоба / обращение на форуме была рассмотрена и <b>одобрена администрацией</b>!",
                parse_mode="HTML"
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
                text=f"❌ <b>Ваша заявка на регистрацию персонажа была отклонена.</b>\n\n📌 <b>Причина:</b> {text}",
                parse_mode="HTML"
            )
            await update.message.reply_text("✅ Уведомление об отклонении паспорта отправлено.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка: {e}")

    elif admin_id in PENDING_REJECT_COMPLAINT:
        target_user_id = PENDING_REJECT_COMPLAINT.pop(admin_id)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"❌ <b>Ваша тема / жалоба на форуме была отклонена.</b>\n\n📌 <b>Причина:</b> {text}",
                parse_mode="HTML"
            )
            await update.message.reply_text("✅ Уведомление об отклонении жалобы отправлено.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка: {e}")


def main():
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация команд
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("menu", menu_command))
    telegram_app.add_handler(CommandHandler("profile", profile_command))
    telegram_app.add_handler(CommandHandler("delete", delete_command))
    
    # Регистрация обработчиков кнопок и текста
    telegram_app.add_handler(CallbackQueryHandler(button_callback_handler))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_message_handler))

    port = int(os.environ.get("PORT", 5000))
    
    import threading
    def run_flask():
        app_bot.run(host="0.0.0.0", port=port)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    logger.info("Бот и сервер запущены успешно вместе с командами!")
    telegram_app.run_polling()


if __name__ == "__main__":
    main()
