const { Telegraf, Markup } = require('telegraf');
const { spawn } = require('child_process');
const express = require('express');
const fs = require('fs');
const path = require('path');

// 🔐 المعطيات الأساسية
const BOT_TOKEN = "8896904518:AAEkbtktyuz3AinMFKUvLspRfoMLqKwTdy8"; 
const ADMIN_ID = 7141170679; 

const bot = new Telegraf(BOT_TOKEN);
const app = express();
app.get('/', (req, res) => res.send('System Turbo OK'));
app.listen(process.env.PORT || 8080);

const WHITELIST_FILE = path.join(__dirname, 'allowed_users.json');

function loadWhitelist() {
    if (fs.existsSync(WHITELIST_FILE)) {
        try { return JSON.parse(fs.readFileSync(WHITELIST_FILE)); } catch (e) { return []; }
    }
    return [];
}

function saveWhitelist(data) {
    fs.writeFileSync(WHITELIST_FILE, JSON.stringify(data, null, 4));
}

function isAuthorized(userId) {
    if (userId === ADMIN_ID) return true;
    return loadWhitelist().includes(userId);
}

let activeProcesses = {};

const getUserKeyboard = () => Markup.keyboard([['🚀 إطلاق بث جديد', '📋 البثوث الشغالة']]).resize();

// استقبال أمر البداية
bot.start((ctx) => {
    const userId = ctx.from.id;
    if (!isAuthorized(userId)) {
        return ctx.reply(`❌ عذراً، هاد البوت خاص ومصرح به لأشخاص محددين فقط تجريبياً.\n\n📞 للمزيد من المعلومات أو لتفعيل حسابك، تواصل مع المطور مباشرة:\n➡️ 0717962808`);
    }
    ctx.reply('👋 مرحباً بك في النسخة المستقرة والأقوى لبث المباريات المباشر!', getUserKeyboard());
});

// لوحة التحكم 👑
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

// التعديل والميكانيزم الصحيح لـ Regex بدون أي أخطاء syntax 🛠️
bot.hears(/^\/(add|remove) (\d+)/, (ctx) => {
    if (ctx.from.id !== ADMIN_ID) return;
    const cmd = ctx.match[1];
    const targetId = parseInt(ctx.match[2]);
    let whitelist = loadWhitelist();

    if (cmd === 'add') {
        if (!whitelist.includes(targetId)) {
            whitelist.push(targetId);
            saveWhitelist(whitelist);
            ctx.reply(`✅ تم تفعيل الحساب وإضافته للـ Whitelist: \`${targetId}\``, { parse_mode: 'Markdown' });
        } else { ctx.reply("ℹ️ هاد الـ ID مضاف بالفعل."); }
    } else if (cmd === 'remove') {
        if (whitelist.includes(targetId)) {
            whitelist = whitelist.filter(id => id !== targetId);
            saveWhitelist(whitelist);
            ctx.reply(`❌ تم حذف الحساب وحظره من الـ Whitelist: \`${targetId}\``, { parse_mode: 'Markdown' });
        } else { ctx.reply("ℹ️ هاد الـ ID غير موجود ف القائمة."); }
    }
});

// 🚀 محرك إطلاق البثوث المتطور والمحمي من الـ Crash
bot.hears('🚀 إطلاق بث جديد', (ctx) => {
    if (!isAuthorized(ctx.from.id)) return;
    ctx.reply('📥 أرسل الآن رابط الـ M3U8 أو MPD المباشر:');
    bot.on('text', handleStreamUrl);
});

async function handleStreamUrl(ctx) {
    if (!isAuthorized(ctx.from.id)) return;
    let streamUrl = ctx.message.text.trim();
    
    if (streamUrl.startsWith('/') || (!streamUrl.startsWith('http') && !streamUrl.includes('rtmp'))) return;

    // تنظيف الماركداون والروابط المتكررة
    if (streamUrl.includes('](')) {
        streamUrl = streamUrl.split('](')[1].split(')')[0].trim();
    }
    streamUrl = streamUrl.replace(/[()\[\]]/g, '').trim();

    ctx.reply('📥 صيفط رابط الـ RTMPS ومفتاح البث د الفيسبوك (في سطر واحد):');
    bot.off('text', handleStreamUrl); 

    bot.on('text', async (ctxNext) => {
        if (!isAuthorized(ctxNext.from.id)) return;
        let facebookUrl = ctxNext.message.text.trim();
        
        // غسل وتنظيف كود فيسبوك أوتوماتيكياً من كاع الشوائب والأقواس تليغرام
        if (facebookUrl.includes('](')) {
            facebookUrl = facebookUrl.split('](')[0].trim();
        }
        facebookUrl = facebookUrl.replace(/[()\[\]]/g, '').trim(); 

        // تحويل ذكي لـ rtmp لضمان الإستقرار التام ف السيرفرات الخارجية
        if (facebookUrl.startsWith('rtmps://live-api-s.facebook.com:443/')) {
            facebookUrl = facebookUrl.replace('rtmps://live-api-s.facebook.com:443/', 'rtmp://live-api-s.facebook.com:80/');
        }

        if (!facebookUrl.startsWith('rtmp')) {
            return ctxNext.reply('❌ الرابط صيفطتيه ماشي rtmp/rtmps صحيح، عاود كليكي على "إطلاق بث جديد" وتأكد من النسخ.');
        }

        const streamId = String(Date.now());
        ctxNext.reply(`⏳ جاري معالجة وإطلاق البث ذو المعرف: ${streamId}...`);

        const userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
        
        const ffmpegArgs = [
            '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '15',
            '-user_agent', userAgent,
            '-headers', 'Referer: https://google.com/\r\n',
            '-re', '-i', streamUrl, 
            '-c:v', 'copy', 
            '-c:a', 'aac', 
            '-f', 'flv', facebookUrl
        ];

        try {
            const process = spawn('ffmpeg', ffmpegArgs);
            activeProcesses[streamId] = process;

            ctxNext.reply(`✅ البث شغال الآن بنجاح على فيسبوك تيربو!\n❌ لإيقافه أرسل: /stop_${streamId}`);

            process.on('close', (code) => {
                delete activeProcesses[streamId];
                bot.telegram.sendMessage(ctxNext.from.id, `ℹ️ البث ذو المعرف ${streamId} انتهى أو تم إغلاقه.`);
            });

            process.on('error', (err) => {
                console.error('FFmpeg error:', err.message);
                delete activeProcesses[streamId];
            });

        } catch (err) {
            ctxNext.reply('❌ حدث مشكل تقني ف تشغيل الفلاتر، تأكد من روابط البث.');
        }
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
        try { activeProcesses[streamId].kill(); } catch (e) {}
        ctx.reply("🛑 تم إيقاف البث بنجاح.");
    }
});

setTimeout(() => {
    Object.keys(activeProcesses).forEach(id => {
        try { activeProcesses[id].kill(); } catch (e) {}
    });
    process.exit(0);
}, 19800000); 

bot.launch();

process.on('uncaughtException', (err) => console.error('System Recovered From Exception: ', err.message));
process.on('unhandledRejection', (reason, promise) => console.error('System Recovered From Rejection: ', reason));
  whitelist.push(targetId);
            saveWhitelist(whitelist);
            ctx.reply(`✅ تم تفعيل الحساب وإضافته للـ Whitelist: \`${targetId}\``, { parse_mode: 'Markdown' });
        } else { ctx.reply("ℹ️ هاد الـ ID مضاف بالفعل."); }
    } else if (cmd === 'remove') {
        if (whitelist.includes(targetId)) {
            whitelist = whitelist.filter(id => id !== targetId);
            saveWhitelist(whitelist);
            ctx.reply(`❌ تم حذف الحساب وحظره من الـ Whitelist: \`${targetId}\``, { parse_mode: 'Markdown' });
        } else { ctx.reply("ℹ️ هاد الـ ID غير موجود ف القائمة."); }
    }
});

bot.hears('🚀 إطلاق بث جديد', (ctx) => {
    if (!isAuthorized(ctx.from.id)) return;
    ctx.reply('📥 أرسل الآن رابط الـ M3U8 أو MPD المباشر:');
    bot.on('text', handleStreamUrl);
});

async function handleStreamUrl(ctx) {
    if (!isAuthorized(ctx.from.id)) return;
    let streamUrl = ctx.message.text.trim();
    if (streamUrl.startsWith('/') || !streamUrl.startsWith('http')) return;

    if (streamUrl.includes('](')) {
        streamUrl = streamUrl.split('](')[1].replace(')', '').trim();
    }

    ctx.reply('📥 صيفط رابط الـ RTMPS ومفتاح البث د الفيسبوك (في سطر واحد):');
    bot.off('text', handleStreamUrl); 

    bot.on('text', async (ctxNext) => {
        if (!isAuthorized(ctxNext.from.id)) return;
        let facebookUrl = ctxNext.message.text.trim();
        
        if (facebookUrl.includes('](')) {
            facebookUrl = facebookUrl.split('](')[0].replace('[', '').replace(']', '').trim();
        }
        facebookUrl = facebookUrl.replace(/[()]/g, '').trim(); 

        if (!facebookUrl.startsWith('rtmp')) {
            return ctxNext.reply('❌ الرابط لي صيفطتيه ماشي rtmps صحيح، عاود اضغط على زر الإطلاق وجرب مجدداً.');
        }

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

        try {
            const process = spawn('ffmpeg', ffmpegArgs);
            activeProcesses[streamId] = process;

            ctxNext.reply(`✅ البث شغال الآن بنجاح!\n❌ لإيقافه أرسل: /stop_${streamId}`);

            process.on('close', (code) => {
                delete activeProcesses[streamId];
            });

            process.on('error', (err) => {
                console.error('FFmpeg Error: ', err.message);
                delete activeProcesses[streamId];
            });
        } catch (err) {
            ctxNext.reply('❌ حدث خطأ أثناء تشغيل الـ FFmpeg، تأكد من الروابط.');
        }
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

setTimeout(() => {
    Object.keys(activeProcesses).forEach(id => {
        try { activeProcesses[id].kill(); } catch (e) {}
    });
    process.exit(0);
}, 19800000); 

bot.launch();

process.on('uncaughtException', (err) => console.error('Caught Exception: ', err.message));
process.on('unhandledRejection', (reason, promise) => console.error('Unhandled Rejection: ', reason));
