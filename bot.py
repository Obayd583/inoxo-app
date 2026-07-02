import telebot
from telebot import types
import subprocess
import json
import os
import time
import threading
import requests
from flask import Flask

# 🔐 الإعدادات الأساسية بالتوكن والآي دي ديالك
BOT_TOKEN = "7948322050:AAETdCCpx2f_EMPnOYateYJcHm8q32tzXOk"
ADMIN_ID = 7141170679  # 👑 المالك الرئيسي

# 🔑 معطيات GitHub لإعادة تشغيل الحاوية أوتوماتيكياً بعد 5 ساعات
# حط التوكن ديالك هنا ديريكت بين القوسين "" أو خليه يقراه من الـ Secrets
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "ghp_YOUR_ACTUAL_GITHUB_TOKEN_HERE") 
REPO_OWNER = "Obayd533" 
REPO_NAME = "inoxo-app"  
WORKFLOW_ID = "run-bot.yml" 

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# توقيت إقلاع السيرفر الحالي لحساب الـ 5 ساعات
START_SERVER_TIME = time.time()

@app.route('/')
def home():
    return "Stream Engine Loop Active!"

def run_flask():
    try: app.run(host='0.0.0.0', port=8080)
    except: pass

WHITELIST_FILE = "allowed_users.json"
HISTORY_FILE = "streams_history.json"
CACHE_FILE = "stream_loop_cache.json"  # ملف سري لحفظ الروابط واسترجاعها بعد الـ 5 ساعات

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r") as f:
            try: return json.load(f)
            except: return []
    return []

def save_whitelist(data):
    with open(WHITELIST_FILE, "w") as f: json.dump(data, f, indent=4)

def save_to_history(user_id, stream_url):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: history = json.load(f)
            except: history = []
    history.append({"user_id": user_id, "url": stream_url, "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())})
    if len(history) > 200: history = history[-200:]
    with open(HISTORY_FILE, "w") as f: json.dump(history, f, indent=4)

# دالات حفظ واسترجاع البث التلقائي لكسر الـ 6 ساعات د جيتهاب
def save_stream_cache(stream_url, facebook_url, user_id):
    with open(CACHE_FILE, "w") as f:
        json.dump({"stream_url": stream_url, "facebook_url": facebook_url, "user_id": user_id, "start_time": START_SERVER_TIME}, f)

def load_stream_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f: return json.load(f)
        except: return None
    return None

def clear_stream_cache():
    if os.path.exists(CACHE_FILE):
        try: os.remove(CACHE_FILE)
        except: pass

active_processes = {}
restart_flags = {}
stream_owners = {}
stream_sources = {}
facebook_targets = {}

def is_authorized(user_id):
    if user_id == ADMIN_ID: return True
    return user_id in load_whitelist()

def get_user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🚀 إطلاق بث جديد"), types.KeyboardButton("📋 بثوثي الشغالة"))
    return markup

def trigger_github_action_loop():
    """تفرقيع حاوية جيتهاب القديمة وتشغيل واحدة جديدة كلياً في صمت"""
    if not GITHUB_TOKEN or "YOUR_ACTUAL_GITHUB_TOKEN" in GITHUB_TOKEN:
        print("GitHub Token is missing!")
        return
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"}
    try: requests.post(url, headers=headers, json=data)
    except: pass

# ⏱️ دالة الإشراف والتجديد الصامت كل 10 دقائق (600 ثانية) + مراقبة الـ 5 ساعات
def stream_timer_supervisor(stream_id, user_id):
    while restart_flags.get(stream_id, False):
        time.sleep(10) # فحص خفيف كل 10 ثواني
        
        # 1. نظام الـ 5 ساعات: كيطفي السيرفر الحالي ويشعل الجديد لراسو
        elapsed = time.time() - START_SERVER_TIME
        if elapsed >= 18000: # 5 ساعات بالضبط (5 * 3600)
            trigger_github_action_loop() # إطلاق الحاوية الجديدة أولاً
            try: bot.send_message(user_id, "🔄 **مرت 5 ساعات متواصلة:** جاري نقل البث تلقائياً لحاوية جديدة لضمان الـ 8 ساعات بدون انقطاع...")
            except: pass
            time.sleep(5)
            os._exit(0) # تدمير الحاوية الحالية فورا ف صمت

# ⏱️ دالة القتل والتجديد الصارم التلقائي كل 10 دقائق ف صمت
def silent_10min_loop_renewer(stream_id, user_id):
    while restart_flags.get(stream_id, False):
        time.sleep(600) # 10 دقائق بالضبط ف صمت
        if restart_flags.get(stream_id, False) and stream_id in active_processes:
            try:
                # قتل العملية الحالية في صمت لإجبار الـ Loop على تشغيل عملية FFmpeg جديدة منعشة
                active_processes[stream_id].terminate()
            except: pass

# 📺 محرك البث الـ Loop المعدل تيربو
def run_heavy_stream_loop(stream_id, user_id):
    restart_flags[stream_id] = True
    first_run = True

    # تشغيل مراقب الـ 5 ساعات
    supervisor_thread = threading.Thread(target=stream_timer_supervisor, args=(stream_id, user_id))
    supervisor_thread.daemon = True
    supervisor_thread.start()

    # تشغيل مجدد الـ 10 دقائق الصامت (بدون رسائل تليغرام)
    renew_thread = threading.Thread(target=silent_10min_loop_renewer, args=(stream_id, user_id))
    renew_thread.daemon = True
    renew_thread.start()

    while restart_flags.get(stream_id, False):
        stream_url = stream_sources.get(stream_id)
        facebook_url = facebook_targets.get(stream_id)
        if not stream_url or not facebook_url: break

        # تصفية شاملة للروابط من الماركداون والروابط المخفية
        if '](' in facebook_url: facebook_url = facebook_url.split('](')[0].replace('[', '').strip()
        facebook_url = facebook_url.replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()
        
        if "rtmps://live-api-s.facebook.com:443/" in facebook_url:
            facebook_url = facebook_url.replace("rtmps://live-api-s.facebook.com:443/", "rtmp://live-api-s.facebook.com:80/")

        ffmpeg_cmd = [
            'ffmpeg', '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '15',
            '-headers', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n',
            '-i', stream_url, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-f', 'flv', facebook_url
        ]
        try:
            if first_run:
                bot.send_message(user_id, f"🚀 تم إطلاق البث بنجاح!\n🆔 المعرف: `{stream_id}`\n\n⏱️ البث غايبقا شغال 8h مع تجديد صامت كل 10min.", parse_mode="Markdown")
                first_run = False
            
            # قراءة صامتة كليا من DEVNULL باش ما يتبلوكا ف حتى شي مرحلة
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            active_processes[stream_id] = process
            process.wait()
            
            if restart_flags.get(stream_id, False): 
                time.sleep(1)
                continue
            else: 
                break
        except Exception as e:
            time.sleep(2)
            continue

# لوحة التحكم
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_history = types.InlineKeyboardButton("🔗 الروابط المرسلة", callback_data="view_history")
    btn_active = types.InlineKeyboardButton("📺 اللايفات الشغالة", callback_data="view_active_all")
    btn_users = types.InlineKeyboardButton("👥 إدارة الـ Whitelist", callback_data="view_whitelist")
    markup.add(btn_history, btn_active, btn_users)
    bot.send_message(ADMIN_ID, "👑 **مرحباً بك في لوحة تحكم المالك الرئيسي:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.from_user.id != ADMIN_ID: return
    if call.data == "view_history":
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f: history = json.load(f)
            if not history: bot.send_message(ADMIN_ID, "ℹ️ السجل فارغ.")
            else:
                text = "📋 **آخر الروابط المرسلة:**\n\n"
                for idx, item in enumerate(reversed(history[-15:])): text += f"{idx+1}. 👤 `{item['user_id']}`\n🔗 `{item['url']}`\n\n"
                bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    elif call.data == "view_active_all":
        if not active_processes or not any(restart_flags.values()): bot.send_message(ADMIN_ID, "ℹ️ لا توجد بثوث شغالة حالياً.")
        else:
            text = "📺 **جميع البثوث الشغالة:**\n\n"
            for s_id, is_running in restart_flags.items():
                if is_running: text += f"🆔 `{s_id}` | 👤 `{stream_owners.get(s_id)}`\n❌ لإيقافه: /stop_{s_id}\n\n"
            bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    elif call.data == "view_whitelist":
        whitelist = load_whitelist()
        text = "👥 **قائمة الـ Whitelist الحالية:**\n\n"
        for uid in whitelist: text += f"👤 المستخدم: `{uid}`\n"
        text += "\n✍️ للإضافة: `/add ID` \n❌ لحذف: `/remove ID`"
        bot.send_message(ADMIN_ID, text, parse_mode="Markdown")

@bot.message_handler(commands=['add', 'remove'])
def admin_text_commands(message):
    if message.from_user.id != ADMIN_ID: return
    command = message.text.split()
    if len(command) < 2: return
    try:
        target_id = int(command[1])
        whitelist = load_whitelist()
        if command[0] == '/add' and target_id not in whitelist:
            whitelist.append(target_id)
            save_whitelist(whitelist)
            bot.reply_to(message, f"✅ تم إضافة `{target_id}`.")
        elif command[0] == '/remove' and target_id in whitelist:
            whitelist.remove(target_id)
            save_whitelist(whitelist)
            bot.reply_to(message, f"❌ تم إزالة `{target_id}`.")
    except: pass

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not is_authorized(message.from_user.id): return
    bot.send_message(message.from_user.id, "👋 مرحباً بك في بوت البثوث اللانهائية الاحترافي الموزون!\nاستخدم الأزرار التفاعلية أسفله:", reply_markup=get_user_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text_actions(message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    text = message.text.strip()

    if text.startswith('/stop_') or text == '/stop':
        stream_id = text.replace('/stop_', '') if text.startswith('/stop_') else "LIVE_STREAM"
        clear_stream_cache() # مسح الذاكرة المؤقتة لمنع الإعادة التلقائية
        restart_flags[stream_id] = False
        try: active_processes[stream_id].terminate()
        except: pass
        bot.reply_to(message, f"🛑 تم إيقاف البث كلياً وعاد النظام للوضعية العادية.")
        return

    if text == "🚀 إطلاق بث جديد":
        msg = bot.reply_to(message, "📥 أرسل الآن رابط الـ **MPD** أو **M3U8** المباشر:")
        bot.register_next_step_handler(msg, process_stream_url)
    elif text == "📋 بثوثي الشغالة":
        if os.path.exists(CACHE_FILE):
            bot.reply_to(message, "📋 **لديك بث نشط شغال تيربو ومحمي حالياً ف الخلفية.**\n❌ لإيقافه كلياً أرسل: `/stop`", parse_mode="Markdown")
        else:
            bot.reply_to(message, "ℹ️ ليس لديك بثوث شغالة حالياً.")

def process_stream_url(message):
    if not is_authorized(message.from_user.id): return
    stream_url = message.text.strip()
    if stream_url.startswith('/') or not stream_url.startswith('http'): return
    msg = bot.reply_to(message, "📥 صيفط رابط **RTMPS ومفتاح البث د الفيسبوك** مجموعين ف سطر واحد:")
    bot.register_next_step_handler(msg, process_facebook_url, stream_url)

def process_facebook_url(message, stream_url):
    if not is_authorized(message.from_user.id): return
    facebook_url = message.text.strip()
    if not facebook_url.startswith('rtmp'): return

    stream_id = "LIVE_STREAM"
    stream_owners[stream_id] = message.from_user.id
    stream_sources[stream_id] = stream_url
    facebook_targets[stream_id] = facebook_url

    # حفظ الروابط ف ملف الكاش باش يلا طفا السيرفر ف 5 سوايع يلقاهم واجدين ويكمل اللايف
    save_stream_cache(stream_url, facebook_url, message.from_user.id)
    save_to_history(message.from_user.id, stream_url)

    threading.Thread(target=run_heavy_stream_loop, args=(stream_id, message.from_user.id), daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Running Pro Clean Polling Engine...")
    
    # 💥 فحص الإقلاع الذكي: إيلا السيرفر طفا وشعل لراسو ف جيتهاب ولقا لايف باقيلو الوقت، كيكمل البث ديريكت لراسو!
    cached_data = load_stream_cache()
    if cached_data:
        s_id = "LIVE_STREAM"
        stream_sources[s_id] = cached_data["stream_url"]
        facebook_targets[s_id] = cached_data["facebook_url"]
        stream_owners[s_id] = cached_data["user_id"]
        # إحياء محرك الـ Loop تلقائياً
        threading.Thread(target=run_heavy_stream_loop, args=(s_id, cached_data["user_id"]), daemon=True).start()
        try: bot.send_message(cached_data["user_id"], "🟢 **تم تجديد جلسة السيرفر بنجاح:** البث شغال دابا ومستمر ف الحاوية الجديدة!")
        except: pass

    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True, timeout=120)
        except: time.sleep(3)
                                                 
