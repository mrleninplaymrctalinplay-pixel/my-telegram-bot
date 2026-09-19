import os
import random
import logging
import json
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "8996747968:AAGt-wgqjd2Ao8stQezE_-othXKG3SC3Z54"
ADMIN_GROUP_ID = -1003913257980

# Ссылки на ваши Mini Apps (GitHub Pages)
URL_REGISTER = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/register.html"
URL_COMPLAINTS = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/complaints.html"
URL_SOCIAL = "https://mrleninplaymrctalinplay-pixel.github.io/my-telegram-bot/social.html"

app_bot = Flask(__name__)

# Хранилище выбранного языка пользователей (в памяти)
USER_LANGUAGES = {}

PENDING_REJECT_PASSPORT = {}
PENDING_REJECT_COMPLAINT = {}

# Тексты на разных языках
TRANSLATIONS = {
    "ru": {
        "welcome": "Привет, {name}! 👋\n\nДобро пожаловать в официальный бот проекта <b>GreeLand RP</b>.\nВыберите нужный раздел или измените язык:",
        "choose_lang": "🌍 Выберите язык / Select language:",
        "lang_changed": "✅ Язык успешно изменен на Русский!",
        "btn_social": "🌐 GreeLand Gram (Соцсеть)",
        "btn_register": "🪪 Регистрация паспорта",
        "btn_complaints": "⚖️ Жалобы и Форум",
        "btn_profile": "👤 Профиль",
        "btn_lang": "⚙️ Язык / Language",
        "help_text": "💡 <b>Справка по проекту GreeLand RP:</b>\n\n1. Используйте кнопки меню для доступа к сервисам.\n2. /menu — Главное меню\n3. /profile — Профиль\n4. /delete — Удалить персонажа",
        "profile_text": "👤 <b>Ваш профиль:</b>\n• Имя: {name}\n• ID: <code>{id}</code>\n• Статус: Игрок GreeLand RP",
        "delete_text": "⚠️ <b>Удаление персонажа:</b>\n\nВы действительно хотите удалить персонажа? Обратитесь к администрации."
    },
    "uk": {
        "welcome": "Привіт, {name}! 👋\n\nЛаскаво просимо до офіційного бота проекту <b>GreeLand RP</b>.\nВиберіть потрібний розділ або змініть мову:",
        "choose_lang": "🌍 Виберіть мову / Select language:",
        "lang_changed": "✅ Мову успішно змінено на Українську!",
        "btn_social": "🌐 GreeLand Gram (Соцмережа)",
        "btn_register": "🪪 Реєстрація паспорта",
        "btn_complaints": "⚖️ Скарги та Форум",
        "btn_profile": "👤 Профіль",
        "btn_lang": "⚙️ Мова / Language",
        "help_text": "💡 <b>Довідка щодо проекту GreeLand RP:</b>\n\n1. Використовуйте кнопки меню для доступу до сервісів.\n2. /menu — Головне меню\n3. /profile — Профіль\n4. /delete — Видалити персонажа",
        "profile_text": "👤 <b>Ваш профіль:</b>\n• Ім'я: {name}\n• ID: <code>{id}</code>\n• Статус: Гравець GreeLand RP",
        "delete_text": "⚠️ <b>Видалення персонажа:</b>\n\nВи дійсно хочете видалити персонажа? Зверніться до адміністрації."
    },
    "kk": {
        "welcome": "Сәлем, {name}! 👋\n\n<b>GreeLand RP</b> жобасынын ресми ботына қош келдіңіз.\nҚажетті бөлімді таңдаңыз немесе тілді өзгертіңіз:",
        "choose_lang": "🌍 Тілді таңдаңыз / Select language:",
        "lang_changed": "✅ Тіл Қазақ тіліне сәтті өзгертілді!",
        "btn_social": "🌐 GreeLand Gram (Әлеуметтік желі)",
        "btn_register": "🪪 Төлқұжатты тіркеу",
        "btn_complaints": "⚖️ Шағымдар және Форум",
        "btn_profile": "👤 Профиль",
        "btn_lang": "⚙️ Тіл / Language",
        "help_text": "💡 <b>GreeLand RP анықтамасы:</b>\n\n1. Қызметтерді ашу үшін мәзір түймелерін пайдаланыңыз.\n2. /menu — Басты мәзір\n3. /profile — Профиль\n4. /delete — Кейіпкерді жою",
        "profile_text": "👤 <b>Сіздің профиліңіз:</b>\n• Аты: {name}\n• ID: <code>{id}</code>\n• Статус: GreeLand RP ойыншысы",
        "delete_text": "⚠️ <b>Кейіпкерді жою:</b>\n\nКейіпкерді шынымен жойғыңыз келе ме? Әкімшілікке хабарласыңыз."
    },
    "en": {
        "welcome": "Hello, {name}! 👋\n\nWelcome to the official <b>GreeLand RP</b> project bot.\nSelect a section or change the language below:",
        "choose_lang": "🌍 Select your language:",
        "lang_changed": "✅ Language successfully changed to English!",
        "btn_social": "🌐 GreeLand Gram (Social)",
        "btn_register": "🪪 Passport Registration",
        "btn_complaints": "⚖️ Complaints & Forum",
        "btn_profile": "👤 Profile",
        "btn_lang": "⚙️ Language",
        "help_text": "💡 <b>GreeLand RP Help:</b>\n\n1. Use the menu buttons to access services.\n2. /menu — Main menu\n3. /profile — Profile\n4. /delete — Delete character",
        "profile_text": "👤 <b>Your Profile:</b>\n• Name: {name}\n• ID: <code>{id}</code>\n• Status: GreeLand RP Player",
        "delete_text": "⚠️ <b>Character Deletion:</b>\n\nDo you really want to delete your character? Contact administration."
    }
}

def get_lang(user_id):
    return USER_LANGUAGES.get(user_id, "ru")

def get_keyboard(lang):
    t = TRANSLATIONS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["btn_social"], web_app={"url": URL_SOCIAL})],
        [InlineKeyboardButton(t["btn_register"], web_app={"url": URL_REGISTER})],
        [InlineKeyboardButton(t["btn_complaints"], web_app={"url": URL_COMPLAINTS})],
        [
            InlineKeyboardButton(t["btn_profile"], callback_data="btn_profile"),
            InlineKeyboardButton(t["btn_lang"], callback_data="btn_language_menu")
        ]
    ])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)
    text = TRANSLATIONS[lang]["welcome"].format(name=user.first_name)
    reply_markup = get_keyboard(lang)
    
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(TRANSLATIONS[lang]["help_text"], parse_mode="HTML")

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(user.id)
    text = TRANSLATIONS[lang]["profile_text"].format(name=user.first_name, id=user.id)
    await update.message.reply_text(text, parse_mode="HTML")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(TRANSLATIONS[lang]["delete_text"], parse_mode="HTML")

@app_bot.route('/api/submit', methods=['POST'])
def handle_miniapp_submit():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    form_type = data.get('type')
    user_id = data.get('user_id')
    content = data.get('content')

    if form_type == 'passport':
        keyboard = [[
            InlineKeyboardButton("✅ Одобрить", callback_data=f"pass_app_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"pass_rej_{user_id}")
        ]]
        text_to_admin = f"📋 <b>Новая заявка на паспорт:</b>\n\n{content}"
    elif form_type == 'complaint':
        keyboard = [[
            InlineKeyboardButton("✅ Принять", callback_data=f"comp_app_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"comp_rej_{user_id}")
        ]]
        text_to_admin = f"⚖️ <b>Новая жалоба / Forum:</b>\n\n{content}"
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
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Telegram API error: {e}")

    return jsonify({"status": "error", "message": "Telegram API error"}), 500

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    lang = get_lang(user_id)

    if data == "btn_profile":
        user = query.from_user
        text = TRANSLATIONS[lang]["profile_text"].format(name=user.first_name, id=user.id)
        await query.message.reply_text(text, parse_mode="HTML")
    elif data == "btn_language_menu":
        lang_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
            [InlineKeyboardButton("🇺🇦 Українська", callback_data="set_lang_uk")],
            [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="set_lang_kk")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")],
            [InlineKeyboardButton("◀️ Назад / Back", callback_data="btn_back_start")]
        ])
        await query.message.edit_text("🌍 Выберите язык / Select language:", reply_markup=lang_keyboard)
    elif data.startswith("set_lang_"):
        new_lang = data.split("_")[2]
        USER_LANGUAGES[user_id] = new_lang
        await query.answer(TRANSLATIONS[new_lang]["lang_changed"], show_alert=True)
        await start_command(update, context)
    elif data == "btn_back_start":
        await start_command(update, context)
    elif data.startswith("pass_app_"):
        target_user_id = int(data.split("_")[2])
        static_id = random.randint(1000, 9999)
        await context.bot.send_message(target_user_id, f"✅ Паспорт одобрен! Ваш Static ID: <code>{static_id}</code>", parse_mode="HTML")
        await query.edit_message_text(f"{query.message.text}\n\n<b>[ОДОБРЕНО]</b> Static: {static_id}", parse_mode="HTML")
    elif data.startswith("comp_app_"):
        target_user_id = int(data.split("_")[2])
        await context.bot.send_message(target_user_id, "✅ Ваша жалоба одобрена администрацией!", parse_mode="HTML")
        await query.edit_message_text(f"{query.message.text}\n\n<b>[ПРИНЯТО]</b>", parse_mode="HTML")

def main():
    telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("menu", menu_command))
    telegram_app.add_handler(CommandHandler("profile", profile_command))
    telegram_app.add_handler(CommandHandler("delete", delete_command))
    telegram_app.add_handler(CallbackQueryHandler(button_callback_handler))

    port = int(os.environ.Context.get("PORT", 5000) if hasattr(os.environ, "Context") else os.environ.get("PORT", 5000))
    
    import threading
    def run_flask():
        app_bot.run(host="0.0.0.0", port=port)

    threading.Thread(target=run_flask).start()
    telegram_app.run_polling()

if __name__ == "__main__":
    main()
