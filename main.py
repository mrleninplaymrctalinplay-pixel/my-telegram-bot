# ==================== СБРОС И УДАЛЕНИЕ ====================

@router.message(Command("delete"))
@router.message(Command("reset"))
@router.callback_query(F.data == "user_delete_self")
async def cmd_delete_character(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    lang = get_user_lang(user_id)
    t = TEXTS[lang]

    await state.clear()
    cursor.execute("UPDATE users SET roblox_nick=NULL, fio=NULL, birth_date=NULL, gender=NULL, bio=NULL, status='none' WHERE user_id = ?", (user_id,))
    conn.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t["form_btn"], web_app=WebAppInfo(url=WEB_APP_URL))]])
    
    if isinstance(event, Message):
        await event.answer(t["deleted"], reply_markup=kb)
    else:
        await event.message.edit_text(t["deleted"], reply_markup=kb)

# ==================== ПРИЕМ ДАННЫХ ИЗ WEB APP ====================

@router.message(F.web_app_data)
async def handle_web_app_data(message: Message, bot: Bot):
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    t = TEXTS[lang]

    try:
        data = json.loads(message.web_app_data.data)
        username = message.from_user.username or "N/A"

        roblox_nick = data.get("robloxNick", "N/A")
        full_name = data.get("fullName", "N/A")
        dob = data.get("dob", "N/A")
        gender = data.get("gender", "N/A")
        bio = data.get("bio", "N/A")

        cursor.execute("""
        UPDATE users SET username=?, roblox_nick=?, fio=?, birth_date=?, gender=?, bio=?, status='pending'
        WHERE user_id=?
        """, (username, roblox_nick, full_name, dob, gender, bio, user_id))
        conn.commit()

        # Уведомление админу
        admin_text = (
            f"📋 New Registration Submitted via Web App:\n"
            f"👤 From: @{username} (ID: {user_id})\n"
            f"🌐 Lang: {lang}\n\n"
            f"🎮 Roblox Username: {roblox_nick}\n"
            f"📛 Full Name: {full_name}\n"
            f"📅 Date of Birth: {dob}\n"
            f"⚧ Gender: {gender}\n"
            f"📖 Biography: {bio}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user_id}")
        ]])

        await bot.send_message(ADMIN_CHAT_ID, admin_text, reply_markup=kb, parse_mode="Markdown")
        await message.answer(t["submitted"], parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Error processing submission: {e}")

# ==================== ДЕЙСТВИЯ АДМИНИСТРАТОРА ====================

@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (target_id,))
    conn.commit()

    await bot.send_message(target_id, "🎉 Your Canadian character registration has been approved!")
    await callback.message.edit_text(callback.message.text + "\n\n✅ APPROVED")

@router.callback_query(F.data.startswith("reject_"))
async def reject_user(callback: CallbackQuery, bot: Bot):
    target_id = int(callback.data.split("_")[1])
    cursor.execute("UPDATE users SET status = 'rejected' WHERE user_id = ?", (target_id,))
    conn.commit()

    await bot.send_message(target_id, "❌ Your character registration application was rejected.")
    await callback.message.edit_text(callback.message.text + "\n\n❌ REJECTED")

# ==================== ЗАПУСК ====================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
