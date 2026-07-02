import telebot
from telebot import types
import subprocess
import os
import json
import time
import requests
from threading import Thread
from flask import Flask

# 🔐 المعطيات الأساسية
BOT_TOKEN = "8896904518:AAEkbtktyuz3AinMFKUvLspRfoMLqKwTdy8"
ADMIN_ID = 7141170679

# 🔑 معطيات GitHub لإعادة تشغيل الـ Workflow لراسو (خريطة الـ 5 ساعات)
GITHUB_TOKEN = os.environ.get("GH_TOKEN", "") # غادي نوريكم كيفاش تزيدوه ف السيكريتس ولا تحطو التوكن ديالك هنا ديريكت
REPO_OWNER = "Obayd533" # اسم حسابك ف جيتهاب
REPO_NAME = "inoxo-app"  # اسم المستودع ديالك
WORKFLOW_ID = "run-bot.yml" # اسم ملف الـ yaml

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Turbo Live Loop Engine Active"

def run_flask():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

WHITELIST_FILE = 'allowed_users.json'

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, 'r') as f: return json.load(f)
        except: return []
    return []

def save_whitelist(data):
    with open(WHITELIST_FILE, 'w') as f: json.dump(data, f, indent=4)

def is_authorized(user_id):
    if user_id == ADMIN_ID: return True
    return user_id in load_whitelist()

active_processes = {}
user_states = {}
start_time = time.time() # توقيت بداية تشغيل السيرفر الحالي

# حفظ الروابط الحالية ف ملف مؤقت باش يلا السيرفر طفا وشعل لراسو يلقاهم واجدين ويكمل البث تلقائياً
CACHE_FILE = "stream_cache.json"

def save_stream_cache(stream_url, fb_url):
    with open(CACHE_FILE, 'w') as f:
        json.dump({"stream_url": stream_url, "fb_url": fb_url}, f)

def load_stream_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f: return json.load(f)
        except: return None
    return None

def clear_stream_cache():
    if os.path.exists(CACHE_FILE):
        try: os.remove(CACHE_FILE)
        except: pass

def trigger_github_restart():
    """هاد الدالة كتمشي لـ GitHub وكتطفي السيرفر الحالي وتشعل واحد جديد أوتوماتيكياً فاش كتوصل 5 سوايع"""
    if not GITHUB_TOKEN:
        print("GitHub Token is missing! cannot auto-restart workflow.")
        return
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"} # أو اسم الـ branch ديالك (غالباً main)
    try:
        requests.post(url, headers=headers, json=data)
        print("🚀 GitHub Loop triggered successfully!")
    except Exception as e:
        print(f"Error triggering GitHub loop: {e}")

def get_user_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🚀 إطلاق بث جديد', '📋 البثوث الشغالة')
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_authorized(message.from_user.id): return
    bot.reply_to(message, "👋 مرحباً بك في نسخة البث الصامت اللانهائي (8 ساعات متواصلة)!", reply_markup=get_user_keyboard())

@bot.message_handler(func=lambda message: message.text == '🚀 إطلاق بث جديد')
def start_stream_flow(message):
    if not is_authorized(message.from_user.id): return
    bot.reply_to(message, "📥 أرسل الآن رابط الـ M3U8 أو MPD المباشر للمباراة:")
    user_states[message.from_user.id] = {'step': 'WAITING_STREAM_URL'}

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'WAITING_STREAM_URL')
def receive_stream_url(message):
    url = message.text.strip()
    if url.startswith('/') or not url.startswith('http'): return
    
    if '](' in url: url = url.split('](')[1].split(')')[0].strip()
    url = url.replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()

    user_states[message.from_user.id] = {'step': 'WAITING_FB_URL', 'stream_url': url}
    bot.reply_to(message, "📥 صيفط رابط الـ RTMPS ومفتاح البث د الفيسبوك (في سطر واحد):")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('step') == 'WAITING_FB_URL')
def receive_fb_url(message):
    user_id = message.from_user.id
    fb_url = message.text.strip()
    
    if '](' in fb_url: fb_url = fb_url.split('](')[0].strip()
    fb_url = fb_url.replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()

    if "rtmps://live-api-s.facebook.com:443/" in fb_url:
        fb_url = fb_url.replace("rtmps://live-api-s.facebook.com:443/", "rtmp://live-api-s.facebook.com:80/")

    if not fb_url.startswith('rtmp'):
        bot.reply_to(message, "❌ الرابط غير صحيح.")
        user_states.pop(user_id, None)
        return

    stream_url = user_states[user_id]['stream_url']
    user_states.pop(user_id, None)

    save_stream_cache(stream_url, fb_url)
    bot.reply_to(message, "✅ تـم حـفـظ الـروابـط! جـاري إطـلاق الـبـث الـصامـت وتـفـعـيـل نـظـام الـتـجـديـد الـتـلـقـائـي كـل 10 دقـائـق...")
    
    # إطلاق البث الأول
    start_ffmpeg_core(stream_url, fb_url, message.chat.id)

def start_ffmpeg_core(stream_url, fb_url, chat_id):
    stream_id = "LIVE_STREAM"
    
    # إيقاف أي بث قديم شغال أولاً لمنع تداخل العمليات
    if stream_id in active_processes:
        try: active_processes[stream_id].kill()
        except: pass

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    headers = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nOrigin: https://snrtlive.ma\r\nReferer: https://snrtlive.ma/\r\n"

    ffmpeg_args = [
        'ffmpeg',
        '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '30',
        '-user_agent', user_agent,
        '-headers', headers,
        '-re', '-i', stream_url,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-f', 'flv', fb_url
    ]

    try:
        process = subprocess.Popen(ffmpeg_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        active_processes[stream_id] = process
        
        # مراقبة الانتهاء الطبيعي للمباراة
        def monitor():
            process.wait()
        Thread(target=monitor).start()
    except Exception as e:
        print(f"FFmpeg launch error: {e}")

def auto_restart_and_loop_manager():
    """المحرك السري: كيدير تجديد تلقائي ف الصمت كل 10 دقائق، وفاش كتوصل 5 سوايع كيطفي ويشعل راسه ف جيتهاب"""
    global start_time
    chat_id = ADMIN_ID # إرسال التقارير الأساسية للآدمين فقط في الحالات القصوى
    
    while True:
        time.sleep(10) # فحص مستمر كل 10 ثواني
        current_elapsed = time.time() - start_time
        
        # 1. نظام الـ 5 ساعات: إعادة تشغيل الـ Workflow كاملا في GitHub لكسر قيود الـ 6 ساعات
        if current_elapsed >= 18000: # 5 ساعات بالثواني (5 * 3600)
            cache = load_stream_cache()
            if cache:
                # إطلاق سيرفر جديد قبل ما يطفا هادا
                trigger_github_restart()
                try: bot.send_message(chat_id, "🔄 مرت 5 ساعات! تم نقل البث تلقائياً إلى حاوية GitHub جديدة وضمان استمرار الـ 8 ساعات بنجاح وبدون انقطاع.")
                except: pass
                time.sleep(10)
                os._exit(0) # إنهاء العملية الحالية بسلام
        
        # 2. نظام التجديد التلقائي كل 10 دقائق (600 ثانية) ف صمت وبلا ميساجات
        # كيعاود يطلق الـ FFmpeg باش يضمن أن السيرفر د الفيسبوك مايموتش واللايف يبقا شغال تيربو
        cache = load_stream_cache()
        if cache:
            stream_id = "LIVE_STREAM"
            # إذا دازت 10 دقائق على تشغيل الـ FFmpeg الحالي أو إيلا طاح لراسه، كنعاودو نجددوه
            if stream_id in active_processes:
                # التحقق هل دازت 10 دقائق (هنا نقوم بالتجديد لإنعاش الاتصال بالفيسبوك)
                # لتجنب كثرة القتل، سنترك النظام يجدد كل 10 دقائق عبر قتل العملية الحالية وإعادة تشغيلها صامتاً
                pass 

def silent_timer_restarter():
    """تجديد صامت صارم كل 10 دقائق دقيقة بدقيقة"""
    while True:
        time.sleep(600) # 10 دقائق بالضبط
        cache = load_stream_cache()
        if cache:
            # إعادة إنعاش الـ FFmpeg في صمت وبدون إرسال أي رسالة تليغرام برزاطة
            start_ffmpeg_core(cache["stream_url"], cache["fb_url"], ADMIN_ID)

@bot.message_handler(func=lambda message: message.text == '📋 البثوث الشغالة')
def list_active_streams(message):
    if not is_authorized(message.from_user.id): return
    cache = load_stream_cache()
    if cache:
        elapsed = int(time.time() - start_time)
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        bot.reply_to(message, f"📋 **البث التيربو الصامت شغال حالياً:**\n⏱️ مدة التشغيل الحالية: {hours} ساعة و {minutes} دقيقة.\n🔄 نظام التجديد التلقائي (10min) شغال ف الخلفية.\n❌ لإيقاف البث كلياً: /stop_live")
    else:
        bot.reply_to(message, "ℹ️ لا توجد أي بثوث شغالة حالياً.")

@bot.message_handler(commands=['stop_live', 'stop'])
def stop_all_stream(message):
    if not is_authorized(message.from_user.id): return
    clear_stream_cache()
    stream_id = "LIVE_STREAM"
    if stream_id in active_processes:
        try:
            active_processes[stream_id].kill()
            del active_processes[stream_id]
        except: pass
    bot.reply_to(message, "🛑 تم إيقاف البث وحذف الروابط من الذاكرة التلقائية بنجاح.")

if __name__ == '__main__':
    # تشغيل سيرفر الويب الوهمي لحماية الحاوية
    Thread(target=run_flask).start()
    
    # تشغيل محرك إدارة الوقت والـ 5 ساعات
    Thread(target=auto_restart_and_loop_manager).start()
    
    # تشغيل محرك التجديد الصامت كل 10 دقائق
    Thread(target=silent_timer_restarter).start()
    
    # التحقق عند إقلاع السيرفر (إيلا كان جاي من ريستارت د 5 ساعات يكمل البث لراسو)
    auto_cache = load_stream_cache()
    if auto_cache:
        start_ffmpeg_core(auto_cache["stream_url"], auto_cache["fb_url"], ADMIN_ID)
    
    while True:
        try: bot.polling(none_stop=True, timeout=60)
        except: time.sleep(5)
