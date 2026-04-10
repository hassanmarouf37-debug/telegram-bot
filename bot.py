from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import math
import random

TOKEN = "8569435543:AAHmCXEMKfqRbgYal7NAma_9j8NlmDPhzok"

user_data_store = {}

def floor_2(x):
    return math.floor(x * 100) / 100

def random_time():
    hour = random.randint(10, 19)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

# شاشة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["💰 Tax"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("اختر خدمة:", reply_markup=reply_markup)

# التعامل مع الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ضغط Tax
    if text == "💰 Tax":
        keyboard = [
            ["1", "2", "3", "4", "5"],
            ["6", "7", "8", "9", "10"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("اختر عدد المنتجات:", reply_markup=reply_markup)
        return

    # اختيار عدد المنتجات
    if text.isdigit():
        qty = int(text)
        user_data_store[update.message.chat_id] = qty

        await update.message.reply_text(
            f"تم اختيار {qty} منتجات\nالآن اكتب السعر والضريبة مثل:\n299.99 7.5"
        )
        return

    # الحساب
    try:
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text("اكتب هيك: 299.99 7.5")
            return

        num = float(parts[0])
        tax_percent = float(parts[1])

        qty = user_data_store.get(update.message.chat_id, 4)

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


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()