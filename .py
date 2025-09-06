import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# =============================
# تنظیمات
# ================= # 🔹 جایگزین============
TOKEN = "8323475984:AAFSKKmGyHucoYMapCD0QdLACAyKCtJzR2g"      
ADMIN_ID = 6551138167              # 🔹 آیدی عددی مدیر

# مراحل گفتگو
NAME, PHONE, CATEGORY, PRODUCT, COLOR_SIZE, DESCRIPTION = range(6)

# =============================
# دیتابیس
# =============================
def init_db():
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    category TEXT,
                    product TEXT,
                    color_size TEXT,
                    description TEXT
                )""")
    conn.commit()
    conn.close()

# =============================
# استارت ربات
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 سلام! لطفاً نام و نام خانوادگی خود را وارد کنید:")
    return NAME

# مرحله ۱: نام
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📞 لطفاً شماره تلفن خود را وارد کنید:")
    return PHONE

# مرحله ۲: شماره
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    keyboard = [["تابلوسازی", "چاپ"]]
    await update.message.reply_text(
        "📂 لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY

# مرحله ۳: دسته‌بندی
async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("🔢 لطفاً کد محصول را وارد کنید:")
    return PRODUCT

# مرحله ۴: کد محصول
async def get_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["product"] = update.message.text
    await update.message.reply_text("🎨 لطفاً رنگ و اندازه مورد نظر را بنویسید:")
    return COLOR_SIZE

# مرحله ۵: رنگ و اندازه
async def get_color_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["color_size"] = update.message.text
    await update.message.reply_text("📝 لطفاً توضیح دقیق و کاربرد تابلو یا چاپ را بنویسید:")
    return DESCRIPTION

# مرحله ۶: توضیحات و ثبت
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text

    # ذخیره در دیتابیس
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("INSERT INTO orders (name, phone, category, product, color_size, description) VALUES (?, ?, ?, ?, ?, ?)",
              (context.user_data["name"], context.user_data["phone"], context.user_data["category"],
               context.user_data["product"], context.user_data["color_size"], context.user_data["description"]))
    conn.commit()
    conn.close()

    # ارسال به مدیر
    order_text = f"""
📦 سفارش جدید دریافت شد:

👤 نام: {context.user_data["name"]}
📞 تلفن: {context.user_data["phone"]}
📂 دسته‌بندی: {context.user_data["category"]}
🔢 کد محصول: {context.user_data["product"]}
🎨 رنگ و اندازه: {context.user_data["color_size"]}
📝 توضیحات: {context.user_data["description"]}
"""
    await context.bot.send_message(chat_id=ADMIN_ID, text=order_text)

    # پیام به مشتری
    await update.message.reply_text(
        "✅ سفارش شما ثبت شد.\n"
        "هنگامی که آماده شود به شما اطلاع داده می‌شود.\n\n"
        "☎ در صورت نیاز به مشاوره تماس بگیرید:\n"
        "تابلوسازی: 09121785867\n"
        "چاپ: 09125717919"
    )

    return ConversationHandler.END

# جستجو در سفارش‌ها
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ لطفاً نام مشتری را بعد از دستور وارد کنید. مثال:\n/search علی احمدی")
        return

    name = " ".join(context.args)
    conn = sqlite3.connect("orders.db")
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE name LIKE ?", (f"%{name}%",))
    results = c.fetchall()
    conn.close()

    if results:
        msg = "📋 سفارش‌های یافت‌شده:\n\n"
        for r in results:
            msg += f"👤 {r[1]} | 📞 {r[2]} | {r[3]} - {r[4]} | 🎨 {r[5]} | 📝 {r[6]}\n\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("❌ هیچ سفارشی با این نام پیدا نشد.")

# کنسل
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛔ سفارش لغو شد.")
    return ConversationHandler.END

# =============================
# ران کردن ربات
# =============================
def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product)],
            COLOR_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_color_size)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("search", search))

    print("🤖 Bot is running on Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
