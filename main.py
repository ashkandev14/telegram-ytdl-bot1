import telebot
import yt_dlp
import os

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")  # فقط یوزرنیم بدون @
bot = telebot.TeleBot(BOT_TOKEN)

MAX_FILE_SIZE_MB = 50
REQUIRED_CHANNELS = []

def is_user_subscribed(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

def download_best_quality(url):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = sorted(info['formats'], key=lambda x: x.get('height', 0), reverse=True)

        for fmt in formats:
            filesize = fmt.get('filesize')
            if filesize and filesize < MAX_FILE_SIZE_MB * 1024 * 1024 and fmt.get('ext') == 'mp4':
                download_opts = {
                    'format': fmt['format_id'],
                    'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
                    'quiet': True
                }
                with yt_dlp.YoutubeDL(download_opts) as downloader:
                    downloader.download([url])
                    filepath = f"{temp_dir}/{info['id']}.{fmt['ext']}"
                    return filepath
    return None

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if not is_user_subscribed(user_id):
        if REQUIRED_CHANNELS:
            links = "\n".join([f"👉 {ch}" for ch in REQUIRED_CHANNELS])
            bot.send_message(message.chat.id, f"🔒 برای استفاده از ربات، باید عضو این کانال‌ها باشی:\n\n{links}\n\nسپس دوباره /start رو بفرست ✅")
        else:
            bot.send_message(message.chat.id, "⚠️ لیست کانال‌ها هنوز توسط ادمین تنظیم نشده.")
        return
    bot.send_message(message.chat.id, "سلام! 🎬 لینک یوتیوبتو بفرست تا برات ویدیو رو بفرستم.")

@bot.message_handler(commands=['setchannels'])
def set_channels(message):
    if message.from_user.username != ADMIN_USERNAME:
        bot.reply_to(message, "⛔️ فقط ادمین می‌تونه لیست کانال‌ها رو تنظیم کنه.")
        return
    msg = bot.send_message(message.chat.id, "📥 لطفاً لیست کانال‌ها رو به صورت جدا شده با فاصله بفرست (مثلاً:\n@channel1 @channel2 ...):")
    bot.register_next_step_handler(msg, save_channels)

def save_channels(message):
    global REQUIRED_CHANNELS
    new_channels = message.text.strip().split()
    REQUIRED_CHANNELS = new_channels
    text = "\n".join([f"✅ {ch}" for ch in REQUIRED_CHANNELS])
    bot.send_message(message.chat.id, f"✅ لیست کانال‌ها آپدیت شد:\n{text}")

@bot.message_handler(func=lambda m: True)
def handle_video_request(message):
    user_id = message.from_user.id
    if not is_user_subscribed(user_id):
        bot.send_message(message.chat.id, "⛔️ اول باید عضو همه کانال‌ها بشی.")
        return

    url = message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        bot.send_message(message.chat.id, "لطفاً فقط لینک یوتیوب بفرست.")
        return

    msg = bot.send_message(message.chat.id, "🔄 در حال بررسی لینک و کیفیت مناسب زیر 50MB...")
    filepath = download_best_quality(url)

    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="🎉 اینم ویدیوت!")
        os.remove(filepath)
    else:
        bot.send_message(message.chat.id, "❌ هیچ کیفیتی زیر 50MB برای این ویدیو پیدا نشد.")

bot.polling()