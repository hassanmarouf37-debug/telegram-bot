from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import math
import csv
import os
import psycopg2
import random

TOKEN = os.environ["TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

user_data_store = {}

SUPPORT_USERNAME = "@hassanmarouf37"

# ======================
# DB INIT
# ======================
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zip_counter (
        zip TEXT PRIMARY KEY,
        idx INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ======================
# HELPERS
# ======================
def random_time():
    return f"{random.randint(5,10):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"

def floor_2(x):
    return math.floor(x * 100) / 100

# ======================
# ADDRESS SYSTEM (POSTGRESQL)
# ======================
def get_sequential_address(zip_code):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("SELECT idx FROM zip_counter WHERE zip=%s", (zip_code,))
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
            "UPDATE zip_counter SET idx=%s WHERE zip=%s",
            (index + 1, zip_code)
        )
    else:
        cursor.execute(
            "INSERT INTO zip_counter (zip, idx) VALUES (%s, %s)",
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
    # ADDRESS
    # ======================
    if text == "🏠 Home Address":
        user_data_store[chat_id] = "ADDRESS"
        await update.message.reply_text("اكتب ZIP code:")
        return

    if state == "ADDRESS":
        row = get_sequential_address(text)

        if not row:
            await update.message.reply_text("❌ ZIP code غير موجود")
            user_data_store.pop(chat_id, None)
            await start(update, context)
            return

        data, current, remaining = row

        await update.message.reply_text(
            f"Address {current}\n\n"
            f"Street: {data['number']} {data['street']}\n"
            f"City: {data['city']}\n"
            f"State: {data['state']}\n"
            f"ZIP: {data['zip']}\n\n"
            f"Remaining: {remaining}"
        )

        user_data_store.pop(chat_id, None)
        await start(update, context)
        return

    # ======================
    # TAX
    # ======================
    if text == "💰 Tax":
        user_data_store[chat_id] = {"step": "TAX_QTY"}
        await update.message.reply_text("اختر عدد المنتجات:")
        return

    if isinstance(state, dict) and state.get("step") == "TAX_QTY":
        try:
            qty = int(text)
            user_data_store[chat_id] = {"step": "TAX_PRICE", "qty": qty}
            await update.message.reply_text("اكتب السعر والضريبة مثل: 299.99 7.5")
            return
        except:
            await update.message.reply_text("اكتب رقم صحيح")
            return

    if isinstance(state, dict) and state.get("step") == "TAX_PRICE":
        try:
            price, tax_percent = map(float, text.split())
            qty = state["qty"]

            subtotal = floor_2(price * qty)
            tax = floor_2(subtotal * (tax_percent / 100))
            total = floor_2(subtotal + tax)

            await update.message.reply_text(
                f"Quantity: {qty}\n"
                f"Subtotal: {subtotal:.2f}\n"
                f"Tax ({tax_percent}%): {tax:.2f}\n"
                f"Total: {total:.2f}\n"
                f"Time: {random_time()}"
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