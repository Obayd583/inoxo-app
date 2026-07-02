import telebot
from telebot import types
import subprocess
import os
import json
import time
from threading import Thread
from flask import Flask

# 🔐 المعطيات الأساسية ديالك
BOT_TOKEN = "8896904518:AAEkbtktyuz3AinMFKUvLspRfoMLqKwTdy8"
ADMIN_ID = 7141170679

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Python Stream Bot OK"

def run_flask():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

WHITELIST_FILE = 'allowed_users.json'

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_whitelist(data):
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def is_authorized(user_id):
    if user_id == ADMIN_ID:
        return True
    return user_id in load_whitelist()

active_processes = {}
user_states = {}

def get_user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🚀 إطلاق بث جديد', '📋 البثوث الشغالة')
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ عذراً، هاد البوت خاص ومصرح به لأشخاص محددين فقط تجريبياً.\n\n📞 لتفعيل حسابك، تواصل مع المطور:\n➡️ 0717962808")
        return
    bot.reply_to(message, "👋 مرحباً بك في نسخة Python المستقرة على GitHub Actions!", reply_markup=get_user_keyboard())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("👥 إدارة الـ Whitelist", callback_data="view_whitelist"))
    markup.row(types.InlineKeyboardButton("📺 البثوث الشغالة حالياً", callback_data="view_active_all"))
    bot.reply_to(message, "👑 **لوحة تحكم الـ Admin:**", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data == "view_whitelist":
        whitelist = load_whitelist()
        text = "👥 **قائمة الأشخاص المصرح لهم:**\n\n"
        if not whitelist:
            text += "_القائمة فارغة حالياً._\n"
        else:
            for uid in whitelist:
                text += f"👤 ID: `{uid}`\n"
        text += "\n✍️ **للإضافة أرسل:** `/add ID` \n❌ **للحذف أرسل:** `/remove ID`"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')
    
    elif call.data == "view_active_all":
        keys = list(active_processes.keys())
        if not keys:
            bot.send_message(call.message.chat.id, "ℹ️ لا توجد أي بثوث شغالة حالياً.")
            return
        text = "📺 **البثوث النشطة حالياً:**\n\n"
        for pid in keys:
            text += f"🆔 معرف البث: `{pid}`\n❌ لإيقافه: /stop_{pid}\n\n"
        bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text and (m.text.startswith('/add ') or m.text.startswith('/remove ')))
def handle_whitelist_commands(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    cmd = parts[0]
    try:
        target_id = int(parts[1])
    except:
        bot.reply_to(message, "❌ ID غير صحيح.")
        return
        
    whitelist = load_whitelist()
    if cmd == '/add':
        if target_id not in whitelist:
            whitelist.append(target_id)
            save_whitelist(whitelist)
            bot.reply_to(message, f"✅ تم إضافة الحساب للـ Whitelist: `{target_id}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "ℹ️ هاد الـ ID مضاف بالفعل.")
    elif cmd == '/remove':
        if target_id in whitelist:
            whitelist.remove(target_id)
            save_whitelist(whitelist)
            bot.reply_to(message, f"❌ تم حذف الحساب من الـ Whitelist: `{target_id}`", parse_mode='Markdown')
        else:
            bot.reply_to(message, "ℹ️ هاد الـ ID غير موجود ف القائمة.")

@bot.message_handler(func=lambda message: message.text == '🚀 إطلاق بث جديد')
def start_stream_flow(message):
    if not is_authorized(message.from_user.id):
        return
    bot.reply_to(message, "📥 أرسل الآن رابط الـ M3U8 أو MPD المباشر للمباراة:")
    user_states[message.from_user.id] = {'step': 'WAITING_STREAM_URL'}

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'WAITING_STREAM_URL')
def receive_stream_url(message):
    url = message.text.strip()
    if url.startswith('/') or not url.startswith('http'):
        return
    
    # تنظيف الماركداون بشكل متقدم
    if '](' in url:
        url = url.split('](')[1].split(')')[0].strip()
    url = url.replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()

    user_states[message.from_user.id] = {'step': 'WAITING_FB_URL', 'stream_url': url}
    bot.reply_to(message, "📥 صيفط رابط الـ RTMPS ومفتاح البث د الفيسبوك (في سطر واحد):")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'WAITING_FB_URL')
def receive_fb_url(message):
    user_id = message.from_user.id
    fb_url = message.text.strip()
    
    if '](' in fb_url:
        fb_url = fb_url.split('](')[0].strip()
    fb_url = fb_url.replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()

    if "rtmps://live-api-s.facebook.com:443/" in fb_url:
        fb_url = fb_url.replace("rtmps://live-api-s.facebook.com:443/", "rtmp://live-api-s.facebook.com:80/")

    if not fb_url.startswith('rtmp'):
        bot.reply_to(message, "❌ الرابط ماشي rtmp صحيح، عاود اضغط على زر الإطلاق وجرب مجدداً.")
        user_states.pop(user_id, None)
        return

    stream_url = user_states[user_id]['stream_url']
    user_states.pop(user_id, None)

    stream_id = str(int(time.time()))
    bot.reply_to(message, f"⏳ جاري إطلاق البث ذو المعرف {stream_id} على سيرفر GitHub Actions...")

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ffmpeg_args = [
        'ffmpeg',
        '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '15',
        '-user_agent', user_agent,
        '-headers', 'Referer: https://google.com/\r\n',
        '-re', '-i', stream_url,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-f', 'flv', fb_url
    ]

    try:
        process = subprocess.Popen(ffmpeg_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_processes[stream_id] = process
        bot.send_message(message.chat.id, f"✅ البث شغال الآن بنجاح!\n❌ لإيقافه أرسل: /stop_{stream_id}")
        
        def monitor():
            process.wait()
            if stream_id in active_processes:
                del active_processes[stream_id]
                try: bot.send_message(message.chat.id, f"ℹ️ البث ذو المعرف {stream_id} انتهى.")
                except: pass
        Thread(target=monitor).start()

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطأ ف تشغيل البث: {str(e)}")

@bot.message_handler(func=lambda message: message.text == '📋 البثوث الشغالة')
def list_active_streams(message):
    if not is_authorized(message.from_user.id):
        return
    keys = list(active_processes.keys())
    if not keys:
        bot.reply_to(message, "ℹ️ لا توجد أي بثوث شغالة حالياً.")
        return
    res = "📋 **بثوثك النشطة حالياً:**\n\n"
    for pid in keys:
        res += f"🆔 المعرف: `{pid}`\n❌ للإيقاف: /stop_{pid}\n\n"
    bot.reply_to(message, res, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text and message.text.startswith('/stop_'))
def stop_stream(message):
    if not is_authorized(message.from_user.id):
        return
    stream_id = message.text.replace('/stop_', '').strip()
    if stream_id in active_processes:
        try:
            active_processes[stream_id].kill()
            del active_processes[stream_id]
            bot.reply_to(message, "🛑 تم إيقاف البث بنجاح ف السيرفر.")
        except:
            bot.reply_to(message, "❌ فشل إيقاف البث.")
    else:
        bot.reply_to(message, "ℹ️ هاد البث غير موجود أو متوقف بالفعل.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    
    # محرك التكرار اللانهائي (Anti-Crash Loop) لبوت فايتون
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot crash prevented: {e}")
            time.sleep(5)
                      
