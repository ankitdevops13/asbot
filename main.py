import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import urllib.parse
import yt_dlp
import cloudscraper
from urllib.parse import urlparse

from logs import logging
from bs4 import BeautifulSoup
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
import random 
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import base64
import datetime


photologo = 'https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png'
photoyt = "https://www.theproche.com/wp-content/uploads/2022/03/youtube-thumbnail.png"
utkarsh = "https://files.catbox.moe/2k68oh.jpg"

async def show_random_emojis(message):    
    emojis = ['🥰', '😘', '❤️', '⚡️', '🚀', '🌟', '🔥', '✨','😍']
    emoji_message = await message.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message

owner_id = 6748792256

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzM0MTA1OTA2NCIsInRnX3VzZXJuYW1lIjoiQEFua2l0U2hha3lhIiwiaWF0IjoxNzU4MjcxNjg1fQ.xdRrrm3xkWr8kDZFblSowp1syOnwjPQRtXOBX0N5ZAk"



cookies_file_path= "youtube_cookies.txt"


auth_users = [1226915008,6748792256,8085418235,5817712634,8172689585]
import sqlite3
import os

# Database setup
DB_PATH = "bot_database.db"

def init_database():
    """Initialize SQLite database for storing authorized users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create auth_users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_users (
            user_id INTEGER PRIMARY KEY,
            authorized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            authorized_by INTEGER
        )
    ''')
    
    # Insert default/owner users if they don't exist
    default_users = [1226915008, 8085418235, 6748792256, 5817712634, 8172689585]
    for user_id in default_users:
        cursor.execute('''
            INSERT OR IGNORE INTO auth_users (user_id, authorized_by)
            VALUES (?, ?)
        ''', (user_id, 6748792256))  # Owner ID as authorized_by
    
    conn.commit()
    conn.close()

# Initialize database when script starts
init_database()

def add_auth_user(user_id, authorized_by):
    """Add user to authorized list in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO auth_users (user_id, authorized_by)
        VALUES (?, ?)
    ''', (user_id, authorized_by))
    conn.commit()
    conn.close()

def remove_auth_user(user_id):
    """Remove user from authorized list"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auth_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def is_auth_user(user_id):
    """Check if user is authorized"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM auth_users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_all_auth_users():
    """Get list of all authorized users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, authorized_at, authorized_by FROM auth_users ORDER BY authorized_at DESC')
    users = cursor.fetchall()
    conn.close()
    return users

@bot.on_message(filters.command("auth") & filters.private)
async def authorize_user(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is owner
    if user_id != owner_id:
        await message.reply("❌ You are not authorized to use this command. Only the bot owner can authorize users.")
        return
    
    try:
        # Parse user ID from command
        args = message.text.split()
        if len(args) < 2:
            await message.reply("📝 **Usage:** `/auth <user_id>`\n\nExample: `/auth 1234567890`")
            return
        
        target_user_id = int(args[1])
        
        # Check if user is already authorized
        if is_auth_user(target_user_id):
            await message.reply(f"✅ User `{target_user_id}` is already authorized.")
            return
        
        # Add user to database
        add_auth_user(target_user_id, user_id)
        await message.reply(f"✅ User `{target_user_id}` has been authorized successfully!")
        
    except ValueError:
        await message.reply("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")


@bot.on_message(filters.command("unauth") & filters.private)
async def unauthorize_user(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is owner
    if user_id != owner_id:
        await message.reply("❌ You are not authorized to use this command. Only the bot owner can unauthorize users.")
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.reply("📝 **Usage:** `/unauth <user_id>`\n\nExample: `/unauth 1234567890`")
            return
        
        target_user_id = int(args[1])
        
        # Prevent removing owner
        if target_user_id == owner_id:
            await message.reply("❌ Cannot remove the bot owner from authorized list.")
            return
        
        # Check if user exists
        if not is_auth_user(target_user_id):
            await message.reply(f"❌ User `{target_user_id}` is not authorized.")
            return
        
        # Remove user from database
        remove_auth_user(target_user_id)
        await message.reply(f"✅ User `{target_user_id}` has been unauthorized.")
        
    except ValueError:
        await message.reply("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@bot.on_message(filters.command("authlist") & filters.private)
async def list_auth_users(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is owner
    if user_id != owner_id:
        await message.reply("❌ Only the bot owner can view the authorized users list.")
        return
    
    users = get_all_auth_users()
    
    if not users:
        await message.reply("📋 No authorized users found.")
        return
    
    # Format the list
    msg = "📋 **Authorized Users List**\n\n"
    for i, (uid, auth_time, auth_by) in enumerate(users, 1):
        msg += f"{i}. **User ID:** `{uid}`\n"
        msg += f"   📅 **Authorized:** `{auth_time}`\n"
        msg += f"   👤 **By:** `{auth_by}`\n\n"
    
    await message.reply(msg, parse_mode=ParseMode.MARKDOWN)


# Command to authorize a user

async def authorize_user(client, message):
    if message.from_user.id == owner_id:  # Ensure only the owner can authorize
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

# Function to check authorization
async def is_auth(user_id):
    return user_id in auth_users or user_id == owner_id


@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )

    try:
        # Wait for the user to send the cookies filel
        input_message: Message = await client.listen(m.chat.id)

        # Validate the uploaded file
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        # Download the cookies file
        downloaded_path = await input_message.download()

        # Read the content of the uploaded file
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        # Replace the content of the target cookies file
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")
        
@bot.on_message(filters.command(["start"]) )
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text(f"**Hi 👋.. How are you...?**\n**Bot Made BY 𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚™🇮🇳**")

@bot.on_message(filters.command(["stop"]) )
async def restart_handler(_, m):
    await m.reply_text("🚦**STOPPED**🚦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)
    
@bot.on_message(filters.command(["logs"]) )
async def send_logs(bot: Client, m: Message):
    try:
        with open("logs.txt", "rb") as file:
            sent= await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete(True)
    except Exception as e:
        await m.reply_text(f"Error sending logs: {e}")


@bot.on_message(filters.command(["y2t"]))
async def youtube_to_txt(client, message: Message):
    user_id = str(message.from_user.id)
    
    await message.reply_text(
        "<pre><code>Welcome to the YouTube to .txt🗃️ Converter!</code></pre>\n"
        "<pre><code>Please Send YouTube Playlist link for convert into a `.txt` file.</code></pre>\n"
    )

    input_message: Message = await bot.listen(message.chat.id)
    youtube_link = input_message.text.strip()
    await input_message.delete(True)

    # Fetch the YouTube information using yt-dlp with cookies
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'forcejson': True,
        'cookies': 'youtube_cookies.txt'  # Specify the cookies file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(youtube_link, download=False)
            if 'entries' in result:
                title = result.get('title', 'youtube_playlist')
            else:
                title = result.get('title', 'youtube_video')
        except yt_dlp.utils.DownloadError as e:
            await message.reply_text(
                f"<pre><code>🚨 Error occurred {str(e)}</code></pre>"
            )
            return

    # Ask the user for the custom file name
    file_name_message = await message.reply_text(
        f"<pre><code>🔤 Send file name (without extension)</code></pre>\n"
        f"**✨ Send  `1`  for Default**\n"
        f"<pre><code>{title}</code></pre>\n"
    )

    input4: Message = await bot.listen(message.chat.id, filters=filters.text & filters.user(message.from_user.id))
    raw_text4 = input4.text
    await file_name_message.delete(True)
    await input4.delete(True)
    if raw_text4 == '1':
       custom_file_name  = title
    else:
       custom_file_name = raw_text4
    
    # Extract the YouTube links
    videos = []
    if 'entries' in result:
        for entry in result['entries']:
            video_title = entry.get('title', 'No title')
            url = entry['url']
            videos.append(f"{video_title}: {url}")
    else:
        video_title = result.get('title', 'No title')
        url = result['url']
        videos.append(f"{video_title}: {url}")

    # Create and save the .txt file with the custom name
    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)  # Ensure the directory exists
    with open(txt_file, 'w') as f:
        f.write('\n'.join(videos))

    # Send the generated text file to the user with a pretty caption
    await message.reply_document(
        document=txt_file,
        caption=f'<a href="{youtube_link}">__**Click Here to open Playlist**__</a>\n<pre><code>{custom_file_name}.txt</code></pre>\n'
    )

    # Remove the temporary text file after sending
    os.remove(txt_file)
async def get_credit_name(bot, m, editable, user_id, user_first_name, user_username, user_mention):
    """Helper function to get credit name from user"""
    
    owner_credit = f"𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚™🇮🇳"
    
    credit_options = (
        f"**Choose your credit name:**\n\n"
        f"👤 **Your Name:** {user_mention}\n"
        f"🔖 **Username:** @{user_username if user_username else 'Not set'}\n\n"
        f"**Options:**\n"
        f"• Send `de` - Use bot owner's name\n"
        f"• Send `me` - Use your Telegram name\n"
        f"• Send `username` - Use your @username\n"
        f"• Or type any custom name\n\n"
        f"**Default:** Owner's credit"
    )
    
    await editable.edit(credit_options)
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    
    # Process selection
    if raw_text3 == 'de':
        CR = owner_credit
        credit_display = "Bot Owner"
    elif raw_text3 == 'me':
        CR = user_mention
        credit_display = user_first_name
    elif raw_text3 == 'username':
        if user_username:
            CR = f"@{user_username}"
            credit_display = f"@{user_username}"
        else:
            CR = user_mention
            credit_display = f"{user_first_name} (no username)"
    else:
        CR = raw_text3
        credit_display = "Custom Name"
    
    # Show confirmation
    confirm_msg = await m.reply_text(f"✅ Credit set to: {CR}")
    await asyncio.sleep(1)
    await confirm_msg.delete()
    
    return CR

@bot.on_message(filters.command(["ankit","deaduser"]) )
async def txt_handler(bot: Client, m: Message):
    user_id = m.from_user.id
    if not is_auth_user(user_id):
        await m.reply_text("**HEY BUDDY THIS IS ONLY FOR MY ADMINS**")
        return
    
    # Get user details
    user_first_name = m.from_user.first_name
    user_last_name = m.from_user.last_name or ""
    user_full_name = f"{user_first_name} {user_last_name}".strip()
    user_username = m.from_user.username
    user_mention = f"<a href='tg://user?id={user_id}'>{user_full_name}</a>"
    
    editable = await m.reply_text(f"<pre><code>**🔹Hi I am Poweful TXT Downloader📥 Bot.**</code></pre>\n<pre><code>🔹**Send me the TXT file and wait.**</code></pre>")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit ="𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳" 
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            links.append(i.split("://", 1))
        os.remove(x)
    except:
        await m.reply_text("<pre><code>Invalid file input.</code></pre>")
        os.remove(x)
        return
   
    await editable.edit(f"<pre><code>Total 🔗 links found are __**{len(links)}**__</code></pre>\n<pre><code>Send From where you want to download initial is `1`</code></pre>")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("<pre><code>**Enter Your Batch Name**</code></pre>\n<pre><code>Send `1` for use default.</code></pre>")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == '1':
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("<pre><code>╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ </code></pre>\n┣━━⪼ send `144`  for 144p\n┣━━⪼ send `240`  for 240p\n┣━━⪼ send `360`  for 360p\n┣━━⪼ send `480`  for 480p\n┣━━⪼ send `720`  for 720p\n┣━━⪼ send `1080` for 1080p\n<pre><code>╰━━⌈⚡[ 𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳 ]⚡⌋━━➣ </code></pre>")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    quality = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"

    # ========== CREDIT NAME SECTION (4 spaces indentation) ==========
    # Get credit name from user
    CR = await get_credit_name(
        bot, m, editable, user_id, 
        user_first_name, user_username, user_mention
    )
    # ========== END CREDIT NAME SECTION ==========

    pw_token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDI4NDE2NDAuNTQyLCJkYXRhIjp7Il9pZCI6IjY1OWZjZWU5YmI4YjFkMDAxOGFmYTExZCIsInVzZXJuYW1lIjoiODUzOTkyNjE5MCIsImZpcnN0TmFtZSI6IlNoaXR0dSIsImxhc3ROYW1lIjoiU2luZ2giLCJvcmdhbml6YXRpb24iOnsiX2lkIjoiNWViMzkzZWU5NWZhYjc0NjhhNzlkMTg5Iiwid2Vic2l0ZSI6InBoeXNpY3N3YWxsYWguY29tIiwibmFtZSI6IlBoeXNpY3N3YWxsYWgifSwiZW1haWwiOiJzaGl0dHVrdW1hcjM3QGdtYWlsLmNvbSIsInJvbGVzIjpbIjViMjdiZDk2NTg0MmY5NTBhNzc4YzZlZiJdLCJjb3VudHJ5R3JvdXAiOiJJTiIsInR5cGUiOiJVU0VSIn0sImlhdCI6MTc0MjIzNjg0MH0.oIubH2nR-onRJrzCAGcGU96tsmAzRYyXEnlaA4oIvcU"
    await editable.edit("<pre><code>**Enter CP or PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋**</code></pre>\n<pre><code>Send  `unknown`  for use default</code></pre>")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == '?':
        PW = pw_token
    else:
        PW = raw_text4
        
    await editable.edit("<pre><code>⚪Send ☞ jpg url for **Video Thumbnail** format</code></pre>\n<pre><code>🔘Send ☞ jpg url for **Document Thumbnail** format</code></pre>")
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
            # Replace parts of the URL as needed
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
                

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)


            elif "contentId=" in url or "master.m3u8&contentHashIdl=" in url:
                
                content = url.replace("https://", "").split("contentId=")[-1]

                if "master.m3u8&contentHashIdl=" in url:
                    content = url.split("master.m3u8&contentHashIdl=")[1]
                
                
                    
                
                headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': f'{raw_text4}',    
                    'accept-language': 'EN',
                    'api-version': '18',
                    'app-version': '1.4.73.2',
                    'build-number': '35',
                    'connection': 'Keep-Alive',
                    'content-type': 'application/json',
                    'device-details': 'Xiaomi_Redmi 7_SDK-32',
                    'device-id': 'c28d3cb16bbdac01',
                    'region': 'IN',
                    'user-agent': 'Mobile-Android',
                    'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                    'accept-encoding': 'gzip'
                }
                
                params = {
                    'contentId': content,
                    'offlineDownload': "false"
                }

                response = requests.get(
                    "https://api.classplusapp.com/cams/uploader/video/jw-signed-url",
                    params=params,
                    headers=headers
                ).json()
                
                if "testbook.com" in url or "classplusapp.com/drm" in url or "media-cdn.classplusapp.com/drm" in url:
                    final_url = res['drmUrls']['manifestUrl']
                else:
                    final_url = response["url"]
                    
                print("\nSigned URL:\n", final_url)
                print("response I'd\n", content)
                print("respose", response)
                print("Final URL\n", final_url)
            else:
                print("Invalid Link")
                
            
    
            if '/master.mpd' in url:
             url = f"https://master-api-v3.vercel.app/pw/m3u8v2?url={url}&token={raw_text4}&authorization={auth_token}&q={raw_text2}"
                
            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{name1[:60]}'
            
            
             
             
            #if 'cpvod.testbook.com' in url:
               #url = requests.get(f'http://api.masterapi.tech/akamai-player-v3?url={url}', headers={'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}).json()['url']
               #url0 = f"https://dragoapi.vercel.app/video/{url}"
            if "edge.api.brightcove.com/playback/v2" in url:
                vid_id = url.split("playback/v2")[1]
                url = f"https://edge.api.brightcove.com/playback/v1{vid_id}"
                
            if "/master.mpd" in url:
                cmd= f" yt-dlp -k --allow-unplayable-formats -f bestvideo.{quality} --fixup never {url} "
                print("counted")

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            #elif "youtube.com" in url or "youtu.be" in url:
                #cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

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
                                caption = ccimg,
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
        
                
                elif "youtu" in url:
                    try:
                        await bot.send_photo(chat_id=m.chat.id, photo=photoyt, caption=ccyt)
                        count +=1
                    except Exception as e:
                        await m.reply_text(str(e))    
                        time.sleep(1)    
                        continue

                
                else:
                    remaining_links = len(links) - count
                    progress = (count / len(links)) * 100
                    emoji_message = await show_random_emojis(message)
                    Show = f"🚀 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒...» {progress:.2f}%\n\n📥 𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 🚀.. »\n\n├──🎞️ 📊 Total Links = {len(links)}\n\n├──🎞️ ⚡️ Currently On = {str(count).zfill(3)}\n\n├──⏳ Remaining URL = {remaining_links}\n\n├──🎞️ Title:- {name}\n\n├──⌨️ Resolution » {raw_text2}\n\n├──🖼️ Thumbnail » {raw_text6}\n\n├── Url:  <a href= {url} >__**CLICK HERE**__</a>\n\n├──🤖 Bot Made By: 『ᴀɴᴋɪᴛ sʜᴀᴋʏᴀ』"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await emoji_message.delete()
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
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
    await m.reply_text("<pre><code>🔰Done🔰\n\nDownloaded By ⌈✨ 𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳 ✨⌋</code></pre>")
    


@bot.on_message(filters.command(["member","misthi"]) )
async def txt_handler(bot: Client, m: Message):
    user_id = m.from_user.id
    if user_id not in is_auth_user:
        await m.reply_text("**HEY BUDDY THIS IS ONLY FOR MY ADMINS  **")
    else:
        editable = await m.reply_text(f"<pre><code>**🔹Hi I am Poweful TXT Downloader📥 Bot.**</code></pre>\n<pre><code>🔹**Send me the TXT file and wait.**</code></pre>")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit ="𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳" 
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            links.append(i.split("://", 1))
        os.remove(x)
    except:
        await m.reply_text("<pre><code>Invalid file input.</code></pre>")
        os.remove(x)
        return
   
    await editable.edit(f"<pre><code>Total 🔗 links found are __**{len(links)}**__</code></pre>\n<pre><code>Send From where you want to download initial is `1`</code></pre>")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    try:
        arg = int(raw_text)
    except:
        arg = 1
    await editable.edit("<pre><code>**Enter Your Batch Name**</code></pre>\n<pre><code>Send `1` for use default.</code></pre>")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == '1':
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("<pre><code>╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ </code></pre>\n┣━━⪼ send `144`  for 144p\n┣━━⪼ send `240`  for 240p\n┣━━⪼ send `360`  for 360p\n┣━━⪼ send `480`  for 480p\n┣━━⪼ send `720`  for 720p\n┣━━⪼ send `1080` for 1080p\n<pre><code>╰━━⌈⚡[ 𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳 ]⚡⌋━━➣ </code></pre>")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    quality = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"

    await editable.edit("<pre><code>**Enter Your Name**</code></pre>\n<pre><code>Send `de` for use default</code></pre>")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    if raw_text3 == 'de':
        CR = credit
    else:
        CR = raw_text3

    pw_token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDI4NDE2NDAuNTQyLCJkYXRhIjp7Il9pZCI6IjY1OWZjZWU5YmI4YjFkMDAxOGFmYTExZCIsInVzZXJuYW1lIjoiODUzOTkyNjE5MCIsImZpcnN0TmFtZSI6IlNoaXR0dSIsImxhc3ROYW1lIjoiU2luZ2giLCJvcmdhbml6YXRpb24iOnsiX2lkIjoiNWViMzkzZWU5NWZhYjc0NjhhNzlkMTg5Iiwid2Vic2l0ZSI6InBoeXNpY3N3YWxsYWguY29tIiwibmFtZSI6IlBoeXNpY3N3YWxsYWgifSwiZW1haWwiOiJzaGl0dHVrdW1hcjM3QGdtYWlsLmNvbSIsInJvbGVzIjpbIjViMjdiZDk2NTg0MmY5NTBhNzc4YzZlZiJdLCJjb3VudHJ5R3JvdXAiOiJJTiIsInR5cGUiOiJVU0VSIn0sImlhdCI6MTc0MjIzNjg0MH0.oIubH2nR-onRJrzCAGcGU96tsmAzRYyXEnlaA4oIvcU"
    await editable.edit("<pre><code>**Enter PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋**</code></pre>\n<pre><code>Send  `unknown`  for use default</code></pre>")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == '?':
        PW = pw_token
    else:
        PW = raw_text4

    await editable.edit("<pre><code>⚪Send ☞ jpg url for **Video Thumbnail** format</code></pre>\n<pre><code>🔘Send ☞ jpg url for **Document Thumbnail** format</code></pre>")
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
            # Replace parts of the URL as needed
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
                

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'https://contentId=' in url:
                
                content = url.replace("https://", "").split("contentId=")[-1]
                
                if ".m3u8" in content:
                    content = content.split(".m3u8")[0]
                    
                
                headers = {
                    'host': 'api.classplusapp.com',
                    'x-access-token': raw_text4,    
                    'accept-language': 'EN',
                    'api-version': '18',
                    'app-version': '1.4.73.2',
                    'build-number': '35',
                    'connection': 'Keep-Alive',
                    'content-type': 'application/json',
                    'device-details': 'Xiaomi_Redmi 7_SDK-32',
                    'device-id': 'c28d3cb16bbdac01',
                    'region': 'IN',
                    'user-agent': 'Mobile-Android',
                    'webengage-luid': '00000187-6fe4-5d41-a530-26186858be4c',
                    'accept-encoding': 'gzip'
                }
                
                params = {
                    'contentId': content,
                    'offlineDownload': "false"
                }

                response = requests.get(
                    "https://api.classplusapp.com/cams/uploader/video/jw-signed-url",
                    params=params,
                    headers=headers
                ).json()
                
                if "testbook.com" in url or "classplusapp.com/drm" in url or "media-cdn.classplusapp.com/drm" in url:
                    url = res['drmUrls']['manifestUrl']
                else:
                    url = response["url"]
                    
                print("\nSigned URL:\n", url)
            else:
                print("Invalid Link")


    
                
            if '/master.mpd' in url:
             url = f"https://master-api-v3.vercel.app/pw/m3u8v2?url={url}&token={raw_text4}&authorization={auth_token}&q={raw_text2}"
                
            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{name1[:60]}'
            
            #if 'cpvod.testbook.com' in url:
               #url = requests.get(f'http://api.masterapi.tech/akamai-player-v3?url={url}', headers={'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}).json()['url']
               #url0 = f"https://dragoapi.vercel.app/video/{url}"
            if "edge.api.brightcove.com/playback/v2" in url:
                vid_id = url.split("playback/v2")[1]
                url = f"https://edge.api.brightcove.com/playback/v1{vid_id}"
                
            if "/master.mpd" in url:
                cmd= f" yt-dlp -k --allow-unplayable-formats -f bestvideo.{quality} --fixup never {url} "
                print("counted")

            
            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            #elif "youtube.com" in url or "youtu.be" in url:
                #cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

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

                elif any(img in url.lower() for img in ['.jpeg', '.png', '.jpg']):
                        try:
                            subprocess.run(['wget', url, '-O', f'{name}.jpg'], check=True)  # Fixing this line
                            await bot.send_photo(
                                chat_id=m.chat.id,
                                caption = ccimg,
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
                
                elif "youtu" in url:
                    try:
                        await bot.send_photo(chat_id=m.chat.id, photo=photoyt, caption=ccyt)
                        count +=1
                    except Exception as e:
                        await m.reply_text(str(e))    
                        time.sleep(1)    
                        continue
                        
                elif "apps-s3-prod.utkarshapp.com" in url or "PDF.pdf" in url:
                    try:
                        await bot.send_photo(chat_id=m.chat.id, photo=utkarsh, caption=ccukt)
                        count +=1
                    except Exception as e:
                        await m.reply_text(str(e))    
                        time.sleep(1)    
                        continue
                
                else:
                    remaining_links = len(links) - count
                    progress = (count / len(links)) * 100
                    emoji_message = await show_random_emojis(message)
                    Show = f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n ┃         📊 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒...»         ┃\n┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n┃🚀  Overall Progress:{progress:.2f}%┃\n┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n📥  𝐃𝐎𝐖𝐍𝐋𝐎𝐀𝐃 𝐒𝐓𝐀𝐓𝐔𝐒.. »      ┃\n┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n ┃ 📊 Total Links = {len(links)}\n⚡️ Currently On = {str(count).zfill(3)}\n⏳ Remaining URL = {remaining_links}\n┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n ┃ 📝 Title:- {name}\n ⌨️ Resolution » {raw_text2}\n 🖼️ Thumbnail » {raw_text6}\n┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n┃ 🔗 Url:  <a href= {url} >__**CLICK HERE**__</a>\n┣━━━━━━━━━━━━━━━━━━━━━━━━┫\n┃🤖 Bot Made By: 『ᴀɴᴋɪᴛ sʜᴀᴋʏᴀ』┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━┛"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await emoji_message.delete()
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
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
    await m.reply_text("<pre><code>🔰Done🔰\n\nDownloaded By ⌈✨ 𝐀𝐧𝐤𝐢𝐭 𝐒𝐡𝐚𝐤𝐲𝐚🇮🇳 ✨⌋</code></pre>")


def decode_jwt(token):
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload)
    return json.loads(decoded)



@bot.on_message(filters.command("token"))
async def token_details(client, message):

    try:
        token = message.text.split(" ", 1)[1]

        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)

        decoded = base64.urlsafe_b64decode(payload).decode()
        data = json.loads(decoded)

        pretty = json.dumps(data, indent=4)

        await message.reply(f"```\n{pretty}\n```")

    except Exception as e:
        await message.reply(f"❌ Invalid Token\n{e}")


@bot.on_message(filters.command("token2"))
async def token_info(client, message):

    try:
        token = message.text.split(" ", 1)[1]

        data = decode_jwt(token)

        name = data.get("name")
        user_id = data.get("id")
        org_id = data.get("orgId")
        mobile = data.get("mobile")
        org_code = data.get("orgCode")

        iat = data.get("iat")
        exp = data.get("exp")

        issued = datetime.datetime.fromtimestamp(iat)
        expiry = datetime.datetime.fromtimestamp(exp)

        now = datetime.datetime.now()

        status = "✅ VALID" if exp > int(now.timestamp()) else "❌ EXPIRED"

        reply = f"""
🔐 **Token Details**

👤 Name: `{name}`
🆔 User ID: `{user_id}`
🏫 Org ID: `{org_id}`
📱 Mobile: `{mobile}`
🔑 Org Code: `{org_code}`

🕒 Issued: `{issued}`
⌛ Expiry: `{expiry}`

⚡ Status: {status}
"""

        await message.reply(reply)

    except Exception as e:
        await message.reply(f"❌ Invalid Token\n\nError: {e}")



bot.run()
