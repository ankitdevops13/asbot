import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import random
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from aiohttp import web
from pytube import YouTube
import cloudscraper
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
import math
import datetime
import aiofiles
import logging
import tgcrypto
import concurrent.futures

# ==================== CORE.PY FUNCTIONS ====================
def duration(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)
    
def exec(cmd):
    process = subprocess.run(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output = process.stdout.decode()
    print(output)
    return output

def pull_run(work, cmds):
    with concurrent.futures.ThreadPoolExecutor(max_workers=work) as executor:
        print("Waiting for tasks to complete")
        fut = executor.map(exec,cmds)

async def aio(url,name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(k, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return k

async def download(url,name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ka, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return ka

def parse_vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = []
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",2)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.append((i[0], i[2]))
            except:
                pass
    return new_info

def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i.strip()
            i = i.split("|")[0].split(" ",3)
            try:
                if "RESOLUTION" not in i[2] and i[2] not in temp and "audio" not in i[2]:
                    temp.append(i[2])
                    new_info.update({f'{i[2]}':f'{i[0]}'})
            except:
                pass
    return new_info

async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    print(f'[{cmd!r} exited with {proc.returncode}]')
    if proc.returncode == 1:
        return False
    if stdout:
        return f'[stdout]\n{stdout.decode()}'
    if stderr:
        return f'[stderr]\n{stderr.decode()}'

def old_download(url, file_name, chunk_size = 1024 * 10):
    if os.path.exists(file_name):
        os.remove(file_name)
    r = requests.get(url, allow_redirects=True, stream=True)
    with open(file_name, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                fd.write(chunk)
    return file_name

def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"

async def download_video(url, cmd, name):
    download_cmd = f'{cmd} -R 25 --fragment-retries 25 --external-downloader aria2c --downloader-args "aria2c: -x 16 -j 32"'
    print(download_cmd)
    logging.info(download_cmd)
    k = subprocess.run(download_cmd, shell=True)
    
    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        name = name.split(".")[0]
        if os.path.isfile(f"{name}.mkv"):
            return f"{name}.mkv"
        elif os.path.isfile(f"{name}.mp4"):
            return f"{name}.mp4"
        elif os.path.isfile(f"{name}.mp4.webm"):
            return f"{name}.mp4.webm"
        return name
    except FileNotFoundError as exc:
        return os.path.isfile.splitext[0] + "." + "mp4"

async def send_doc(bot: Client, m: Message, cc, ka, cc1, prog, count, name):
    reply = await m.reply_text(f"**Uploading ..🚀..** - `{name}`\n╰────⌈**𝐀𝐍𝐊𝐈𝐓❤️**⌋────╯")
    time.sleep(1)
    start_time = time.time()
    await m.reply_document(ka, caption=cc1)
    count += 1
    await reply.delete(True)
    time.sleep(1)
    os.remove(ka)
    time.sleep(3)

async def send_vid(bot: Client, m: Message, cc, filename, thumb, name):
    subprocess.run(f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"', shell=True)
    reply = await m.reply_text(f"**Uploading ..🚀..** - `{name}`\n╰────⌈**𝐀𝐍𝐊𝐈𝐓❤️**⌋────╯")
    try:
        if thumb == "no":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb
    except Exception as e:
        await m.reply_text(e)
        
    dur = int(duration(filename))
    start_time = time.time()

    try:
        await m.reply_video(filename, caption=cc, supports_streaming=True, height=720, width=1280, thumb=thumbnail, duration=dur)
    except Exception:
        await m.reply_document(filename, caption=cc)
    os.remove(filename)
    os.remove(f"{filename}.jpg")
    await reply.delete(True)

# ==================== PROGRESS BAR FUNCTIONS (ONLY FOR VIDEOS) ====================
def human_readable_size(size, decimal_places=2):
    """Bytes ko readable format mein convert karega"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def time_formatter(milliseconds: int) -> str:
    """Milliseconds ko readable time mein convert karega"""
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

async def progress_bar(current, total, reply, start):
    """Upload progress bar dikhayega - SIRF VIDEOS KE LIYE"""
    now = time.time()
    diff = now - start
    if diff < 1:
        return
    
    percent = current * 100 / total
    speed = current / diff
    elapsed_time = round(diff) * 1000
    time_to_completion = round((total - current) / speed) * 1000
    estimated_total_time = elapsed_time + time_to_completion

    elapsed_time = time_formatter(milliseconds=elapsed_time)
    estimated_total_time = time_formatter(milliseconds=estimated_total_time)

    # Progress bar design
    progress = "[{0}{1}]".format(
        ''.join(["█" for i in range(math.floor(percent / 5))]),
        ''.join(["░" for i in range(20 - math.floor(percent / 5))])
    )

    percentage = round(percent, 2)
    speed = human_readable_size(speed)
    total_size = human_readable_size(total)
    current_size = human_readable_size(current)

    try:
        await reply.edit_text(
            f"**📤 Uploading Video...**\n"
            f"{progress} **{percentage}%**\n"
            f"**📊 Progress:** `{current_size}` / `{total_size}`\n"
            f"**🚀 Speed:** `{speed}/s`\n"
            f"**⏰ ETA:** `{estimated_total_time}`\n"
            f"**🕐 Elapsed:** `{elapsed_time}`"
        )
    except:
        pass

async def upload_video_with_progress(bot, m, cc, filename, thumb, name):
    """Video upload karega progress bar ke saath - SIRF VIDEOS KE LIYE"""
    try:
        # Thumbnail generate karo
        subprocess.run(f'ffmpeg -i "{filename}" -ss 00:00:10 -vframes 1 "{filename}.jpg"', shell=True)
        
        # Progress message start karo
        start_time = time.time()
        progress_msg = await m.reply_text(f"**📤 Preparing to upload {name}...**")
        
        # Thumbnail set karo
        if thumb == "no":
            thumbnail = f"{filename}.jpg"
        else:
            thumbnail = thumb
        
        # Video duration nikaalo
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", 
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dur = int(float(result.stdout))
        
        # Video upload karo progress bar ke saath
        await m.reply_video(
            filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(progress_msg, start_time)
        )
        
        # Cleanup
        if os.path.exists(f"{filename}.jpg"):
            os.remove(f"{filename}.jpg")
        await progress_msg.delete()
        
    except Exception as e:
        # Agar video upload na ho to document ke roop mein upload karo (BINA PROGRESS BAR KE)
        try:
            await m.reply_document(
                filename,
                caption=cc
            )
        except Exception as doc_error:
            await m.reply_text(f"Upload failed: {str(doc_error)}")
        
        # Cleanup
        if os.path.exists(f"{filename}.jpg"):
            os.remove(f"{filename}.jpg")

# ==================== RANDOM EMOJI FUNCTION ====================
async def show_random_emojis(message):
    emojis = ['😀', '😈', '❤️🔥', '🔱', '🆖', '🧿', '💥', '🔮','🙉']
    emoji_message = await message.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message

# ==================== BOT CONFIGURATION ====================
owner_id = 7341059064
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

photoyt = "https://www.theproche.com/wp-content/uploads/2022/03/youtube-thumbnail.png"
utkarsh = "https://files.catbox.moe/2k68oh.jpg"
auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzM0MTA1OTA2NCIsInRnX3VzZXJuYW1lIjoiQEFua2l0U2hha3lhIiwiaWF0IjoxNzUyMzA1MTc0fQ.3RIgokYBSvom_0d_aW4S7U-sjDKLNpWhi8_CKabkbZQ"

api_url = "http://master-api-v3.vercel.app"
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZnJlZSB1c2VyICIsInRnX3VzZXJuYW1lIjoiUFVCTElDIFVTRSIsImlhdCI6MTc0OTYxOTUzM30.oRI_9FotOi3Av9S2Wrr2g6VXUHJEknWVY91-TZ5XdNg"
cookies_file_path = os.getenv("COOKIES_FILE_PATH", "/youtube_cookies.txt")

# Global variables
my_name = "🅰︎🅽🅺🅸🆃❤️🔥"

auth_users = [1226915008,7341059064,5817712634]

# ==================== COMMAND HANDLERS ====================
@bot.on_message(filters.command("auth") & filters.private)
async def authorize_user(client, message):
    if message.from_user.id == owner_id:
        try:
            user_id = int(message.text.split()[1])
            if user_id not in auth_users:
                auth_users.append(user_id)
                await message.reply("User authorized successfully.")
            else:
                await message.reply("User is already authorized.")
        except (IndexError, ValueError):
            await message.reply("Please provide a valid user ID.")
    else:
        await message.reply("You are not authorized to use this command.")

async def is_auth(user_id):
    return user_id in auth_users or user_id == owner_id

@bot.on_message(filters.command(["start"]))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text(f"**Hi 👋.. How are you...?**\n**Bot Made BY 🅰𝕊ℍ𝕌 🅂🄷🄰🅁🄼🅰™️🇮🇳**")

@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    await m.reply_text("🆖**STOPPED**🆖", True)
    os.execl(sys.executable, sys.executable, *sys.argv)
    
@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )

    try:
        input_message: Message = await client.listen(m.chat.id)
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        downloaded_path = await input_message.download()
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📓 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["kanika","shilu","alpha"]))
async def txt_handler(bot: Client, m: Message):
    user_id = m.from_user.id
    if user_id not in auth_users:
        await m.reply_text("**HEY BUDDY THIS IS ONLY FOR MY ADMINS  **")
    else:
        editable = await m.reply_text(f"**📩Send me the TXT file and wait.**")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit = f"𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚™🇮🇳"
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            links.append(i.split("://", 1))
        os.remove(x)
    except:
        await m.reply_text("Invalid file input.")
        os.remove(x)
        return
   
    await editable.edit(f"Total links found are **{len(links)}**\n\nSend From where you want to download initial is **1**")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("**Enter Your Batch Name or send d for grabing from text filename.**")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == 'd':
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("**Enter resolution.\n Eg : 480 or 720**")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "144x256"
        elif raw_text2 == "240":
            res = "240x426"
        elif raw_text2 == "360":
            res = "360x640"
        elif raw_text2 == "480":
            res = "480x854"
        elif raw_text2 == "720":
            res = "720x1280"
        elif raw_text2 == "1080":
            res = "1080x1920" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
        
    await editable.edit("**Enter Your Name or send 'de' for use default.\n Eg : 🅰︎🅽🅺🅸🆃 🆂🅷🅰🅺🆈🅰™️👨‍💻**")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    if raw_text3 == 'de':
        CR = credit
    else:
        CR = raw_text3

    await editable.edit("**Enter Your Working Cp & PW Token For CP URL & MPD URLor send 'unknown' for use default**")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == 'pw':
        token = pw_token
    else:
        token = raw_text4

    await editable.edit("Now send the **Thumb url**\n**Eg :** ``\n\nor Send `no`")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb == "no"

    count =int(raw_text)    
    try:
        for i in range(arg-1, len(links)):
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)
          
            elif 'videos.classplusapp' in url or "tencdn.classplusapp" in url or "alisg-cdn-a.classplusapp.com" in url or "webvideos.classplusapp.com" in url or "media-cdn-alisg.classplusapp.com" in url or "videos.classplusapp" in url or "videos.classplusapp.com" in url or "media-cdn-a.classplusapp" in url or "media-cdn.classplusapp" in url:
                headers = {'host': 'api.classplusapp.com', 'x-access-token': f'{raw_text4}', 'accept-language': 'EN', 'api-version': '18', 'app-version': '1.4.73.2', 'build-number': '35', 'connection': 'Keep-Alive', 'content-type': 'application/json', 'device-details': 'Xiaomi_Redmi 7_SDK-32', 'device-id': 'c28d3cb16bbdac01', 'region': 'IN', 'user-agent': 'Mobile-Android', 'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c', 'accept-encoding': 'gzip'}
                params = {"url": f"{url}"}
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url   = response.json()['url']
            elif 'media-cdn.classplusapp.com/drm/' in url:
             url = f'https://dragoapi.vercel.app/video/{url}'

            elif '/master.mpd' in url:
             url = f"https://master-api-v3.vercel.app/pw/m3u8v2?url={url}&token={raw_text4}&authorization={auth_token}&q={raw_text2}"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{str(count).zfill(3)}) {name1[:60]}'

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            
            try:  
                cc = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakya.mkv\n**├── Resolution :** [{res}]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n**<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>**'
                cc1 = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakya.pdf\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n**<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>**'
                cczip = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakya.zip\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n**<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>**'
                ccimg = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakya.jpg\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n**<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>**'
                ccyt = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n╭─────────────────.★..─╮\n   <a href="{url}">__**Click Here to Watch Stream**__</a>\n╰─..★.─────────────────╯\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakya.mkv\n**├── Resolution :** [{res}]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n**<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>**'
                ccukt = f'**\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯**\n\n╭─────────────────.★..─╮\n   <a href="{url}">__**Click Here to Download**__</a>\n╰─..★.─────────────────╯\n\n**📝 Title:** {name1} \n**├── Extention :** @AnkitShakya.doc\n**├── Resolution :** [None]\n\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n**📥 Extracted By :**\n╭──────────.✨..─╮\n\n      {CR}\n\n╰─..✨.──────────╯\n\n**<pre><code>━━━━━✦𝐀𝐍𝐊𝐈𝐓❤️✦━━━━━</code></pre>**'
                
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count+=1
                        continue


                elif ".pdf" in url:
                    try:
                        await asyncio.sleep(4)
                        url = url.replace(" ", "%20")
                        scraper = cloudscraper.create_scraper()
                        response = scraper.get(url)
                        if response.status_code == 200:
                            with open(f'{name}.pdf', 'wb') as file:
                                file.write(response.content)
                            await asyncio.sleep(4)
                            copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                            count += 1
                            os.remove(f'{name}.pdf')
                        else:
                            await m.reply_text(f"Failed to download PDF: {response.status_code} {response.reason}")
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue                


                elif ".zip" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.zip" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.zip', caption=cczip)
                        count += 1
                        os.remove(f'{name}.zip')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                elif any(img in url.lower() for img in ['.jpeg', '.png', '.jpg']):
                        try:
                            subprocess.run(['wget', url, '-O', f'{name}.jpg'], check=True)  # Fixing this line
                            await bot.send_photo(
                                chat_id=m.chat.id,
                                caption = cimg,
                                photo= f'{name}.jpg',  )
                            count += 1
                            await asyncio.sleep(1)
                            continue
                        except subprocess.CalledProcessError:
                            await message.reply("Failed to download the image. Please check the URL.")
                        except Exception as e:
                            await message.reply(f"An error occurred: {e}")
                        finally:
                            # Clean up the downloaded file
                            if os.path.exists(f'{name}.jpg'):
                                os.remove(f'{name}.jpg')
                              
                elif ".ws" in url and url.endswith(".ws"):
                    try: 
                        # HTML UPLOAD - BINA PROGRESS BAR KE
                        await bot.send_document(chat_id=m.chat.id, document=f"{name}.html", caption=cc3)
                        os.remove(f'{name}.html')
                        count += 1
                        time.sleep(5)
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        await m.reply_text(str(e))
                        continue
                 
                else:
                    # VIDEO UPLOAD - PROGRESS BAR KE SAATH
                    remaining_links = len(links) - count
                    progress = (count / len(links)) * 100
                    emoji_message = await show_random_emojis(message)
                    Show = f"🚀 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒...» {progress:.2f}%\n\n📥 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🚀.. »\n\n├──🎞️ 📊 Total Links = {len(links)}\n\n├──🎞️ ⚡️ Currently On = {str(count).zfill(3)}\n\n├──⏳ Remaining URL = {remaining_links}\n\n├──🎞️ Title:- {name}\n\n├──⌨️ Resolution » {raw_text2}\n\n├──🖼️ Thumbnail » {raw_text6}\n\n├── Url: [Not Defined]\n\n├──🤖 Bot Made By: 『ᴀɴᴋɪᴛ sʜᴀᴋʏᴀ』"
                    prog = await m.reply_text(Show)
                    res_file = await download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await emoji_message.delete()
                    
                    # VIDEO UPLOAD WITH PROGRESS BAR
                    await upload_video_with_progress(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"\n\n<pre><code>**├──❎ Downloding Fail**</code></pre>\n\n╭──────.★..─╮\n{str(count).zfill(3)}\n╰─..★.──────╯\n\n📝 Title:- {name1}\n\n├──⌨️ Resolution » {raw_text2}\n<pre><code>📚 Batch Name: {b_name}</code></pre>\n\n├──🔗 Url:  <a href= {url} >__**CLICK HERE**__</a>\n\n├──🤖 Bot Made By: 『ᴀɴᴋɪᴛ sʜᴀᴋʏᴀ』"
                )
                count += 1
                continue


    except Exception as e:
        await m.reply_text(e)    
    await m.reply_text("🔰Done🔰\n<pre><code>📚Batch Download Successfully</code></pre>")

bot.run()
