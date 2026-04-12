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
    # جدول الـ ZIP
    cur.execute("""
    CREATE TABLE IF NOT EXISTS zip_counter (
        zip TEXT PRIMARY KEY,
        idx INTEGER DEFAULT 0
    )
    """)
    # جدول السيارات (الـ Item)
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
# UTIL & HELPERS
# ======================
def reset(chat_id):
    if chat_id in user_data:
        user_data.pop(chat_id)

def get_car(item_id):
    if not os.path.exists('cars.csv'):
        return None
    try:
        with open('cars.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # تخطي الهيدر
            for row in reader:
                if not row: continue
                # المقارنة كنصوص للحفاظ على الأصفار
                if row[0].strip() == item_id.strip():
                    # استخراج السيارات وتجاهل الفراغات
                    cars_list = [c.strip() for c in row[1:] if c.strip()]
                    if not cars_list: return None

                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("SELECT idx FROM car_counter WHERE item = %s", (item_id,))
                    res = cur.fetchone()
                    
                    idx = res[0] if res else 0
                    if not res:
                        cur.execute("INSERT INTO car_counter (item, idx) VALUES (%s, 0)", (item_id,))
                    
                    current_car = cars_list[idx % len(cars_list)]
                    new_idx = (idx + 1) % len(cars_list)
                    
                    cur.execute("UPDATE car_counter SET idx = %s WHERE item = %s", (new_idx, item_id))
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    return current_car, (idx % len(cars_list)) + 1, len(cars_list)
    except Exception as e:
        print(f"Error: {e}")
    return None

# ======================
# COMMANDS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["🚗 Car", "📮 ZIP"], ["🛠 Support"]]
    await update.message.reply_text(
        "مرحباً بك في بوت الخدمات. اختر من القائمة أدناه:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_data.get(chat_id)

    if text == "🚗 Car":
        reset(chat_id)
        user_data[chat_id] = {"step": "car"}
        await update.message.reply_text("📥 من فضلك أرسل الـ Item Number:")
        return

    if state and state.get("step") == "car":
        item_input = text.strip()
        result = get_car(item_input)

        if not result:
            await update.message.reply_text("❌ عذراً، هذا الـ Item غير موجود.")
        else:
            car_name, current, total = result
            await update.message.reply_text(
                f"✅ **Item Details**\n\n"
                f"🔢 **Item:** `{item_input}`\n"
                f"🚗 **Car:** {car_name}\n"
                f"📊 **Progress:** {current}/{total}",
                parse_mode="Markdown"
            )
        reset(chat_id)
        await start(update, context)
        return

    if text == "🛠 Support":
        await update.message.reply_text(f"للدعم الفني تواصل مع: {SUPPORT_USERNAME}")
        return

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت يعمل الآن...")
    app.run_polling()
