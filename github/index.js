const { Telegraf, Markup } = require('telegraf');
const { spawn } = require('child_process');
const express = require('express');

// 🔐 [تعديل] حط التوكن والآي دي ديالك هنا
const BOT_TOKEN = "8896904518:AAEkbtktyuz3AinMFKUvLspRfoMLqKwTdy8"; 
const ADMIN_ID = 7141170679; 

const bot = new Telegraf(BOT_TOKEN);
const app = express();

// سيرفر وهمي باش جيتهاب ما يطفيش السكريبت
app.get('/', (req, res) => res.send('System OK'));
app.listen(process.env.PORT || 8080);

let activeProcesses = {};

const getUserKeyboard = () => Markup.keyboard([['🚀 إطلاق بث جديد', '📋 البثوث الشغالة']]).resize();

bot.start((ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    ctx.reply('👋 مرحباً بك في بوت GitHub المستقل للبث المباشر!', getUserKeyboard());
});

bot.hears('🚀 إطلاق بث جديد', (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    ctx.reply('📥 أرسل الآن رابط الـ M3U8 أو MPD المباشر:');
    bot.on('text', handleStreamUrl);
});

async function handleStreamUrl(ctx) {
    if (ctx.from.id !== ADMIN_ID) return;
    const streamUrl = ctx.message.text.trim();
    if (streamUrl.startsWith('/') || !streamUrl.startsWith('http')) return;

    ctx.reply('📥 صيفط رابط الـ RTMPS ومفتاح البث د الفيسبوك (في سطر واحد):');
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
