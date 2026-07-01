const { Telegraf, Markup } = require('telegraf');
const { spawn } = require('child_process');
const express = require('express');
const fs = require('fs');
const path = require('path');

// 🔐 [تعديل] حط المعطيات ديالك هنا
const BOT_TOKEN = "8896904518:AAEkbtktyuz3AinMFKUvLspRfoMLqKwTdy8"; 
const ADMIN_ID = 7141170679; 

const bot = new Telegraf(BOT_TOKEN);
const app = express();
app.get('/', (req, res) => res.send('System OK'));
app.listen(process.env.PORT || 8080);

const WHITELIST_FILE = path.join(__dirname, 'allowed_users.json');

// دالة لجلب لستة د الناس المصرح لهم
function loadWhitelist() {
    if (fs.existsSync(WHITELIST_FILE)) {
        try { return JSON.parse(fs.readFileSync(WHITELIST_FILE)); } catch (e) { return []; }
    }
    return [];
}

// دالة لحفظ لستة د الناس
function saveWhitelist(data) {
    fs.writeFileSync(WHITELIST_FILE, JSON.stringify(data, null, 4));
}

// دالة كتفحص واش الشخص مصرح ليه ولا لا
function isAuthorized(userId) {
    if (userId === ADMIN_ID) return true;
    return loadWhitelist().includes(userId);
}

let activeProcesses = {};

const getUserKeyboard = () => Markup.keyboard([['🚀 إطلاق بث جديد', '📋 البثوث الشغالة']]).resize();

// 🛑 استقبال أي شخص جديد غريب
bot.start((ctx) => {
    const userId = ctx.from.id;
    
    if (!isAuthorized(userId)) {
        return ctx.reply(`❌ عذراً، هاد البوت خاص ومصرح به لأشخاص محددين فقط تجريبياً.\n\n📞 للمزيد من المعلومات أو لتفعيل حسابك، تواصل مع المطور مباشرة:\n➡️ 0717962808`);
    }
    
    ctx.reply('👋 مرحباً بك في بوت GitHub التيربو للبث اللانهائي الآمن!', getUserKeyboard());
});

// 👑 لوحة تحكم الـ Admin الرئيسي
bot.command('admin', (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    ctx.reply('👑 **لوحة تحكم الـ Admin المفرقعة:**', {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([
            [Markup.button.callback('👥 إدارة الـ Whitelist', 'view_whitelist')],
            [Markup.button.callback('📺 البثوث الشغالة حالياً', 'view_active_all')]
        ])
    });
});

bot.action('view_whitelist', (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    const whitelist = loadWhitelist();
    let text = "👥 **قائمة الأشخاص المصرح لهم بالتجريب:**\n\n";
    if (whitelist.length === 0) {
        text += "_القائمة فارغة حالياً._\n";
    } else {
        whitelist.forEach(uid => { text += `👤 ID: \`${uid}\`\n`; });
    }
    text += "\n✍️ **للإضافة أرسل:** `/add ID` \n❌ **للحذف أرسل:** `/remove ID`";
    ctx.reply(text, { parse_mode: 'Markdown' });
});

bot.action('view_active_all', (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    const keys = Object.keys(activeProcesses);
    if (keys.length === 0) return ctx.reply('ℹ️ لا توجد أي بثوث شغالة حالياً ف السيرفر.');
    let text = "📺 **البثوث النشطة حالياً:**\n\n";
    keys.forEach(id => { text += `🆔 معرف البث: \`${id}\`\n❌ لإيقافه فوراً: /stop_${id}\n\n`; });
    ctx.reply(text, { parse_mode: 'Markdown' });
});

// ميكانيزم إضافة أو حذف الأشخاص عبر الـ ID
bot.hears(/^\/(add|remove) (\d+)/, (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    const cmd = ctx.match[1];
    const targetId = parseInt(ctx.match[2]);
    let whitelist = loadWhitelist();

    if (cmd === 'add') {
        if (!whitelist.includes(targetId)) {
            whitelist.push(targetId);
            saveWhitelist(whitelist);
            ctx.reply(`✅ تم تفعيل الحساب وإضافته بنجاح للـ Whitelist: \`${targetId}\``, { parse_mode: 'Markdown' });
        } else {
            ctx.reply("ℹ️ هاد الـ ID مضاف بالفعل من قبل.");
        }
    } else if (cmd === 'remove') {
        if (whitelist.includes(targetId)) {
            whitelist = whitelist.filter(id => id !== targetId);
            saveWhitelist(whitelist);
            ctx.reply(`❌ تم حذف الحساب وحظره من الـ Whitelist: \`${targetId}\``, { parse_mode: 'Markdown' });
        } else {
            ctx.reply("ℹ️ هاد الـ ID غير موجود ف القائمة أصلاً.");
        }
    }
});

// إطلاق البثوث (فقط للمصرح لهم)
bot.hears('🚀 إطلاق بث جديد', (ctx) => {
    if (!isAuthorized(ctx.from.id)) return;
    ctx.reply('📥 أرسل الآن رابط الـ M3U8 أو MPD المباشر:');
    bot.on('text', handleStreamUrl);
});

async function handleStreamUrl(ctx) {
    if (!isAuthorized(ctx.from.id)) return;
    const streamUrl = ctx.message.text.trim();
    if (streamUrl.startsWith('/') || !streamUrl.startsWith('http')) return;

    ctx.reply('📥 صيفط رابط الـ RTMPS ومفتاح البث د الفيسبوك (في سطر واحد):');
    bot.off('text', handleStreamUrl); 

    bot.on('text', async (ctxNext) => {
        if (!isAuthorized(ctxNext.from.id)) return;
        const facebookUrl = ctxNext.message.text.trim();
        if (!facebookUrl.startsWith('rtmp')) return;

        const streamId = String(Date.now());
        ctxNext.reply(`⏳ جاري إطلاق البث ذو المعرف: ${streamId} في الخلفية...`);

        const userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
        const ffmpegArgs = [
            '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '15',
            '-user_agent', userAgent,
            '-headers', 'Referer: https://google.com/\r\n',
            '-re', '-i', streamUrl, 
            '-c', 'copy', 
            '-f', 'flv', facebookUrl
        ];

        const process = spawn('ffmpeg', ffmpegArgs);
        activeProcesses[streamId] = process;

        ctxNext.reply(`✅ البث شغال الآن بنجاح!\n❌ لإيقافه أرسل: /stop_${streamId}`);

        process.on('close', (code) => {
            delete activeProcesses[streamId];
        });
    });
}

bot.hears('📋 البثوث الشغالة', (ctx) => {
    if (!isAuthorized(ctx.from.id)) return;
    const keys = Object.keys(activeProcesses);
    if (keys.length === 0) return ctx.reply('ℹ️ لا توجد أي بثوث شغالة حالياً.');
    let res = "📋 **بثوثك النشطة حالياً:**\n\n";
    keys.forEach(id => { res += `🆔 المعرف: \`${id}\`\n❌ للإيقاف: /stop_${id}\n\n`; });
    ctx.reply(res, { parse_mode: 'Markdown' });
});

bot.hears(/^\/stop_(.+)/, (ctx) => {
    if (!isAuthorized(ctx.from.id)) return;
    const streamId = ctx.match[1];
    if (activeProcesses[streamId]) {
        activeProcesses[streamId].kill();
        ctx.reply("🛑 تم إيقاف البث بنجاح.");
    }
});

// ⏱️ ميكانيزم الإيقاف الآمن الذكي بعد 5 ساعات ونصف لحماية السيرفر من البلوك المباشر
setTimeout(() => {
    Object.keys(activeProcesses).forEach(id => {
        try { activeProcesses[id].kill(); } catch (e) {}
    });
    process.exit(0);
}, 19800000); 

bot.launch();
process.on('uncaughtException', (err) => console.error('Error: ', err.message));
    bot.off('text', handleStreamUrl); 

    bot.on('text', async (ctxNext) => {
        const facebookUrl = ctxNext.message.text.trim();
        if (!facebookUrl.startsWith('rtmp')) return;

        const streamId = String(Date.now());
        ctxNext.reply(`⏳ جاري إطلاق البث ذو المعرف: ${streamId} في الخلفية...`);

        // إعدادات التمويه والـ FFmpeg الخفيف
        const userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36";
        const ffmpegArgs = [
            '-user_agent', userAgent,
            '-headers', 'Referer: https://google.com/\r\n',
            '-re', '-i', streamUrl, 
            '-c', 'copy', 
            '-f', 'flv', facebookUrl
        ];

        const process = spawn('ffmpeg', ffmpegArgs);
        activeProcesses[streamId] = process;

        ctxNext.reply(`✅ البث شغال الآن بنجاح!\n❌ لإيقافه أرسل: /stop_${streamId}`);

        process.on('close', (code) => {
            delete activeProcesses[streamId];
            bot.telegram.sendMessage(ADMIN_ID, `ℹ️ انتهى أو انقطع البث ذو المعرف: ${streamId}`);
        });
    });
}

bot.hears('📋 البثوث الشغالة', (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    const keys = Object.keys(activeProcesses);
    if (keys.length === 0) return ctx.reply('ℹ️ لا توجد أي بثوث شغالة حالياً.');
    let res = "📋 **البثوث النشطة حالياً:**\n\n";
    keys.forEach(id => { res += `🆔 المعرف: \`${id}\`\n❌ للإيقاف: /stop_${id}\n\n`; });
    ctx.reply(res, { parse_mode: 'Markdown' });
});

bot.hears(/^\/stop_(.+)/, (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    const streamId = ctx.match[1];
    if (activeProcesses[streamId]) {
        activeProcesses[streamId].kill();
        ctx.reply("🛑 تم إيقاف البث بنجاح.");
    } else {
        ctx.reply("❌ هاد البث غير موجود أو متوقف بالفعل.");
    }
});

bot.launch();
process.on('uncaughtException', (err) => console.error('Error: ', err.message));
  
