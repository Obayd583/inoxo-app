import telebot
from telebot import types
import subprocess
import json
import os
import time
import threading
import requests
from flask import Flask

# 🔐 الإعدادات الأساسية بالتوكن الجديد والآي دي ديالك
BOT_TOKEN = "8736155204:AAEUYBRonEzBHJkUhqn9nR4iNAF50NPlv74"
ADMIN_ID = 7141170679  # 👑 المالك الرئيسي

# 🔑 معطيات GitHub لإعادة تشغيل الحاوية أوتوماتيكياً بعد 5 ساعات
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "ghp_YOUR_ACTUAL_GITHUB_TOKEN_HERE") 
REPO_OWNER = "Obayd583" 
REPO_NAME = "inoxo-app"  
WORKFLOW_ID = "run-bot.yml"  

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

START_SERVER_TIME = time.time()

@app.route('/')
def home():
    return "🚀 Turbo Stream Engine Active!"

def run_flask():
    try: app.run(host='0.0.0.0', port=8080)
    except: pass

WHITELIST_FILE = "allowed_users.json"
CACHE_FILE = "stream_loop_cache.json"

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_whitelist(data):
    with open(WHITELIST_FILE, "w") as f: json.dump(data, f, indent=4)

def save_stream_cache(stream_id, name, stream_url, facebook_url, user_id):
    cache = load_all_cache()
    cache[stream_id] = {
        "name": name,
        "stream_url": stream_url,
        "facebook_url": facebook_url,
        "user_id": user_id,
        "start_time": START_SERVER_TIME
    }
    with open(CACHE_FILE, "w") as f: json.dump(cache, f, indent=4)

def load_all_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def remove_from_cache(stream_id):
    cache = load_all_cache()
    if stream_id in cache:
        del cache[stream_id]
        with open(CACHE_FILE, "w") as f: json.dump(cache, f, indent=4)

active_processes = {}
restart_flags = {}
stream_owners = {}
stream_sources = {}
facebook_targets = {}
stream_names = {}

def is_authorized(user_id):
    if user_id == ADMIN_ID: return True
    return user_id in load_whitelist()

def get_user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🚀 إطلاق بث جديد"))
    markup.row(types.KeyboardButton("📋 بثوثي الشغالة"), types.KeyboardButton("❌ إيقاف بث محدد"))
    return markup

def trigger_github_action_loop():
    if not GITHUB_TOKEN or "YOUR_ACTUAL_GITHUB_TOKEN" in GITHUB_TOKEN: return
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try: requests.post(url, headers=headers, json={"ref": "main"})
    except: pass

# ⏱️ مراقبة الـ 5 ساعات لنقل الجلسة
def stream_timer_supervisor(stream_id, user_id):
    while restart_flags.get(stream_id, False):
        time.sleep(10)
        elapsed = time.time() - START_SERVER_TIME
        if elapsed >= 18000:  # 5 ساعات
            trigger_github_action_loop()
            try: bot.send_message(user_id, f"🔄 مرت 5 ساعات! جاري نقل البث المسمى `{stream_names.get(stream_id)}` تلقائياً لحاوية جديدة...")
            except: pass
            time.sleep(5)
            os._exit(0)

# ⏱️ التجديد التلقائي الصامت كل 10 دقائق
def silent_10min_loop_renewer(stream_id, user_id):
    while restart_flags.get(stream_id, False):
        time.sleep(600)  
        if restart_flags.get(stream_id, False) and stream_id in active_processes:
            try: active_processes[stream_id].terminate()
            except: pass

# 📺 محرك البث الـ Loop الصارم والآمن
def run_heavy_stream_loop(stream_id, user_id):
    restart_flags[stream_id] = True
    
    threading.Thread(target=stream_timer_supervisor, args=(stream_id, user_id), daemon=True).start()
    threading.Thread(target=silent_10min_loop_renewer, args=(stream_id, user_id), daemon=True).start()

    while restart_flags.get(stream_id, False):
        stream_url = stream_sources.get(stream_id)
        facebook_url = facebook_targets.get(stream_id)
        if not stream_url or not facebook_url: break

        # [تعديل مهم] تم إيقاف تغيير rtmps إلى rtmp باش يدوز الرابط الصحيح ديالك نيشان بلا مشاكل!
        ffmpeg_cmd = [
            'ffmpeg', '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '15',
            '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n',
            '-i', stream_url, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-f', 'flv', facebook_url
        ]
        try:
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            active_processes[stream_id] = process
            process.wait()
            if restart_flags.get(stream_id, False):
                time.sleep(1)
                continue
            else: break
        except:
            time.sleep(2)
            continue

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not is_authorized(message.from_user.id): return
    bot.send_message(message.from_user.id, "🟢 **مرحباً بك في النسخة الفولاذية والنهائية!**\n\nكلشي واجد دابا والمكتبات مضبوطة. استخدم الأزرار التفاعلية أسفله:", reply_markup=get_user_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text_actions(message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    text = message.text.strip()

    if text == "🚀 إطلاق بث جديد":
        msg = bot.reply_to(message, "✍️ أولاً، صيفط **سمية واضحة لهاد البث** (مثال: ماتش الماط):")
        bot.register_next_step_handler(msg, process_get_name)
        
    elif text == "📋 بثوثي الشغالة":
        cache = load_all_cache()
        user_streams = {s_id: data for s_id, data in cache.items() if data["user_id"] == user_id}
        if not user_streams:
            bot.reply_to(message, "ℹ️ لا توجد أي بثوث شغالة حالياً.")
            return
        res = "📺 **بثوثك الشغالة حالياً تيربو:**\n\n"
        for s_id, data in user_streams.items():
            res += f"📌 **الاسم:** {data['name']}\n🆔 المعرف: `{s_id}`\n⏱️ نظام التجديد التلقائي شغال ف الخلفية.\n\n"
        bot.reply_to(message, res, parse_mode="Markdown")

    elif text == "❌ إيقاف بث محدد":
        cache = load_all_cache()
        user_streams = {s_id: data for s_id, data in cache.items() if data["user_id"] == user_id}
        if not user_streams:
            bot.reply_to(message, "ℹ️ ليس لديك أي بث شغال لإيقافه.")
            return
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        for s_id, data in user_streams.items():
            btn = types.InlineKeyboardButton(f"🟢 إيقاف: {data['name']}", callback_data=f"stop_{s_id}")
            markup.add(btn)
        bot.send_message(user_id, "👇 اختر البث لي بغيتي تطفي من القائمة التفاعلية:", reply_markup=markup)

def process_get_name(message):
    name = message.text.strip()
    msg = bot.reply_to(message, "📥 دابا أرسل رابط الـ **MPD** أو **M3U8** المباشر:")
    bot.register_next_step_handler(msg, process_stream_url, name)

def process_stream_url(message, name):
    stream_url = message.text.strip()
    if stream_url.startswith('/') or not stream_url.startswith('http'): return
    msg = bot.reply_to(message, "📥 دابا صيفط رابط **RTMPS ومفتاح البث د الفيسبوك** كامل ف سطر واحد:")
    bot.register_next_step_handler(msg, process_facebook_url, name, stream_url)

def process_facebook_url(message, name, stream_url):
    facebook_url = message.text.strip()
    if not facebook_url.startswith('rtmp') and not facebook_url.startswith('rtmps'): return

    stream_id = str(int(time.time() * 1000))
    stream_owners[stream_id] = message.from_user.id
    stream_sources[stream_id] = stream_url
    facebook_targets[stream_id] = facebook_url
    stream_names[stream_id] = name

    save_stream_cache(stream_id, name, stream_url, facebook_url, message.from_user.id)

    threading.Thread(target=run_heavy_stream_loop, args=(stream_id, message.from_user.id), daemon=True).start()
    bot.reply_to(message, f"🚀 **تم إطلاق البث بنجاح!**\n📌 الاسم: `{name}`\n\n⏱️ البث شغال دابا وتجديد تلقائي صامت خدام ف الخلفية.", parse_mode="Markdown", reply_markup=get_user_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def callback_stop_stream(call):
    user_id = call.from_user.id
    stream_id = call.data.replace("stop_", "")
    
    cache = load_all_cache()
    if stream_id in cache:
        restart_flags[stream_id] = False
        try: active_processes[stream_id].terminate()
        except: pass
        remove_from_cache(stream_id)
        bot.answer_callback_query(call.id, "🛑 تم إيقاف البث")
        bot.edit_message_text(f"✅ تم إيقاف البث المسمى `{cache[stream_id]['name']}` بنجاح وتطهير الحاوية.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "⚠️ هاد البث متوقف مسبقاً.")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Running Clean Polling Engine...")
    
    cached_all = load_all_cache()
    if cached_all:
        for s_id, data in cached_all.items():
            stream_sources[s_id] = data["stream_url"]
            facebook_targets[s_id] = data["facebook_url"]
            stream_owners[s_id] = data["user_id"]
            stream_names[s_id] = data["name"]
            threading.Thread(target=run_heavy_stream_loop, args=(s_id, data["user_id"]), daemon=True).start()
            try: bot.send_message(data["user_id"], f"🟢 **تجديد الجلسة:** البث المسمى `{data['name']}` كمل لراسو ف السيرفر الجديد!")
            except: pass

    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, timeout=120)
        except: time.sleep(3)
