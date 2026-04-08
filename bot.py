from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import math
import random

TOKEN = "8569435543:AAHmCXEMKfqRbgYal7NAma_9j8NlmDPhzok"

def floor_2(x):
    return math.floor(x * 100) / 100

def random_time():
    hour = random.randint(10, 19)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text("اكتب هيك: 100 8")
            return

        num = float(parts[0])
        tax_percent = float(parts[1])

        subtotal = floor_2(num * 4)
        tax = floor_2(subtotal * (tax_percent / 100))
        total = floor_2(subtotal + tax)

        time = random_time()

        reply = (
            f"Subtotal: {subtotal:.2f}\n"
            f"Tax ({tax_percent}%): {tax:.2f}\n"
            f"Total: {total:.2f}\n"
            f"Time: {time}"
        )

    except:
        reply = "اكتب مثل: 299.99 7.5"

    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()