from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import psycopg2
import os
import csv
import math
import random

# ======================
# CONFIG
# ======================
TOKEN = os.environ["TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

SUPPORT_USERNAME = "@hassanmarouf37"

user_data = {}

# ======================
# DB INIT
# ======================
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS zip_counter (
        zip TEXT PRIMARY KEY,
        idx INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ======================
# UTIL
# ======================
def rnd_time():
    return f"{random.randint(5,10):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"

def fix(x):
    return math.floor(x * 100) / 100

# ======================
# ADDRESS SYSTEM
# ======================
def get_address(zip_code):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT idx FROM zip_counter WHERE zip=%s", (zip_code,))
    row = cur.fetchone()

    idx = row[0] if row else 0

    rows = []
    with open("addresses.csv", newline='', encoding="utf-8") as f:
        r = csv.DictReader(f)
        for i in r:
            if i["zip"] == zip_code:
                rows.append(i)

    if not rows:
        conn.close()
        return None

    total = len(rows)

    if idx >= total:
        idx = 0

    selected = rows[idx]

    if row:
        cur.execute("UPDATE zip_counter SET idx=%s WHERE zip=%s", (idx + 1, zip_code))
    else:
        cur.execute("INSERT INTO zip_counter (zip, idx) VALUES (%s, %s)", (zip_code, 1))

    conn.commit()
    conn.close()

    return selected, idx + 1, total - (idx + 1)

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["💰 Tax"],
        ["🏠 Home Address"],
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
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat_id

    state = user_data.get(chat_id, None)

    # ======================
    # 🔥 HARD GUARD (FIX MAIN BUG)
    # ======================
    if not state and text not in ["💰 Tax", "🏠 Home Address", "🚗 Car", "/start", "/support"]:
        await start(update, context)
        return

    # ======================
    # TAX
    # ======================
    if text == "💰 Tax":
        user_data[chat_id] = {"step": "qty"}
        await update.message.reply_text("اختر عدد المنتجات:")
        return

    if state and state.get("step") == "qty":
        try:
            qty = int(text)
            user_data[chat_id] = {"step": "price", "qty": qty}
            await update.message.reply_text("اكتب السعر والضريبة: 299.99 7.5")
        except:
            await update.message.reply_text("❌ رقم غير صحيح")
        return

    if state and state.get("step") == "price":
        try:
            price, tax = map(float, text.split())
            qty = state["qty"]

            subtotal = fix(price * qty)
            tax_val = fix(subtotal * (tax / 100))
            total = fix(subtotal + tax_val)

            await update.message.reply_text(
                f"Quantity: {qty}\n"
                f"Subtotal: {subtotal:.2f}\n"
                f"Tax ({tax}%): {tax_val:.2f}\n"
                f"Total: {total:.2f}\n"
                f"Time: {rnd_time()}"
            )

            user_data.pop(chat_id, None)
            await start(update, context)
        except:
            await update.message.reply_text("❌ صيغة خطأ")
        return

    # ======================
    # ADDRESS
    # ======================
    if text == "🏠 Home Address":
        user_data[chat_id] = {"step": "zip"}
        await update.message.reply_text("اكتب ZIP code:")
        return

    if state and state.get("step") == "zip":
        if not text.isdigit():
            await update.message.reply_text("❌ ZIP code غير صحيح")
            return

        row = get_address(text)

        if not row:
            await update.message.reply_text("❌ ZIP غير موجود")
            user_data.pop(chat_id, None)
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

        user_data.pop(chat_id, None)
        await start(update, context)
        return

    # ======================
    # CAR (FIXED)
    # ======================
    if text == "🚗 Car":
        user_data[chat_id] = {"step": "car"}
        await update.message.reply_text("اكتب Item Number:")
        return

    if state and state.get("step") == "car":
        item = text.strip()

        if len(item) < 3:
            await update.message.reply_text("❌ Item غير صحيح")
            return

        await update.message.reply_text(
            f"Item: {item}\nMSPN: 56028\nCar: Toyota Camry"
        )

        user_data.pop(chat_id, None)
        await start(update, context)
        return

# ======================
# RUN BOT
# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("support", support))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()