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
# INIT SQLITE
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
# ADDRESS SYSTEM
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
        cursor.execute("UPDATE zip_counter SET idx=? WHERE zip=?", (index + 1, zip_code))
    else:
        cursor.execute("INSERT INTO zip_counter (zip, idx) VALUES (?, ?)", (zip_code, 1))

    conn.commit()
    conn.close()

    return selected, index + 1, total - (index + 1)

# ======================
# TAX SYSTEM
# ======================
def floor_2(x):
    return math.floor(x * 100) / 100

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
    # ADDRESS
    # ======================
    if text == "🏠 Home Address":
        user_data_store[chat_id] = "ADDRESS"
        await update.message.reply_text("اكتب ZIP code:")
        return

    if state == "ADDRESS":
        row = get_sequential_address(text)

        if not row:
            await update.message.reply_text("❌ ZIP code غير موجود أو غير صحيح")
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
    # CAR (placeholder)
    # ======================
    if text == "🚗 Car":
        user_data_store[chat_id] = "CAR"
        await update.message.reply_text("اكتب Item Number:")
        return

    if state == "CAR":
        await update.message.reply_text("❌ Car system غير مفعّل حالياً")
        user_data_store.pop(chat_id, None)
        await start(update, context)
        return

    # ======================
    # TAX START
    # ======================
    if text == "💰 Tax":
        user_data_store[chat_id] = {"step": "TAX_QTY"}
        await update.message.reply_text("اختر عدد المنتجات:")
        return

    # ======================
    # TAX FLOW FIXED
    # ======================
    if isinstance(state, dict) and state.get("step") == "TAX_QTY":
        try:
            qty = int(text)
            user_data_store[chat_id] = {"step": "TAX_PRICE", "qty": qty}
            await update.message.reply_text("اكتب السعر والضريبة مثل:\n299.99 7.5")
            return
        except:
            await update.message.reply_text("اكتب رقم صحيح")
            return

    if isinstance(state, dict) and state.get("step") == "TAX_PRICE":
        try:
            parts = text.split()

            if len(parts) != 2:
                raise ValueError

            price = float(parts[0])
            tax_percent = float(parts[1])
            qty = state["qty"]

            subtotal = floor_2(price * qty)
            tax = floor_2(subtotal * (tax_percent / 100))
            total = floor_2(subtotal + tax)

            await update.message.reply_text(
                f"Quantity: {qty}\n"
                f"Subtotal: {subtotal:.2f}\n"
                f"Tax: {tax:.2f}\n"
                f"Total: {total:.2f}"
            )

            user_data_store.pop(chat_id, None)
            await start(update, context)
            return

        except:
            await update.message.reply_text("اكتب مثل: 299.99 7.5")
            return

# ======================
# RUN BOT
# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("support", support))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()