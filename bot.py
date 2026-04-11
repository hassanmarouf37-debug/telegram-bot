from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import math
import csv
import os
import sqlite3

TOKEN = os.environ["TOKEN"]

user_data_store = {}

SUPPORT_USERNAME = "@hassanmarouf37"

# ======================
# INIT SQLITE DB
# ======================
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS zip_counter (
    zip TEXT PRIMARY KEY,
    idx INTEGER
)
""")

conn.commit()
conn.close()

# ======================
# HELPERS
# ======================
def random_time():
    import random
    return f"{random.randint(10,19):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"

# ======================
# ADDRESS SYSTEM (SQLITE)
# ======================
def get_sequential_address(zip_code):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT idx FROM zip_counter WHERE zip=?", (zip_code,))
    row = cursor.fetchone()

    index = row[0] if row else 0

    results = []

    with open("addresses.csv", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["zip"] == zip_code:
                results.append(r)

    if not results:
        conn.close()
        return None

    total = len(results)

    if index >= total:
        index = 0

    selected = results[index]

    if row:
        cursor.execute(
            "UPDATE zip_counter SET idx=? WHERE zip=?",
            (index + 1, zip_code)
        )
    else:
        cursor.execute(
            "INSERT INTO zip_counter (zip, idx) VALUES (?, ?)",
            (zip_code, 1)
        )

    conn.commit()
    conn.close()

    return selected, index + 1, total - (index + 1)

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💰 Tax", "🏠 Home Address"],
        ["🚗 Car"]
    ]
    await update.message.reply_text(
        "اختر خدمة:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ======================
# SUPPORT
# ======================
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(SUPPORT_USERNAME)

# ======================
# MAIN HANDLER
# ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat_id

    state = user_data_store.get(chat_id)

    # ======================
    # ADDRESS FLOW
    # ======================
    if text == "🏠 Home Address":
        user_data_store[chat_id] = "ADDRESS"
        await update.message.reply_text("اكتب ZIP code:")
        return

    if state == "ADDRESS":
        row = get_sequential_address(text)

        if not row:
            await update.message.reply_text(
                "❌ ZIP code غير موجود أو غير صحيح"
            )
            user_data_store.pop(chat_id, None)
            await start(update, context)
            return

        data, current_num, remaining = row

        street = f"{data['number']} {data['street']}"
        city = data["city"]
        state_v = data["state"]
        zip_v = data["zip"]

        await update.message.reply_text(
            f"Address {current_num}\n\n"
            f"Street Address: {street}\n"
            f"City: {city}\n"
            f"State: {state_v}\n"
            f"ZIP Code: {zip_v}\n\n"
            f"Remaining: {remaining}"
        )

        user_data_store.pop(chat_id, None)
        await start(update, context)
        return

    # ======================
    # CAR FLOW (basic fallback if not implemented)
    # ======================
    if text == "🚗 Car":
        user_data_store[chat_id] = "CAR"
        await update.message.reply_text("اكتب Item Number:")
        return

    if state == "CAR":
        await update.message.reply_text(
            "❌ Car system غير مفعل بالكامل في هذا الإصدار"
        )
        user_data_store.pop(chat_id, None)
        await start(update, context)
        return

    # ======================
    # TAX FLOW (placeholder)
    # ======================
    if text == "💰 Tax":
        await update.message.reply_text("Tax system موجود سابقاً بالكود الأساسي")
        return

# ======================
# RUN BOT
# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("support", support))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()