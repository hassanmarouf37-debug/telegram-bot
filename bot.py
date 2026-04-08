from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import math

TOKEN = "8569435543:AAHmCXEMKfqRbgYal7NAma_9j8NlmDPhzok"

def floor_2(x):
    return math.floor(x * 100) / 100

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    try:
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text("اكتب هيك: 100 8")
            return

        num = float(parts[0])
        tax_percent = float(parts[1])

        subtotal = num * 4
        tax = subtotal * (tax_percent / 100)
        total = subtotal + tax

        subtotal = floor_2(subtotal)
        tax = floor_2(tax)
        total = floor_2(total)

        reply = (
            f"Subtotal: {subtotal:.2f}\n"
            f"Tax ({tax_percent}%): {tax:.2f}\n"
            f"Total: {total:.2f}"
        )

    except:
        reply = "خطأ بالمدخلات. اكتب مثل: 299.99 7.5"

    await update.message.reply_text(reply)


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()