import telebot
from telebot import types
import requests
import sqlite3

# ==========================================
# ⚙️ البيانات الخاصة ببوتك
# ==========================================
BOT_TOKEN = "8735201198:AAEzVkTIYEcXCGid_3oPoRDnWbDwuynDRtM"
ADMIN_ID = 7243580458
ADMIN_USERNAME = "@zpjad"

# بيانات API المزود (Telekartsmm)
API_KEY = "86985c07344301b61cb287896b930faf"
API_URL = "https://telekartsmm.com/api/v2"

# نسبة الربح وسعر الصرف
PROFIT_MARGIN = 0.17  # نسبة ربح 17%
USDT_TO_YER = 1600    # سعر صرف الدولار مقابل الريال اليمني

# بيانات الحسابات المالية للدفع
PAYMENT_INFO = {
    "KURAIMI": "3153796539",
    "JAWALI_JEEB": "711189695",
    "USDT_TON": "UQBy73gVX513KLz4XsYR54vqlSP-rFEIxofh2Pk1GqS3AF0c"
}

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 🗄️ إعداد قاعدة البيانات المحلية (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("store_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance_usd REAL DEFAULT 0.0,
            balance_yer REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id):
    conn = sqlite3.connect("store_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance_usd, balance_yer FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance_usd, balance_yer) VALUES (?, 0.0, 0.0)", (user_id,))
        conn.commit()
        conn.close()
        return 0.0, 0.0
    conn.close()
    return row[0], row[1]

# ==========================================
# 🔌 الدوال البرمجية المربوطة بالسيرفر المزود
# ==========================================
def get_provider_services():
    """جلب الخدمات وتطبيق نسبة ربح 17%"""
    payload = {'key': API_KEY, 'action': 'services'}
    try:
        res = requests.post(API_URL, data=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"Error fetching services: {e}")
        return []

def calculate_price_with_profit(cost_usd):
    """إضافة 17% ربح للـ USD وتحويل السعر للريال اليمني"""
    final_usd = round(cost_usd * (1 + PROFIT_MARGIN), 3)
    final_yer = round(final_usd * USDT_TO_YER, 0)
    return final_usd, final_yer

# ==========================================
# 🤖 أوامر البوت والواجهة التفاعلية
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_services = types.InlineKeyboardButton("🛍️ الخدمات والمنتجات", callback_data="show_services")
    btn_balance = types.InlineKeyboardButton("💰 رصيدي ومحفظتي", callback_data="show_balance")
    btn_deposit = types.InlineKeyboardButton("💳 شحن الحساب", callback_data="deposit_info")
    btn_support = types.InlineKeyboardButton("👨‍💻 الدعم الفني", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")
    
    markup.add(btn_services, btn_balance)
    markup.add(btn_deposit, btn_support)
    
    text = (
        f"👋 أهلاً بك عزيزي **{message.from_user.first_name}** في المتجر التلقائي!\n\n"
        f"⚡ تنفيذ جميع الطلبات يتم بشكل آلي وفوري 24/7.\n"
        f"اختر من القائمة أدناه للبدء:"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    if call.data == "show_services":
        bot.answer_callback_query(call.id, "جاري تحميل قائمة الخدمات...")
        services = get_provider_services()
        
        if not services or (isinstance(services, dict) and "error" in services):
            bot.send_message(call.message.chat.id, "❌ تعذر جلب قائمة الخدمات من المزود حالياً، يرجى المحاولة لاحقاً.")
            return

        text = "📋 **قائمة بعض الخدمات المتاحة (شاملة نسبة الربح 17%):**\n\n"
        for s in services[:10]:
            cost = float(s.get('rate', 0)) / 1000
            usd_price, yer_price = calculate_price_with_profit(cost * 1000)
            text += f"🔹 **ID:** `{s.get('service')}` - {s.get('name')}\n"
            text += f"   💵 السعر لكل 1000: **${usd_price}** ({yer_price:,} ريال)\n\n"
        
        text += f"💡 للشراء أو تنفيذ طلب، تواصل مع الدعم {ADMIN_USERNAME}."
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "show_balance":
        usd_bal, yer_bal = get_user_balance(user_id)
        text = (
            f"👤 **بيانات حسابك:**\n"
            f"🆔 ID: `{user_id}`\n\n"
            f"💵 الرصيد بالدولار/USDT: **${usd_bal}**\n"
            f"🇾🇪 الرصيد بالريال اليمني: **{yer_bal:,} YER**"
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "deposit_info":
        text = (
            f"💳 **حسابات وشبكات الإيداع والشحن:**\n\n"
            f"🏦 **بنك الكريمي:** `{PAYMENT_INFO['KURAIMI']}`\n"
            f"📱 **جوالي / جيب:** `{PAYMENT_INFO['JAWALI_JEEB']}`\n"
            f"🌐 **USDT (شبكة TON):**\n`{PAYMENT_INFO['USDT_TON']}`\n\n"
            f"⚠️ بعد التحويل، يرجى إرسال صورة الإشعار مع الـ ID الخاص بك لـ {ADMIN_USERNAME} لتأكيد إضافة الرصيد فوراً."
        )
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ أنت لست مفوضاً لاستخدام لوحة التحكم.")
        return
    bot.reply_to(message, "⚙️ **مرحباً بك في لوحة تحكم الآدمن.**\nالبوت يعمل ومربوط بالـ API بنجاح بنسبة ربح 17%.")

# تشغيل البوت
if __name__ == "__main__":
    print("🚀 البوت يعمل الآن بنجاح...")
    bot.infinity_polling()
