from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import math
import random
import csv
import os
import json

# ======================
# TOKEN (Railway Safe)
# ======================
TOKEN = os.environ["TOKEN"]

# ======================
# MEMORY
# ======================
user_data_store = {}

# ======================
# USED INDEX STORAGE (BY ZIP)
# ======================
USED_FILE = "used.json"

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
# TAX FUNCTIONS
# ======================
def floor_2(x):
    return math.floor(x * 100) / 100

def random_time():
    hour = random.randint(10, 19)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

# ======================
# ADDRESS SYSTEM
# ======================
def get_sequential_address(zip_code):
    results = []

    try:
        with open("addresses.csv", newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if row["zip"] == zip_code:
                    address = f"{row['number']} {row['street']}, {row['city']}, {row['state']} {row['zip']}"
                    results.append(address)

        if not results:
            return None, 0, 0

        total = len(results)
        current_index = used_index.get(zip_code, 0)

        if current_index >= total:
            return None, total, 0

        address = results[current_index]

        used_index[zip_code] = current_index + 1
        save_used(used_index)

        remaining = total - (current_index + 1)

        return address, current_index + 1, remaining

    except:
        return None, 0, 0

# ======================
# START
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["💰 Tax", "🏠 Home Address"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("اختر خدمة:", reply_markup=reply_markup)

# ======================
# MAIN HANDLER
# ======================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.message.chat_id

    # ======================
    # ADDRESS FLOW
    # ======================
    if text == "🏠 Home Address":
        user_data_store[chat_id] = "ADDRESS"
        await update.message.reply_text("اكتب ZIP code:")
        return

    if user_data_store.get(chat_id) == "ADDRESS":
        zip_code = text

        result, current_num, remaining = get_sequential_address(zip_code)

        if result:
            await update.message.reply_text(
                f"Address {current_num}\n{result}\nRemaining: {remaining}"
            )
        else:
            await update.message.reply_text(
                "لا يوجد عناوين متاحة لهذا الـ ZIP"
            )

        user_data_store.pop(chat_id, None)
        return

    # ======================
    # TAX FLOW
    # ======================
    if text == "💰 Tax":
        keyboard = [
            ["1", "2", "3", "4", "5"],
            ["6", "7", "8", "9", "10"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("اختر عدد المنتجات:", reply_markup=reply_markup)
        return

    if text.isdigit():
        qty = int(text)
        user_data_store[chat_id] = qty

        await update.message.reply_text(
            f"تم اختيار {qty} منتجات\nالآن اكتب السعر والضريبة مثل:\n299.99 7.5"
        )
        return

    try:
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text("اكتب مثل: 299.99 7.5")
            return

        num = float(parts[0])
        tax_percent = float(parts[1])

        qty = user_data_store.get(chat_id, 4)

        subtotal = floor_2(num * qty)
        tax = floor_2(subtotal * (tax_percent / 100))
        total = floor_2(subtotal + tax)

        time = random_time()

        reply = (
            f"Quantity: {qty}\n"
            f"Subtotal: {subtotal:.2f}\n"
            f"Tax: {tax:.2f}\n"
            f"Total: {total:.2f}\n"
            f"Time: {time}"
        )

    except:
        reply = "اكتب مثل: 299.99 7.5"

    await update.message.reply_text(reply)

# ======================
# RUN BOT
# ======================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()