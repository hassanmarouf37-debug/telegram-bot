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
# DB CONNECTION
# ======================
def get_conn():
    return psycopg2.connect(DATABASE_URL)

# ======================
# INIT DB
# ======================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS zip_counter (
        zip TEXT PRIMARY KEY,
        idx INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS car_counter (
        item TEXT PRIMARY KEY,
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
    hour = random.randint(10, 17)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def fix(x):
    return math.floor(x * 100) / 100

def reset(chat_id):
    user_data.pop(chat_id, None)

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
        reader = csv.DictReader(f)
        for r in reader:
            if r["zip"] == zip_code:
                rows.append(r)

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
# CAR SYSTEM (UPDATED)
# ======================
def get_car(item_code):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT idx FROM car_counter WHERE item=%s", (item_code,))
    row = cur.fetchone()

    idx = row[0] if row else 0

    cars = []

    # جمع كل السيارات من أي عدد أعمدة carX
    with open("cars.csv", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            if r["item"] == item_code:
                for key in r.keys():
                    if key.startswith("car") and r[key]:
                        cars.append(r[key])
                break

    if not cars:
        conn.close()
        return None

    total = len(cars)

    if idx >= total:
        idx = 0

    selected_car = cars[idx]

    if row:
        cur.execute(
            "UPDATE car_counter SET idx=%s WHERE item=%s",
            (idx + 1, item_code)
        )
    else:
        cur.execute(
            "INSERT INTO car_counter (item, idx) VALUES (%s, %s)",
            (item_code, 1)
        )

    conn.commit()
    conn.close()

    return selected_car, idx + 1, total

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset(update.message.chat_id)

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

    state = user_data.get(chat_id)

    # ======================
    # TAX START
    # ======================
    if text == "💰 Tax":
        reset(chat_id)
        user_data[chat_id] = {"step": "qty"}

        keyboard = [
            ["1", "2", "3", "4", "5"],
            ["6", "7", "8", "9", "10"]
        ]

        await update.message.reply_text(
            "اختر عدد المنتجات:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    if state and state.get("step") == "qty":
        if not text.isdigit():
            return

        user_data[chat_id] = {"step": "price", "qty": int(text)}
        await update.message.reply_text("اكتب السعر والضريبة: 299.99 7.5")
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

            reset(chat_id)
            await start(update, context)
            return

        except:
            await update.message.reply_text("❌ صيغة غير صحيحة")
            return

    # ======================
    # ADDRESS
    # ======================
    if text == "🏠 Home Address":
        reset(chat_id)
        user_data[chat_id] = {"step": "zip"}
        await update.message.reply_text("اكتب ZIP code:")
        return

    if state and state.get("step") == "zip":
        if not text.isdigit():
            return

        row = get_address(text)

        if not row:
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

        reset(chat_id)
        await start(update, context)
        return

    # ======================
    # CAR SYSTEM
    # ======================
    if text == "🚗 Car":
        reset(chat_id)
        user_data[chat_id] = {"step": "car"}
        await update.message.reply_text("اكتب Item Number:")
        return

    if state and state.get("step") == "car":
        item = text.strip()

        result = get_car(item)

        if not result:
            await update.message.reply_text("❌ Item غير موجود")
            reset(chat_id)
            await start(update, context)
            return

        car, current, total = result

        await update.message.reply_text(
            f"Item: {item}\n"
            f"Car: {car}\n"
            f"Progress: {current}/{total}"
        )

        reset(chat_id)
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