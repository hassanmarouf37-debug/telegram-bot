from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import math
import csv
import os
import json

TOKEN = os.environ["TOKEN"]

user_data_store = {}

USED_FILE = "used.json"
CARS_FILE = "cars.csv"

SUPPORT_USERNAME = "@hassanmarouf37"

# ======================
# ADDRESS STORAGE
# ======================
def load_used():
    try:
        with open(USED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_used(data):
    with open(USED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

used_index = load_used()

# ======================
# HELPERS
# ======================
def random_time():
    import random
    return f"{random.randint(10,19):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"

# ======================
# ADDRESS SYSTEM
# ======================
def get_sequential_address(zip_code):
    results = []

    with open("addresses.csv", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["zip"] == zip_code:
                results.append(row)

    if not results:
        return None

    total = len(results)
    index = used_index.get(zip_code, 0)

    if index >= total:
        index = 0

    row = results[index]

    used_index[zip_code] = index + 1
    save_used(used_index)

    return row, index + 1, total - (index + 1)

# ======================
# CAR SYSTEM
# ======================
def get_car_by_item(item_number):
    cars = []
    mspn = None

    with open(CARS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["item"] == item_number:
                cars.append(row["car"])
                mspn = row["mspn"]

    if not cars:
        return None, None

    total = len(cars)
    index = 0

    car = cars[index % total]

    return mspn, car

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
    # ADDRESS START
    # ======================
    if text == "🏠 Home Address":
        user_data_store[chat_id] = "ADDRESS"
        await update.message.reply_text("اكتب ZIP code:")
        return

    if state == "ADDRESS":
        row, current_num, remaining = get_sequential_address(text)

        if not row:
            await update.message.reply_text(
                "❌ ZIP code غير موجود أو غير صحيح"
            )
            user_data_store.pop(chat_id, None)
            await start(update, context)
            return

        street = f"{row['number']} {row['street']}"
        city = row["city"]
        state_v = row["state"]
        zip_v = row["zip"]

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
    # CAR START
    # ======================
    if text == "🚗 Car":
        user_data_store[chat_id] = "CAR"
        await update.message.reply_text("اكتب Item Number:")
        return

    if state == "CAR":
        mspn, car = get_car_by_item(text)

        if mspn:
            await update.message.reply_text(
                f"MSPN: {mspn}\nCar: {car}"
            )
        else:
            await update.message.reply_text(
                "❌ Item number غير موجود أو غير صحيح"
            )

        user_data_store.pop(chat_id, None)
        await start(update, context)
        return

    # ======================
    # TAX START
    # ======================
    if text == "💰 Tax":
        user_data_store[chat_id] = "TAX"
        await update.message.reply_text("اختر عدد المنتجات:")
        return

# ======================
# RUN BOT
# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("support", support))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()