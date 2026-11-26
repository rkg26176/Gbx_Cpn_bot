import ast
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import html
import inspect
import io
import json
import logging
import math
import os
import re
import secrets
import time
from typing import Any
import urllib.parse

import firebase_admin
from firebase_admin import credentials, db as firebase_db
import httpx
import qrcode
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ChatMemberStatus, ChatType
from telegram.error import Forbidden, RetryAfter, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8053042225"))

FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL",
    "https://gbx-cpn-bot-default-rtdb.asia-southeast1.firebasedatabase.app/",
).rstrip("/")

DEFAULT_FIREBASE_CRED_DICT: dict[str, Any] = {
    "type": "service_account",
    "project_id": "gbx-cpn-bot",
    "private_key_id": "5aa55f9031478f4b68e0fcf8939885c921da32be",
    "private_key": (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDl7jJzD62qX2BF\n"
        "cj4fOaf+a9YOa6WmIsfBMv1mmRxiPgwH9Qz4iHpCM5/V/w/vKhbpAUQ9mDDC49Pw\n"
        "czuqeOg5/yM+2lXo6pyi2+ilVNo9DryZF1b3uH8w1390T9SdLOblmwNKVG1zzPEE\n"
        "wMtdp91/xvIKDjXChkRvu7PqLmcrm5aZNlcQNQJH6qM8vvjI0vqG1t9Tr9FXUzHu\n"
        "cxI6NvoRw6jqrPuRLVb4qSJZZnuRH0g0olz3RyT8N2DHRrBicxVuuEGY8T2vPYgz\n"
        "97GcA8zi42O5Ms1J/SdKvsWqxi0OCbrzZXJV9Eo8p8H4QO7BetKeGWk/yZ6btZAj\n"
        "JHNe0tj/AgMBAAECggEAbcj6Fa5awYqgsQgHWWlyKSzcHC6R/W2F612pWJ+qyc3O\n"
        "eM4sz0568bksjEUpGo0CO2b7al2MisG1pI2g45ivaWHFNnGRq5C6EZjm0Gpfed/b\n"
        "dU2LnORe9rcuiB7F6fZSmTcWrxr41933Bsn3UFSikiwvzVVTnfn2G1OIaDyXzl2o\n"
        "ImqC48w6XYvuNfBYl69ySi3BsQm1RM3VXMZcvInM5VS8RJFpLL8ScTNIDFIILW9f\n"
        "MbF0X7Y5GpKKaFwLvzAr10fut2r9pA2Xehb0zu0wJt/JLQqvQ+DlmRXohpM4pa3Q\n"
        "vdjz+l20CCGA83ZEbF8NMNCCPIP0hGH8fys9gJOnoQKBgQD3nzIuMAONSJdcKRA5\n"
        "7Hhvh+zZnXg7ZsEN+CgKaIDm5fY8x+vzncGkZCaFEc50V/t4Dwt65OnXX/wAzCSM\n"
        "dxEAD0gNvrk7RKBbIBnsIpouShHoFA/c4anf87CBuSzPZx/BkyZEk4xzj34owxKc\n"
        "2ItIrE6PP6f+dKi6O+9V4Qb7CwKBgQDttcPYpnmpRpy2WyGFTIgDX8bgtfXTA9Hm\n"
        "4LKOle+5DmclknXIxp6XDpbknwxTRzcEVTrxxQyQ+4b1mqz0aROm5qfh6rKeIArO\n"
        "LjjRkRajkguAlGIHSxn3gozLxvY10cuFX0BPJLpAMkVwENS4+A75TjDs8HipvOfZ\n"
        "qC7kY7SyXQKBgHWNVb0nfggsVe6ib9mPsP0Bgics4k8Q0MVY8Wk/gzIaKXNhVVop\n"
        "oivwf3jcoy4INpEgU0rcMUbVgkS+pPsp6yAkIQilajoAsj+QVb4MDzW6ZBXQsFcj\n"
        "qglvHnP2/JbZVfIHcTtM8HhLvpCLSuK6yiSN6B2JEq9xokgG++/BDBdRAoGBAJ3Z\n"
        "KH7yNTG6CRByvXSl2F/dNtQ7IE0KaVUV+pwCZpiNPuNNOVekxOTsNDkGgInAbYE8\n"
        "E5M+VVTlIb5wAs+eAwW+ftbfIdMs1eAKA4LuBImDzo2Ievv62/hmwZYDvbUJZktf\n"
        "b/XeHqvIdiGvm4JkfpUAXi7IlGeqYI9BRjo1F2WlAoGBALWzIIXpkwq0bybc39sm\n"
        "jqgK1rwHnmZVXl3KQCZP0IUaDS2g2BviGnx+Iiklxk0NDMUGnzYlgx4UIyCFMr0x\n"
        "g5di9yhINzVT5Q6HfhecQZCrXTzdpttOjJHJnrqn9Tjvm/6mq+VcYO3vi7oXmZXw\n"
        "jKK+/tL8s0e4jq1bBwDE6Opa\n"
        "-----END PRIVATE KEY-----\n"
    ),
    "client_email": "firebase-adminsdk-fbsvc@gbx-cpn-bot.iam.gserviceaccount.com",
    "client_id": "102398893735172905250",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40gbx-cpn-bot.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

PORT = int(os.getenv("PORT", "8080"))

UPI_ID = "BHARATPE.8R0I1G1N4X31943@fbpe"
MERCHANT_NAME = "Merchant"

DEFAULT_BHARATPE_CONFIG = {
    "merchant_id": "62337062",
    "token": "1474e270a4c5416e97c57fa146261588",
    "token_alert_sent": False,
}

MAINTENANCE_MESSAGE = (
    "🙂 sʏsᴛᴇᴍ ᴜɴᴅᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "The bot is currently undergoing scheduled maintenance &amp; system upgrades.\n\n"
    "🔒 All operations are temporarily paused for public users.\n"
    "👑 Please check our official channels for real-time announcements when services resume!\n"
    "✨ ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ: @gbx_support_bot"
)

IST = timezone(timedelta(hours=5, minutes=30))
ORDERS_PER_PAGE = 10
USERS_PER_PAGE = 20
REFERRAL_REWARD_AMOUNT = 2.0
MIN_WALLET_TOPUP = 15.0
MAX_WALLET_TOPUP = 50000.0
MAX_UTR_ATTEMPTS = 3
PAYMENT_SESSION_TTL_SECONDS = 15 * 60

MAIN_CHANNEL_URL = "https://t.me/+6ByfGDRBKgsxMjZl"
SUPPORT_BOT_URL = "https://t.me/gbx_support_bot"

CHANNELS: dict[int, dict[str, str]] = {
    -1003332858806: {
        "name": "📢 GBX LOOT",
        "url": "https://t.me/+6ByfGDRBKgsxMjZl",
    },
    -1003630519339: {
        "name": "📢 GBX EARN",
        "url": "https://t.me/+OWrCoeF-JutmNjg1",
    },
    -1003197501531: {
        "name": "📢 GBX ZONE",
        "url": "https://t.me/+f2mWfDs6EUIxYTBl",
    },
    -1003862251237: {
        "name": "💬 Join Group Chat (GC)",
        "url": "https://t.me/+O_-kEF2f5f1kMjdl",
    },
}

JOINED_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}

# Menu button labels
BTN_STOCK = "📊 Stock Status"
BTN_BUY = "🛒 Buy Coupon"
BTN_PROFILE = "👤 My Profile"
BTN_ORDERS = "📦 My Orders"
BTN_LEADERBOARD = "🏆 Leaderboard"
BTN_REFER = "🤝 Refer & Earn"
BTN_SUPPORT = "🆘 Support"
BTN_WALLET = "💰 Wallet"
BTN_MAIN_CHANNELS = "📢 Our Main Channels"

# Concurrency locks
_USER_LOCKS: dict[int, asyncio.Lock] = {}
_INVENTORY_LOCK = asyncio.Lock()
_PROMO_LOCK = asyncio.Lock()
URL_DETECT_RE = re.compile(r"(https?://|www\.|t\.me/|telegram\.me/)", re.IGNORECASE)

_KB_SUPPORTS_STYLE = "style" in inspect.signature(KeyboardButton.__init__).parameters
_INLINE_SUPPORTS_STYLE = "style" in inspect.signature(InlineKeyboardButton.__init__).parameters


def get_user_lock(user_id: int) -> asyncio.Lock:
    lock = _USER_LOCKS.get(user_id)
    if lock is None:
        lock = asyncio.Lock()
        _USER_LOCKS[user_id] = lock
    return lock


def contains_url(text: str) -> bool:
    return bool(URL_DETECT_RE.search(text or ""))


def styled_kb_btn(text: str, style: str | None = None) -> KeyboardButton:
    if style and _KB_SUPPORTS_STYLE:
        return KeyboardButton(text=text, style=style)
    return KeyboardButton(text=text)


def styled_inline_btn(
    text: str,
    style: str | None = None,
    **kwargs: Any,
) -> InlineKeyboardButton:
    if style and _INLINE_SUPPORTS_STYLE:
        return InlineKeyboardButton(text=text, style=style, **kwargs)
    return InlineKeyboardButton(text=text, **kwargs)


def format_qty_expression(quantity: int) -> str:
    if quantity <= 1:
        return "1"
    return f"1 * {quantity}"


_QUOTE_OPEN_TO_CLOSE: dict[str, str] = {
    '"': '"',
    "'": "'",
    "`": "`",
    "“": "”",
    "‘": "’",
}


def _normalize_relaxed_json_quotes(raw_block: str) -> str:
    """Converts backticks, curly quotes, or Telegram-stripped unquoted keys/values into valid JSON."""
    out: list[str] = []
    n = len(raw_block)
    i = 0
    while i < n:
        ch = raw_block[i]
        if ch in _QUOTE_OPEN_TO_CLOSE:
            close_ch = _QUOTE_OPEN_TO_CLOSE[ch]
            j = i + 1
            buf: list[str] = []
            while j < n:
                c = raw_block[j]
                if c == "\\" and j + 1 < n:
                    nxt = raw_block[j + 1]
                    if nxt == '"':
                        buf.append('\\"')
                    elif nxt in ("'", "`"):
                        buf.append(nxt)
                    else:
                        buf.append("\\" + nxt)
                    j += 2
                    continue
                if c == close_ch:
                    break
                if c == '"':
                    buf.append('\\"')
                else:
                    buf.append(c)
                j += 1
            if j < n and raw_block[j] == close_ch:
                out.append('"' + "".join(buf) + '"')
                i = j + 1
                continue
        out.append(ch)
        i += 1
    normalized = "".join(out)
    # Quote unquoted keys (e.g. mobile: ...)
    normalized = re.sub(r'([\{\[,]\s*)([a-zA-Z0-9_$-]+)\s*:', r'\1"\2":', normalized)
    # Handle empty values left behind when Telegram strips `` (e.g. "name": , -> "name": "")
    normalized = re.sub(r':\s*(?=[,\}\]])', ': ""', normalized)
    # Quote unquoted scalar string/UUID/JWT values (e.g. "token": a5140d68-...)
    def _quote_unquoted_val(m: re.Match[str]) -> str:
        prefix = m.group(1)
        val = m.group(2).strip()
        if not val:
            return f'{prefix}""'
        if val in ("true", "false", "null") or re.fullmatch(r"-?\d+(\.\d+)?([eE][+-]?\d+)?", val):
            return f"{prefix}{val}"
        escaped_val = val.replace("\\", "\\\\").replace('"', '\\"')
        return f'{prefix}"{escaped_val}"'

    normalized = re.sub(
        r'(:\s*)([^"\[\{\}\],\s][^,\}\]]*?)(?=\s*[,\}\]])',
        _quote_unquoted_val,
        normalized,
    )
    # Remove trailing commas before } or ]
    normalized = re.sub(r",\s*([\}\]])", r"\1", normalized)
    return normalized


def _parse_structured_object(raw_block: str) -> tuple[bool, Any, bool]:
    """Parses ANY app's JSON/dict/list: standard (\"), single-quoted ('), backtick (`), curly quotes, or Telegram-stripped JSON.
    Returns (is_valid, parsed_obj, is_strict_json).
    """
    s = raw_block.strip()
    if len(s) < 2:
        return False, None, False
    if not ((s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]"))):
        return False, None, False

    # 1. Standard strict JSON
    try:
        parsed = json.loads(s)
        if isinstance(parsed, (dict, list)):
            return True, parsed, True
    except (ValueError, TypeError):
        pass

    # 2. Python dict/list literal (single-quoted strings, True/False/None)
    try:
        parsed_ast = ast.literal_eval(s)
        if isinstance(parsed_ast, (dict, list)):
            return True, parsed_ast, False
    except (ValueError, SyntaxError, TypeError):
        pass

    # 3. Backtick-quoted (`key`: `val`), Smart-quoted, or Telegram-stripped JSON from any app
    try:
        norm_s = _normalize_relaxed_json_quotes(s)
        parsed_norm = json.loads(norm_s)
        if isinstance(parsed_norm, (dict, list)):
            return True, parsed_norm, False
    except (ValueError, TypeError):
        pass

    # 4. Fallback: if it is a balanced { key: val } or [ ... ] block containing ":" (key-value structure)
    if s.startswith("{") and s.endswith("}") and ":" in s:
        return True, s, False

    return False, None, False


def is_valid_json_item(value: str) -> bool:
    ok, _, _ = _parse_structured_object(value)
    return ok


def _format_structured_block(raw_block: str, parsed_obj: Any, is_strict_json: bool) -> str:
    """Preserves original formatting for multi-line/custom-quoted blocks, or compact JSON for single-line."""
    s = raw_block.strip()
    if "\n" in s:
        return s
    if is_strict_json:
        return json.dumps(parsed_obj, ensure_ascii=False, separators=(",", ":"))
    return s


def _extract_balanced_json_blocks(text: str) -> tuple[list[str], str]:
    """Extracts single-line or multi-line JSON/dict objects & arrays for ANY app (supports \", ', `, “”, ‘’)."""
    extracted: list[str] = []
    remaining_chars: list[str] = []
    n = len(text)
    i = 0

    while i < n:
        ch = text[i]
        if ch in ("{", "["):
            open_ch = ch
            close_ch = "}" if ch == "{" else "]"
            depth = 0
            expected_close_quote: str | None = None
            escape = False
            j = i
            found_end = -1

            while j < n:
                c = text[j]
                if escape:
                    escape = False
                elif c == "\\":
                    if expected_close_quote is not None:
                        escape = True
                elif expected_close_quote is not None:
                    if c == expected_close_quote:
                        expected_close_quote = None
                else:
                    if c in _QUOTE_OPEN_TO_CLOSE:
                        expected_close_quote = _QUOTE_OPEN_TO_CLOSE[c]
                    elif c == open_ch:
                        depth += 1
                    elif c == close_ch:
                        depth -= 1
                        if depth == 0:
                            found_end = j
                            break
                j += 1

            if found_end != -1:
                candidate = text[i : found_end + 1].strip()
                ok, parsed, is_strict_json = _parse_structured_object(candidate)
                if ok:
                    if isinstance(parsed, list) and i == 0 and found_end == n - 1:
                        for elem in parsed:
                            if isinstance(elem, (dict, list)):
                                extracted.append(
                                    json.dumps(elem, ensure_ascii=False, separators=(",", ":"))
                                )
                            else:
                                s_el = str(elem).strip()
                                if s_el:
                                    extracted.append(s_el)
                    else:
                        extracted.append(
                            _format_structured_block(candidate, parsed, is_strict_json)
                        )
                    i = found_end + 1
                    continue

        remaining_chars.append(ch)
        i += 1

    return extracted, "".join(remaining_chars)


def parse_coupons_or_links(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    cleaned_items: list[str] = []
    seen: set[str] = set()

    stripped_all = raw_text.strip().lstrip("\ufeff")

    # 1. Extract all balanced JSON / dict / array blocks first (works for any app's JSON)
    json_blocks, leftover_text = _extract_balanced_json_blocks(stripped_all)
    for jb in json_blocks:
        if jb and jb not in seen:
            seen.add(jb)
            cleaned_items.append(jb)

    # 2. Parse any remaining non-JSON lines (coupon codes or URLs)
    for raw_line in leftover_text.splitlines():
        line = raw_line.strip()
        if not line or line in (",", ";"):
            continue

        ok, parsed, is_strict_json = _parse_structured_object(line)
        if ok:
            norm_j = _format_structured_block(line, parsed, is_strict_json)
            if norm_j not in seen:
                seen.add(norm_j)
                cleaned_items.append(norm_j)
            continue

        if (line.startswith("{") and line.endswith("}")) or (
            line.startswith("[") and line.endswith("]")
        ):
            if line not in seen:
                seen.add(line)
                cleaned_items.append(line)
            continue

        if "http://" in line.lower() or "https://" in line.lower():
            parts = [p.strip() for p in re.split(r"[\s,]+", line) if p.strip()]
        elif "," in line and " " not in line.replace(",", ""):
            parts = [p.strip() for p in line.split(",") if p.strip()]
        else:
            parts = [line]

        for item in parts:
            if not item.lower().startswith(("http://", "https://")) and not (
                item.startswith(("{", "[")) and item.endswith(("}", "]"))
            ):
                item = re.sub(r"^(?:\d+[\.\)\-:]\s*|[\-\*\•]\s*)", "", item).strip()
            if item and item not in seen:
                seen.add(item)
                cleaned_items.append(item)

    return cleaned_items


def code_to_firebase_key(code: str) -> str:
    stripped = code.strip()
    ok, parsed, _ = _parse_structured_object(stripped)
    if ok and isinstance(parsed, (dict, list)):
        try:
            stripped = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except (ValueError, TypeError):
            stripped = repr(parsed)
    return hashlib.sha256(stripped.encode("utf-8")).hexdigest()[:32]


# =====================================================================
# Firebase Realtime Database Initialization & Core Persistence
# =====================================================================


def init_firebase() -> None:
    if not firebase_admin._apps:
        env_json = os.getenv("FIREBASE_CRED_JSON", "").strip()
        if env_json:
            cred_dict = json.loads(env_json)
        else:
            cred_dict = DEFAULT_FIREBASE_CRED_DICT
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

    cfg_ref = firebase_db.reference("config/bharatpe")
    if cfg_ref.get() is None:
        cfg_ref.set(DEFAULT_BHARATPE_CONFIG)

    maint_ref = firebase_db.reference("config/maintenance_mode")
    if maint_ref.get() is None:
        maint_ref.set(False)


def fb_ref(path: str) -> firebase_db.Reference:
    return firebase_db.reference(path)


def is_maintenance_enabled() -> bool:
    val = fb_ref("config/maintenance_mode").get()
    return bool(val)


def set_maintenance_enabled(enabled: bool) -> None:
    fb_ref("config/maintenance_mode").set(bool(enabled))


async def guard_maintenance_mode(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Returns True if bot is blocked for this user due to Maintenance Mode."""
    user = update.effective_user
    if not user or user.id == ADMIN_ID:
        return False
    if not is_maintenance_enabled():
        return False

    if update.callback_query:
        try:
            await update.callback_query.answer(
                "System under maintenance. Please try again later.",
                show_alert=False,
            )
        except TelegramError:
            pass
        if update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=MAINTENANCE_MESSAGE,
                    parse_mode="HTML",
                )
            except TelegramError:
                pass
    elif update.message:
        try:
            await update.message.reply_text(
                text=MAINTENANCE_MESSAGE,
                parse_mode="HTML",
            )
        except TelegramError:
            pass
    return True


# =====================================================================
# BharatPe Config & Payment Verification Helpers (Stored in Firebase)
# =====================================================================


def load_bharatpe_config() -> dict[str, Any]:
    data = fb_ref("config/bharatpe").get()
    if not isinstance(data, dict):
        fb_ref("config/bharatpe").set(DEFAULT_BHARATPE_CONFIG)
        return DEFAULT_BHARATPE_CONFIG.copy()
    for k, v in DEFAULT_BHARATPE_CONFIG.items():
        data.setdefault(k, v)
    return data


def save_bharatpe_config(cfg: dict[str, Any]) -> None:
    fb_ref("config/bharatpe").update(cfg)


def extract_token_from_curl(curl_text: str) -> str | None:
    match = re.search(r"token:\s*([a-fA-F0-9]{20,})", curl_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def generate_upi_qr(amount: float, order_note: str = "OrderPayment") -> tuple[io.BytesIO, str]:
    params = {
        "pa": UPI_ID,
        "pn": MERCHANT_NAME,
        "am": f"{amount:.2f}",
        "cu": "INR",
        "tn": order_note,
    }
    upi_url = f"upi://pay?{urllib.parse.urlencode(params)}"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = io.BytesIO()
    bio.name = "qr.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio, upi_url


async def fetch_bharatpe_transactions(page_size: int = 15) -> tuple[int, list[dict[str, Any]]]:
    cfg = load_bharatpe_config()
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (24 * 60 * 60 * 1000)

    url = "https://payments-tesseract.bharatpe.in/api/v1/merchant/transactions"
    params = {
        "module": "PAYMENT_QR",
        "merchantId": cfg["merchant_id"],
        "sDate": start_ms,
        "eDate": now_ms,
        "pageSize": page_size,
        "pageCount": 0,
        "isFromOtDashboard": 1,
    }
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "origin": "https://enterprise.bharatpe.in",
        "referer": "https://enterprise.bharatpe.in/",
        "token": cfg["token"],
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
    except httpx.HTTPError as exc:
        logger.warning("BharatPe HTTP error: %s", exc)
        return 503, []

    if resp.status_code != 200:
        return resp.status_code, []

    data = resp.json()
    txns = data.get("data", {}).get("transactions", [])
    return 200, txns


async def verify_bharatpe_payment(utr: str, expected_amount: float) -> dict[str, Any]:
    status_code, transactions = await fetch_bharatpe_transactions(page_size=25)

    if status_code in (401, 403):
        return {"ok": False, "reason": "TOKEN_EXPIRED"}
    if status_code != 200:
        return {"ok": False, "reason": f"API_ERROR_{status_code}"}

    target_utr = utr.strip()
    for txn in transactions:
        txn_utr = str(txn.get("bankReferenceNo") or "").strip()
        txn_amount = float(txn.get("amount", 0))
        txn_status = str(txn.get("status", "")).upper()
        txn_type = str(txn.get("type", "")).upper()

        if txn_utr == target_utr and txn_status == "SUCCESS" and txn_type == "PAYMENT_RECV":
            if txn_amount + 1e-6 >= expected_amount:
                return {
                    "ok": True,
                    "amount": txn_amount,
                    "utr": txn_utr,
                    "payer": txn.get("payerName", "User"),
                }
            return {
                "ok": False,
                "reason": "AMOUNT_MISMATCH",
                "received_amount": txn_amount,
            }

    return {"ok": False, "reason": "NOT_FOUND"}


def is_within_bharatpe_check_window() -> bool:
    """Allows token check only between 06:00 and 24:00 IST (skips 00:00 to 06:00 IST)."""
    now_ist = datetime.now(IST)
    return 6 <= now_ist.hour < 24


async def token_health_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_within_bharatpe_check_window():
        return

    cfg = load_bharatpe_config()
    status_code, _ = await fetch_bharatpe_transactions(page_size=1)

    if status_code in (401, 403):
        if not cfg.get("token_alert_sent", False):
            cfg["token_alert_sent"] = True
            save_bharatpe_config(cfg)
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        "🚨 <b>BharatPe Token Expired!</b>\n\n"
                        "Please update the session token before users make payments.\n"
                        "Use /curl or send the browser <code>Copy as cURL</code> text / <code>.txt</code> file directly here."
                    ),
                    parse_mode="HTML",
                )
            except TelegramError as exc:
                logger.warning("Failed to send token alert to admin: %s", exc)
    elif status_code == 200 and cfg.get("token_alert_sent", False):
        cfg["token_alert_sent"] = False
        save_bharatpe_config(cfg)


# =====================================================================
# Firebase Bot Promo Coupons & User Refund Helpers
# =====================================================================


def create_bot_promo_coupon(amount: float, max_users: int) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    while True:
        code = f"GBX-{secrets.token_hex(3).upper()}-{secrets.token_hex(2).upper()}"
        if fb_ref(f"bot_promo_coupons/{code}").get() is None:
            break

    data = {
        "code": code,
        "amount": round(float(amount), 2),
        "max_users": int(max_users),
        "claimed_count": 0,
        "claimed_by": {},
        "is_active": True,
        "created_at": now_iso,
    }
    fb_ref(f"bot_promo_coupons/{code}").set(data)
    return data


def redeem_bot_promo_coupon(user_id: int, raw_code: str) -> dict[str, Any]:
    clean_code = raw_code.strip().upper()
    if not clean_code or not re.fullmatch(r"[A-Z0-9_-]{3,40}", clean_code):
        return {
            "ok": False,
            "reason": "Invalid coupon code format. Please check the code and try again.",
        }

    cref = fb_ref(f"bot_promo_coupons/{clean_code}")
    coupon = cref.get()
    if not isinstance(coupon, dict):
        return {
            "ok": False,
            "reason": "Coupon code not found or invalid.",
        }

    if not coupon.get("is_active", True):
        return {
            "ok": False,
            "reason": "This coupon code is no longer active.",
        }

    claimed_by = coupon.get("claimed_by")
    if not isinstance(claimed_by, dict):
        claimed_by = {}

    if str(user_id) in claimed_by:
        return {
            "ok": False,
            "reason": "You have already claimed this coupon code.",
        }

    max_users = int(coupon.get("max_users", 0))
    claimed_count = int(coupon.get("claimed_count", len(claimed_by)))
    if claimed_count >= max_users:
        cref.update({"is_active": False})
        return {
            "ok": False,
            "reason": "This coupon has reached its maximum user claim limit.",
        }

    amount = round(float(coupon.get("amount", 0.0)), 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    new_claimed_count = claimed_count + 1
    updates: dict[str, Any] = {
        f"claimed_by/{user_id}": {
            "user_id": user_id,
            "amount": amount,
            "claimed_at": now_iso,
        },
        "claimed_count": new_claimed_count,
    }
    if new_claimed_count >= max_users:
        updates["is_active"] = False
    cref.update(updates)

    uref = fb_ref(f"users/{user_id}")
    user = uref.get() or {}
    prev_avail = float(user.get("wallet_balance", 0.0))
    new_avail = round(prev_avail + amount, 2)
    ref_bal = float(user.get("referral_earnings", 0.0))
    uref.update({"wallet_balance": new_avail})

    return {
        "ok": True,
        "code": clean_code,
        "amount": amount,
        "previous_available_balance": prev_avail,
        "new_available_balance": new_avail,
        "referral_balance": ref_bal,
        "total_balance": round(new_avail + ref_bal, 2),
        "remaining_claims": max(0, max_users - new_claimed_count),
    }


def process_order_wallet_refund(order_id_query: str, refund_qty: int) -> dict[str, Any]:
    order = lookup_order_by_id(order_id_query)
    if not isinstance(order, dict):
        return {"ok": False, "reason": "Order ID not found in database."}

    actual_order_id = str(order.get("order_id", "")).strip()
    if not actual_order_id:
        return {"ok": False, "reason": "Invalid order record."}

    total_qty = int(order.get("quantity", 1))
    already_refunded_qty = int(order.get("refunded_qty", 0))
    refundable_qty = max(0, total_qty - already_refunded_qty)

    if refundable_qty <= 0:
        return {
            "ok": False,
            "reason": f"All {total_qty} unit(s) for Order {actual_order_id} have already been refunded.",
        }

    if refund_qty < 1 or refund_qty > refundable_qty:
        return {
            "ok": False,
            "reason": f"Invalid refund quantity. You can refund between 1 and {refundable_qty} unit(s).",
        }

    unit_price = float(order.get("price", 0.0))
    refund_amount = round(unit_price * refund_qty, 2)
    target_user_id = int(order.get("user_id", 0))
    if not target_user_id:
        return {"ok": False, "reason": "Customer User ID missing on this order."}

    uref = fb_ref(f"users/{target_user_id}")
    user_data = uref.get()
    if not isinstance(user_data, dict):
        return {"ok": False, "reason": f"User {target_user_id} record not found in Firebase."}

    now_iso = datetime.now(timezone.utc).isoformat()
    refund_id = f"RFD{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"

    prev_avail = float(user_data.get("wallet_balance", 0.0))
    new_avail = round(prev_avail + refund_amount, 2)
    ref_bal = float(user_data.get("referral_earnings", 0.0))
    uref.update({"wallet_balance": new_avail})

    new_refunded_qty = already_refunded_qty + refund_qty
    prev_refunded_amt = float(order.get("refunded_amount", 0.0))
    new_refunded_amt = round(prev_refunded_amt + refund_amount, 2)

    fb_ref(f"orders/{actual_order_id}").update(
        {
            "refunded_qty": new_refunded_qty,
            "refunded_amount": new_refunded_amt,
            "last_refund_id": refund_id,
            "last_refund_at": now_iso,
        }
    )

    fb_ref(f"admin_refunds/{refund_id}").set(
        {
            "refund_id": refund_id,
            "order_id": actual_order_id,
            "user_id": target_user_id,
            "username": user_data.get("username", ""),
            "first_name": user_data.get("first_name", ""),
            "coupon_name": str(order.get("coupon_name", "")),
            "refund_qty": refund_qty,
            "total_order_qty": total_qty,
            "unit_price": unit_price,
            "refund_amount": refund_amount,
            "admin_id": ADMIN_ID,
            "created_at": now_iso,
        }
    )

    return {
        "ok": True,
        "refund_id": refund_id,
        "order_id": actual_order_id,
        "user_id": target_user_id,
        "username": user_data.get("username"),
        "first_name": user_data.get("first_name"),
        "coupon_name": str(order.get("coupon_name", "Item")),
        "refund_qty": refund_qty,
        "total_order_qty": total_qty,
        "unit_price": unit_price,
        "refund_amount": refund_amount,
        "previous_available_balance": prev_avail,
        "new_available_balance": new_avail,
        "referral_balance": ref_bal,
        "total_balance": round(new_avail + ref_bal, 2),
    }


# =====================================================================
# Firebase Inventory (Folders, Sub-Items, Direct Slots & Withdrawals)
# =====================================================================


def _count_unsold_codes_map(
    codes_tree: dict[str, Any] | None,
) -> dict[tuple[str, str], int]:
    counts: dict[tuple[str, str], int] = {}
    if not isinstance(codes_tree, dict):
        return counts
    for item in codes_tree.values():
        if not isinstance(item, dict):
            continue
        if item.get("is_sold") or item.get("is_withdrawn"):
            continue
        sid = str(item.get("slot_id") or "")
        sub_id = str(item.get("sub_id") or "")
        if sid:
            counts[(sid, sub_id)] = counts.get((sid, sub_id), 0) + 1
    return counts


def fetch_all_slots() -> list[dict[str, Any]]:
    slots_raw = fb_ref("slots").get()
    if not isinstance(slots_raw, dict):
        return []
    codes_raw = fb_ref("coupon_codes").get()
    counts = _count_unsold_codes_map(codes_raw)

    result: list[dict[str, Any]] = []
    for slot_id, slot in slots_raw.items():
        if not isinstance(slot, dict):
            continue
        is_folder = bool(slot.get("is_folder", False))
        if is_folder:
            subs_raw = slot.get("sub_items") or {}
            sub_list: list[dict[str, Any]] = []
            folder_total_stock = 0
            if isinstance(subs_raw, dict):
                for sub_id, sub in subs_raw.items():
                    if not isinstance(sub, dict):
                        continue
                    stk = counts.get((slot_id, sub_id), 0)
                    folder_total_stock += stk
                    sub_list.append(
                        {
                            "sub_id": sub_id,
                            "slot_id": slot_id,
                            "name": str(sub.get("name", "Item")),
                            "description": str(sub.get("description", "")),
                            "price": float(sub.get("price", 0.0)),
                            "stock": stk,
                            "created_at": str(sub.get("created_at", "")),
                        }
                    )
            sub_list.sort(key=lambda x: x.get("created_at", ""))
            result.append(
                {
                    "slot_id": slot_id,
                    "name": str(slot.get("name", "Folder")),
                    "is_folder": True,
                    "sub_items": sub_list,
                    "stock": folder_total_stock,
                    "created_at": str(slot.get("created_at", "")),
                }
            )
        else:
            stk = counts.get((slot_id, ""), 0)
            result.append(
                {
                    "slot_id": slot_id,
                    "name": str(slot.get("name", "Coupon")),
                    "description": str(slot.get("description", "")),
                    "price": float(slot.get("price", 0.0)),
                    "is_folder": False,
                    "stock": stk,
                    "created_at": str(slot.get("created_at", "")),
                }
            )

    result.sort(key=lambda x: x.get("created_at", ""))
    return result


def fetch_sellable_item(slot_id: str, sub_id: str = "") -> dict[str, Any] | None:
    slot = fb_ref(f"slots/{slot_id}").get()
    if not isinstance(slot, dict):
        return None
    codes_raw = fb_ref("coupon_codes").get()
    counts = _count_unsold_codes_map(codes_raw)

    if bool(slot.get("is_folder", False)):
        if not sub_id:
            return None
        sub = fb_ref(f"slots/{slot_id}/sub_items/{sub_id}").get()
        if not isinstance(sub, dict):
            return None
        stk = counts.get((slot_id, sub_id), 0)
        return {
            "slot_id": slot_id,
            "sub_id": sub_id,
            "folder_name": str(slot.get("name", "")),
            "name": str(sub.get("name", "Item")),
            "display_name": f"{slot.get('name', '')} / {sub.get('name', '')}",
            "description": str(sub.get("description", "")),
            "price": float(sub.get("price", 0.0)),
            "stock": stk,
        }

    stk = counts.get((slot_id, ""), 0)
    return {
        "slot_id": slot_id,
        "sub_id": "",
        "folder_name": "",
        "name": str(slot.get("name", "Coupon")),
        "display_name": str(slot.get("name", "Coupon")),
        "description": str(slot.get("description", "")),
        "price": float(slot.get("price", 0.0)),
        "stock": stk,
    }


def delete_slot_or_subitem_in_firebase(slot_id: str, sub_id: str = "") -> dict[str, Any]:
    """Deletes a standalone slot, a sub-item inside a folder, or a whole folder + its codes."""
    slot = fb_ref(f"slots/{slot_id}").get()
    if not isinstance(slot, dict):
        return {"ok": False, "reason": "Slot not found."}

    codes_ref = fb_ref("coupon_codes")
    all_codes = codes_ref.get()
    code_deletes: dict[str, Any] = {}

    if sub_id:
        sub = fb_ref(f"slots/{slot_id}/sub_items/{sub_id}").get()
        if not isinstance(sub, dict):
            return {"ok": False, "reason": "Sub-item not found."}
        deleted_name = f"{slot.get('name', '')} / {sub.get('name', '')}"
        if isinstance(all_codes, dict):
            for ckey, cdata in all_codes.items():
                if (
                    isinstance(cdata, dict)
                    and str(cdata.get("slot_id") or "") == slot_id
                    and str(cdata.get("sub_id") or "") == sub_id
                ):
                    code_deletes[ckey] = None
        if code_deletes:
            codes_ref.update(code_deletes)
        fb_ref(f"slots/{slot_id}/sub_items/{sub_id}").delete()
        return {"ok": True, "deleted_name": deleted_name}

    deleted_name = str(slot.get("name", "Slot"))
    if isinstance(all_codes, dict):
        for ckey, cdata in all_codes.items():
            if isinstance(cdata, dict) and str(cdata.get("slot_id") or "") == slot_id:
                code_deletes[ckey] = None
    if code_deletes:
        codes_ref.update(code_deletes)
    fb_ref(f"slots/{slot_id}").delete()
    return {"ok": True, "deleted_name": deleted_name}


def update_item_price_in_firebase(
    slot_id: str, sub_id: str, new_price: float
) -> dict[str, Any]:
    item = fetch_sellable_item(slot_id, sub_id)
    if not item:
        return {"ok": False, "reason": "Selected item or slot not found."}

    old_price = float(item["price"])
    if sub_id:
        fb_ref(f"slots/{slot_id}/sub_items/{sub_id}").update({"price": float(new_price)})
    else:
        fb_ref(f"slots/{slot_id}").update({"price": float(new_price)})

    return {
        "ok": True,
        "display_name": str(item["display_name"]),
        "old_price": old_price,
        "new_price": float(new_price),
    }


def _find_matching_withdrawn_keys(
    codes: list[str], source_filename: str = ""
) -> set[str]:
    """Finds Firebase keys of codes that were withdrawn by admin so they can be re-added without duplicate error."""
    target_keys = {code_to_firebase_key(c) for c in codes}
    if not target_keys:
        return set()

    matched_withdrawn_keys: set[str] = set()
    clean_fname = source_filename.strip()

    all_withdrawals = fb_ref("admin_withdrawals").get()
    if isinstance(all_withdrawals, dict):
        for wdata in all_withdrawals.values():
            if not isinstance(wdata, dict):
                continue
            w_codes = wdata.get("codes") or []
            if not isinstance(w_codes, list) or not w_codes:
                continue
            w_keys = {code_to_firebase_key(str(wc)) for wc in w_codes}
            w_fname = str(wdata.get("filename") or "").strip()
            w_qty = int(wdata.get("quantity", len(w_codes)))

            if clean_fname and w_fname == clean_fname and len(codes) == w_qty:
                matched_withdrawn_keys.update(target_keys & w_keys)
            elif target_keys.issubset(w_keys):
                matched_withdrawn_keys.update(target_keys & w_keys)

    return matched_withdrawn_keys


def _insert_unique_codes_into_firebase(
    slot_id: str, sub_id: str, codes: list[str], source_filename: str = ""
) -> tuple[int, int]:
    now_iso = datetime.now(timezone.utc).isoformat()
    codes_ref = fb_ref("coupon_codes")
    existing_all = codes_ref.get()
    existing_dict = existing_all if isinstance(existing_all, dict) else {}

    re_addable_withdrawn_keys = _find_matching_withdrawn_keys(codes, source_filename)

    updates: dict[str, Any] = {}
    added = 0
    duplicates = 0

    for code in codes:
        ckey = code_to_firebase_key(code)
        if ckey in updates:
            duplicates += 1
            continue

        existing_entry = existing_dict.get(ckey)
        if isinstance(existing_entry, dict):
            if existing_entry.get("is_withdrawn") and (
                ckey in re_addable_withdrawn_keys or not existing_entry.get("is_sold")
            ):
                updates[ckey] = {
                    "slot_id": slot_id,
                    "sub_id": sub_id,
                    "code": code,
                    "is_sold": False,
                    "is_withdrawn": False,
                    "created_at": now_iso,
                }
                added += 1
                continue
            duplicates += 1
            continue

        updates[ckey] = {
            "slot_id": slot_id,
            "sub_id": sub_id,
            "code": code,
            "is_sold": False,
            "is_withdrawn": False,
            "created_at": now_iso,
        }
        added += 1

    if updates:
        codes_ref.update(updates)
    return added, duplicates


def create_slot_or_folder_item(
    main_name: str,
    is_folder: bool,
    sub_name: str,
    description: str,
    unit_price: float,
    codes: list[str],
    source_filename: str = "",
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_main = main_name.strip()
    slots_raw = fb_ref("slots").get()
    slots_dict = slots_raw if isinstance(slots_raw, dict) else {}

    if not is_folder:
        existing_slot_id = None
        for sid, sdata in slots_dict.items():
            if (
                isinstance(sdata, dict)
                and not sdata.get("is_folder", False)
                and str(sdata.get("name", "")).strip().lower() == clean_main.lower()
            ):
                existing_slot_id = sid
                break

        if existing_slot_id:
            slot_id = existing_slot_id
            fb_ref(f"slots/{slot_id}").update(
                {
                    "description": description.strip(),
                    "price": float(unit_price),
                }
            )
        else:
            slot_id = f"slot_{secrets.token_hex(4)}"
            fb_ref(f"slots/{slot_id}").set(
                {
                    "name": clean_main,
                    "is_folder": False,
                    "description": description.strip(),
                    "price": float(unit_price),
                    "created_at": now_iso,
                }
            )

        added, dups = _insert_unique_codes_into_firebase(
            slot_id, "", codes, source_filename=source_filename
        )
        item_info = fetch_sellable_item(slot_id, "")
        return {
            "is_folder": False,
            "slot_id": slot_id,
            "sub_id": "",
            "folder_name": "",
            "item_name": clean_main,
            "price": float(unit_price),
            "added_count": added,
            "duplicate_count": dups,
            "total_stock": item_info["stock"] if item_info else added,
        }

    folder_id = None
    for sid, sdata in slots_dict.items():
        if (
            isinstance(sdata, dict)
            and bool(sdata.get("is_folder", False))
            and str(sdata.get("name", "")).strip().lower() == clean_main.lower()
        ):
            folder_id = sid
            break

    if not folder_id:
        folder_id = f"fld_{secrets.token_hex(4)}"
        fb_ref(f"slots/{folder_id}").set(
            {
                "name": clean_main,
                "is_folder": True,
                "created_at": now_iso,
            }
        )

    clean_sub = sub_name.strip()
    sub_id = None
    existing_subs = fb_ref(f"slots/{folder_id}/sub_items").get()
    if isinstance(existing_subs, dict):
        for s_id, s_obj in existing_subs.items():
            if (
                isinstance(s_obj, dict)
                and str(s_obj.get("name", "")).strip().lower() == clean_sub.lower()
            ):
                sub_id = s_id
                break

    if sub_id:
        fb_ref(f"slots/{folder_id}/sub_items/{sub_id}").update(
            {
                "description": description.strip(),
                "price": float(unit_price),
            }
        )
    else:
        sub_id = f"sub_{secrets.token_hex(4)}"
        fb_ref(f"slots/{folder_id}/sub_items/{sub_id}").set(
            {
                "name": clean_sub,
                "description": description.strip(),
                "price": float(unit_price),
                "created_at": now_iso,
            }
        )

    added, dups = _insert_unique_codes_into_firebase(
        folder_id, sub_id, codes, source_filename=source_filename
    )
    item_info = fetch_sellable_item(folder_id, sub_id)
    return {
        "is_folder": True,
        "slot_id": folder_id,
        "sub_id": sub_id,
        "folder_name": clean_main,
        "item_name": clean_sub,
        "price": float(unit_price),
        "added_count": added,
        "duplicate_count": dups,
        "total_stock": item_info["stock"] if item_info else added,
    }


def direct_add_to_target(
    slot_id: str, sub_id: str, codes: list[str], source_filename: str = ""
) -> dict[str, Any]:
    item = fetch_sellable_item(slot_id, sub_id)
    if not item:
        return {"ok": False, "reason": "Target slot or sub-item not found."}

    added, dups = _insert_unique_codes_into_firebase(
        slot_id, sub_id, codes, source_filename=source_filename
    )
    updated = fetch_sellable_item(slot_id, sub_id)
    return {
        "ok": True,
        "display_name": item["display_name"],
        "price": item["price"],
        "added_count": added,
        "duplicate_count": dups,
        "total_stock": updated["stock"] if updated else added,
    }


def withdraw_codes_for_admin(
    slot_id: str, sub_id: str, requested_qty: int | None
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    item = fetch_sellable_item(slot_id, sub_id)
    if not item:
        return {"ok": False, "reason": "Target slot or sub-item not found."}

    codes_ref = fb_ref("coupon_codes")
    all_codes = codes_ref.get()
    if not isinstance(all_codes, dict):
        return {"ok": False, "reason": "No codes available in stock."}

    available_entries: list[tuple[str, str, str]] = []
    for ckey, cdata in all_codes.items():
        if not isinstance(cdata, dict):
            continue
        if cdata.get("is_sold") or cdata.get("is_withdrawn"):
            continue
        if str(cdata.get("slot_id") or "") == slot_id and str(cdata.get("sub_id") or "") == sub_id:
            available_entries.append(
                (str(cdata.get("created_at", "")), ckey, str(cdata.get("code", "")))
            )

    avail_count = len(available_entries)
    if avail_count == 0:
        return {"ok": False, "reason": "0 codes available in this slot."}

    if requested_qty is None:
        take_qty = avail_count
    else:
        if requested_qty < 1 or requested_qty > avail_count:
            return {
                "ok": False,
                "reason": f"Requested quantity ({requested_qty}) exceeds available live stock ({avail_count}).",
            }
        take_qty = requested_qty

    available_entries.sort(key=lambda x: x[0])
    chosen = available_entries[:take_qty]

    withdrawal_id = f"WDR{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(item["display_name"])).strip("_") or "codes"
    export_filename = f"{safe_slug}_{take_qty}_codes.txt"

    updates: dict[str, Any] = {}
    withdrawn_list: list[str] = []

    for _, ckey, code_val in chosen:
        updates[f"{ckey}/is_withdrawn"] = True
        updates[f"{ckey}/withdrawal_id"] = withdrawal_id
        updates[f"{ckey}/withdrawn_by"] = ADMIN_ID
        updates[f"{ckey}/withdrawn_at"] = now_iso
        withdrawn_list.append(code_val)

    codes_ref.update(updates)
    fb_ref(f"admin_withdrawals/{withdrawal_id}").set(
        {
            "withdrawal_id": withdrawal_id,
            "admin_id": ADMIN_ID,
            "slot_id": slot_id,
            "sub_id": sub_id,
            "item_name": item["display_name"],
            "filename": export_filename,
            "quantity": take_qty,
            "codes": withdrawn_list,
            "created_at": now_iso,
        }
    )

    return {
        "ok": True,
        "withdrawal_id": withdrawal_id,
        "display_name": item["display_name"],
        "filename": export_filename,
        "withdrawn_count": take_qty,
        "remaining_stock": avail_count - take_qty,
        "codes": withdrawn_list,
    }


def _allocate_codes_from_firebase(
    slot_id: str,
    sub_id: str,
    quantity: int,
    order_id: str,
    user_id: int,
    now_iso: str,
) -> list[str] | None:
    codes_ref = fb_ref("coupon_codes")
    all_codes = codes_ref.get()
    if not isinstance(all_codes, dict):
        return None

    matching_entries: list[tuple[str, str, str]] = []
    for ckey, cdata in all_codes.items():
        if not isinstance(cdata, dict):
            continue
        if cdata.get("is_sold") or cdata.get("is_withdrawn"):
            continue
        if str(cdata.get("slot_id") or "") == slot_id and str(cdata.get("sub_id") or "") == sub_id:
            matching_entries.append(
                (str(cdata.get("created_at", "")), ckey, str(cdata.get("code", "")))
            )

    if len(matching_entries) < quantity:
        return None

    matching_entries.sort(key=lambda x: x[0])
    chosen = matching_entries[:quantity]

    updates: dict[str, Any] = {}
    delivered: list[str] = []
    for _, ckey, code_val in chosen:
        updates[f"{ckey}/is_sold"] = True
        updates[f"{ckey}/order_id"] = order_id
        updates[f"{ckey}/sold_to"] = user_id
        updates[f"{ckey}/sold_at"] = now_iso
        delivered.append(code_val)

    codes_ref.update(updates)
    return delivered


# =====================================================================
# Firebase Users, Referrals, Wallet Deposits & Orders Persistence
# =====================================================================


def ensure_user_record(
    user_id: int,
    username: str | None,
    first_name: str | None,
    referrer_id: int | None = None,
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    uref = fb_ref(f"users/{user_id}")
    existing = uref.get()

    if isinstance(existing, dict):
        uref.update({"username": username or "", "first_name": first_name or ""})
        existing["username"] = username or ""
        existing["first_name"] = first_name or ""
        return existing

    valid_referrer: int | None = None
    initial_status = "none"
    if referrer_id and referrer_id != user_id:
        ref_user = fb_ref(f"users/{referrer_id}").get()
        if isinstance(ref_user, dict):
            valid_referrer = referrer_id
            initial_status = "pending"

    new_user = {
        "user_id": user_id,
        "username": username or "",
        "first_name": first_name or "",
        "wallet_balance": 0.0,
        "referrals_count": 0,
        "referral_earnings": 0.0,
        "referred_by": valid_referrer,
        "referral_status": initial_status,
        "referral_reason": "",
        "created_at": now_iso,
    }
    uref.set(new_user)
    return new_user


def get_user_row(user_id: int) -> dict[str, Any] | None:
    data = fb_ref(f"users/{user_id}").get()
    return data if isinstance(data, dict) else None


def claim_referral_reward_if_eligible(user_id: int) -> dict[str, Any]:
    uref = fb_ref(f"users/{user_id}")
    user = uref.get()
    if not isinstance(user, dict):
        return {"rewarded": False}

    status = str(user.get("referral_status", "none"))
    referrer_id = user.get("referred_by")

    if status != "pending" or not referrer_id or int(referrer_id) == user_id:
        return {"rewarded": False}

    ref_uid = int(referrer_id)
    ref_uref = fb_ref(f"users/{ref_uid}")
    ref_data = ref_uref.get()
    if not isinstance(ref_data, dict):
        uref.update({"referral_status": "none"})
        return {"rewarded": False}

    referee_earn = round(float(user.get("referral_earnings", 0.0)) + REFERRAL_REWARD_AMOUNT, 2)
    uref.update(
        {
            "referral_earnings": referee_earn,
            "referral_status": "rewarded",
            "referral_reason": "Verified channel membership",
        }
    )

    new_ref_earn = round(float(ref_data.get("referral_earnings", 0.0)) + REFERRAL_REWARD_AMOUNT, 2)
    new_ref_cnt = int(ref_data.get("referrals_count", 0)) + 1
    ref_uref.update(
        {
            "referral_earnings": new_ref_earn,
            "referrals_count": new_ref_cnt,
        }
    )

    return {
        "rewarded": True,
        "referrer_id": ref_uid,
        "amount": REFERRAL_REWARD_AMOUNT,
    }


def fetch_all_registered_users() -> list[dict[str, Any]]:
    users_raw = fb_ref("users").get()
    if not isinstance(users_raw, dict):
        return []
    users_list: list[dict[str, Any]] = []
    for uid_key, udata in users_raw.items():
        if not isinstance(udata, dict):
            continue
        uid = int(udata.get("user_id") or uid_key)
        users_list.append(
            {
                "user_id": uid,
                "username": str(udata.get("username") or "").strip(),
                "first_name": str(udata.get("first_name") or "").strip(),
                "wallet_balance": float(udata.get("wallet_balance", 0.0)),
                "referral_earnings": float(udata.get("referral_earnings", 0.0)),
                "created_at": str(udata.get("created_at", "")),
            }
        )
    users_list.sort(key=lambda x: x.get("created_at", ""))
    return users_list


def lookup_order_by_id(query_id: str) -> dict[str, Any] | None:
    clean_id = query_id.strip().upper()
    if not clean_id:
        return None
    direct = fb_ref(f"orders/{clean_id}").get()
    if isinstance(direct, dict):
        return direct

    all_orders = fb_ref("orders").get()
    if isinstance(all_orders, dict):
        for oid, odata in all_orders.items():
            if not isinstance(odata, dict):
                continue
            if (
                str(oid).upper() == clean_id
                or str(odata.get("order_id", "")).upper() == clean_id
                or str(odata.get("txid", "")).upper() == clean_id
            ):
                return odata
    return None


def create_payment_session(
    user_id: int,
    amount: float,
    chat_id: int,
    purpose: str = "wallet",
    slot_id: str = "",
    sub_id: str = "",
    quantity: int = 1,
) -> tuple[dict[str, Any], list[str]]:
    now_ts = int(time.time())
    expires_ts = now_ts + PAYMENT_SESSION_TTL_SECONDS
    txid = f"TXN{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"

    deps_ref = fb_ref("wallet_deposits")
    all_deps = deps_ref.get()
    cancelled_txids: list[str] = []
    cancel_updates: dict[str, Any] = {}

    if isinstance(all_deps, dict):
        for old_id, dep in all_deps.items():
            if (
                isinstance(dep, dict)
                and int(dep.get("user_id", 0)) == user_id
                and dep.get("status") == "pending"
            ):
                cancelled_txids.append(old_id)
                cancel_updates[f"{old_id}/status"] = "cancelled"

    if cancel_updates:
        deps_ref.update(cancel_updates)

    session_data = {
        "txid": txid,
        "user_id": user_id,
        "chat_id": chat_id,
        "qr_message_id": None,
        "purpose": purpose,
        "slot_id": slot_id,
        "sub_id": sub_id,
        "quantity": int(quantity),
        "amount": float(amount),
        "utr": "",
        "attempts": 0,
        "status": "pending",
        "created_at": now_ts,
        "expires_at": expires_ts,
        "verified_at": "",
    }
    deps_ref.child(txid).set(session_data)
    return session_data, cancelled_txids


def attach_qr_message_id(txid: str, qr_message_id: int) -> None:
    fb_ref(f"wallet_deposits/{txid}").update({"qr_message_id": qr_message_id})


def get_deposit_session(txid: str, user_id: int | None = None) -> dict[str, Any] | None:
    row = fb_ref(f"wallet_deposits/{txid}").get()
    if not isinstance(row, dict):
        return None
    if user_id is not None and int(row.get("user_id", 0)) != user_id:
        return None
    return row


def mark_deposit_expired(txid: str) -> dict[str, Any] | None:
    dref = fb_ref(f"wallet_deposits/{txid}")
    row = dref.get()
    if not isinstance(row, dict) or row.get("status") != "pending":
        return None
    dref.update({"status": "expired"})
    row["status"] = "expired"
    return row


def cancel_deposit_session(txid: str, user_id: int) -> None:
    dref = fb_ref(f"wallet_deposits/{txid}")
    row = dref.get()
    if (
        isinstance(row, dict)
        and int(row.get("user_id", 0)) == user_id
        and row.get("status") == "pending"
    ):
        dref.update({"status": "cancelled"})


def is_utr_already_used(utr: str) -> bool:
    clean_utr = utr.strip()
    return fb_ref(f"used_utrs/{clean_utr}").get() is not None


def record_utr_attempt_and_check_limit(
    txid: str, user_id: int, utr: str, increment_attempt: bool = True
) -> tuple[bool, int, str]:
    now_ts = int(time.time())
    dref = fb_ref(f"wallet_deposits/{txid}")
    row = dref.get()
    if not isinstance(row, dict) or int(row.get("user_id", 0)) != user_id:
        return False, 0, "Payment session not found. Please start a new session."

    status = str(row.get("status", ""))
    attempts = int(row.get("attempts", 0))

    if status == "verified":
        return False, attempts, "This payment session has already been verified."
    if status == "expired":
        return (
            False,
            attempts,
            "⚠️ Payment QR Expired — Your payment session has timed out. Please start a new purchase to generate a fresh QR code.",
        )
    if status != "pending":
        return (
            False,
            attempts,
            "This payment session was cancelled or closed. Please generate a new QR code.",
        )

    if now_ts > int(row.get("expires_at", 0)):
        dref.update({"status": "expired"})
        return (
            False,
            attempts,
            "⚠️ Payment QR Expired — Your payment session has timed out. Please start a new purchase to generate a fresh QR code.",
        )

    if increment_attempt:
        if attempts >= MAX_UTR_ATTEMPTS:
            dref.update({"status": "failed"})
            return (
                False,
                attempts,
                "Maximum UTR submission limit (3 attempts) reached for this order. Please start a new session.",
            )
        attempts += 1
        dref.update({"utr": utr.strip(), "attempts": attempts})

    return True, attempts, ""


def finalize_wallet_deposit(
    txid: str, user_id: int, utr: str, credited_amount: float
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_utr = utr.strip()

    dref = fb_ref(f"wallet_deposits/{txid}")
    dep = dref.get()
    if not isinstance(dep, dict) or dep.get("status") == "verified":
        return {"ok": False, "reason": "ALREADY_PROCESSED"}

    if is_utr_already_used(clean_utr):
        return {"ok": False, "reason": "DUPLICATE_UTR"}

    uref = fb_ref(f"users/{user_id}")
    user = uref.get() or {}
    prev_available = float(user.get("wallet_balance", 0.0))
    new_available = round(prev_available + float(credited_amount), 2)
    ref_bal = float(user.get("referral_earnings", 0.0))

    fb_ref(f"used_utrs/{clean_utr}").set(
        {"txid": txid, "user_id": user_id, "amount": float(credited_amount), "verified_at": now_iso}
    )
    dref.update({"status": "verified", "utr": clean_utr, "verified_at": now_iso})
    uref.update({"wallet_balance": new_available})

    return {
        "ok": True,
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "previous_available_balance": prev_available,
        "new_available_balance": new_available,
        "referral_balance": ref_bal,
    }


def finalize_upi_coupon_purchase(
    txid: str, user_id: int, utr: str, paid_amount: float
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_utr = utr.strip()
    order_id = f"ORD{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"

    dref = fb_ref(f"wallet_deposits/{txid}")
    dep = dref.get()
    if not isinstance(dep, dict) or dep.get("status") == "verified":
        return {"ok": False, "reason": "ALREADY_PROCESSED"}

    if is_utr_already_used(clean_utr):
        return {"ok": False, "reason": "DUPLICATE_UTR"}

    slot_id = str(dep.get("slot_id") or "")
    sub_id = str(dep.get("sub_id") or "")
    quantity = int(dep.get("quantity") or 1)

    uref = fb_ref(f"users/{user_id}")
    user_row = uref.get() or {}

    fb_ref(f"used_utrs/{clean_utr}").set(
        {"txid": txid, "user_id": user_id, "amount": float(paid_amount), "verified_at": now_iso}
    )
    dref.update({"status": "verified", "utr": clean_utr, "verified_at": now_iso})

    item = fetch_sellable_item(slot_id, sub_id)
    delivered_codes = (
        _allocate_codes_from_firebase(slot_id, sub_id, quantity, order_id, user_id, now_iso)
        if item
        else None
    )

    if not item or delivered_codes is None:
        prev_avail = float(user_row.get("wallet_balance", 0.0))
        new_avail = round(prev_avail + float(paid_amount), 2)
        ref_bal = float(user_row.get("referral_earnings", 0.0))
        uref.update({"wallet_balance": new_avail})
        return {
            "ok": True,
            "fallback_credited": True,
            "previous_available_balance": prev_avail,
            "new_available_balance": new_avail,
            "referral_balance": ref_bal,
            "username": user_row.get("username"),
            "first_name": user_row.get("first_name"),
        }

    unit_price = float(item["price"])
    total_price = round(unit_price * quantity, 2)
    display_name = str(item["display_name"])

    fb_ref(f"orders/{order_id}").set(
        {
            "order_id": order_id,
            "txid": txid,
            "utr": clean_utr,
            "payment_method": "UPI",
            "user_id": user_id,
            "username": user_row.get("username", ""),
            "first_name": user_row.get("first_name", ""),
            "slot_id": slot_id,
            "sub_id": sub_id,
            "coupon_name": display_name,
            "price": unit_price,
            "quantity": quantity,
            "total_price": total_price,
            "delivered_codes": delivered_codes,
            "created_at": now_iso,
        }
    )

    remaining_bal = round(
        float(user_row.get("wallet_balance", 0.0))
        + float(user_row.get("referral_earnings", 0.0)),
        2,
    )
    return {
        "ok": True,
        "fallback_credited": False,
        "order_id": order_id,
        "txid": txid,
        "utr": clean_utr,
        "payment_method": "UPI",
        "coupon_name": display_name,
        "unit_price": unit_price,
        "quantity": quantity,
        "total_price": total_price,
        "delivered_codes": delivered_codes,
        "username": user_row.get("username"),
        "first_name": user_row.get("first_name"),
        "remaining_total_balance": remaining_bal,
    }


def execute_wallet_coupon_purchase(
    user_id: int, slot_id: str, sub_id: str, quantity: int
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    order_id = f"ORD{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"
    txid = f"TXN{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(3).upper()}"

    item = fetch_sellable_item(slot_id, sub_id)
    if not item:
        return {"ok": False, "reason": "COUPON_NOT_FOUND"}

    avail_stock = int(item["stock"])
    if avail_stock < quantity or quantity <= 0:
        return {
            "ok": False,
            "reason": "INSUFFICIENT_STOCK",
            "available_stock": avail_stock,
        }

    unit_price = float(item["price"])
    total_price = round(unit_price * quantity, 2)

    uref = fb_ref(f"users/{user_id}")
    user_row = uref.get()
    if not isinstance(user_row, dict):
        return {"ok": False, "reason": "USER_NOT_FOUND"}

    avail_bal = float(user_row.get("wallet_balance", 0.0))
    ref_bal = float(user_row.get("referral_earnings", 0.0))
    total_bal = round(avail_bal + ref_bal, 2)

    if total_bal + 1e-6 < total_price:
        return {
            "ok": False,
            "reason": "INSUFFICIENT_BALANCE",
            "total_balance": total_bal,
            "required": total_price,
        }

    delivered_codes = _allocate_codes_from_firebase(
        slot_id, sub_id, quantity, order_id, user_id, now_iso
    )
    if delivered_codes is None:
        return {"ok": False, "reason": "INSUFFICIENT_STOCK", "available_stock": 0}

    if avail_bal >= total_price:
        new_avail = round(avail_bal - total_price, 2)
        new_ref = ref_bal
    else:
        rem_to_deduct = round(total_price - avail_bal, 2)
        new_avail = 0.0
        new_ref = max(0.0, round(ref_bal - rem_to_deduct, 2))

    uref.update({"wallet_balance": new_avail, "referral_earnings": new_ref})

    display_name = str(item["display_name"])
    fb_ref(f"orders/{order_id}").set(
        {
            "order_id": order_id,
            "txid": txid,
            "utr": "",
            "payment_method": "Wallet",
            "user_id": user_id,
            "username": user_row.get("username", ""),
            "first_name": user_row.get("first_name", ""),
            "slot_id": slot_id,
            "sub_id": sub_id,
            "coupon_name": display_name,
            "price": unit_price,
            "quantity": quantity,
            "total_price": total_price,
            "delivered_codes": delivered_codes,
            "created_at": now_iso,
        }
    )

    return {
        "ok": True,
        "order_id": order_id,
        "txid": txid,
        "payment_method": "Wallet",
        "coupon_name": display_name,
        "unit_price": unit_price,
        "quantity": quantity,
        "total_price": total_price,
        "delivered_codes": delivered_codes,
        "new_available_balance": new_avail,
        "new_referral_balance": new_ref,
        "remaining_total_balance": round(new_avail + new_ref, 2),
        "username": user_row.get("username"),
        "first_name": user_row.get("first_name"),
    }


def fetch_user_profile_stats(user_id: int) -> dict[str, Any]:
    now_local = datetime.now().astimezone()
    today_prefix = now_local.strftime("%Y-%m-%d")

    user_row = fb_ref(f"users/{user_id}").get()
    user_dict = user_row if isinstance(user_row, dict) else {}

    all_orders = fb_ref("orders").get()
    user_orders: list[dict[str, Any]] = []
    if isinstance(all_orders, dict):
        for o in all_orders.values():
            if isinstance(o, dict) and int(o.get("user_id", 0)) == user_id:
                user_orders.append(o)

    total_orders = len(user_orders)
    today_spent = 0.0
    previous_days_spent = 0.0
    total_spent = 0.0

    for o in user_orders:
        amount = float(o.get("price", 0.0)) * int(o.get("quantity", 1))
        total_spent += amount
        raw_ts = str(o.get("created_at", ""))
        try:
            dt = datetime.fromisoformat(raw_ts).astimezone()
            order_date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            order_date_str = raw_ts[:10]

        if order_date_str == today_prefix:
            today_spent += amount
        else:
            previous_days_spent += amount

    available_bal = float(user_dict.get("wallet_balance", 0.0))
    referral_bal = float(user_dict.get("referral_earnings", 0.0))

    return {
        "user_id": user_id,
        "username": user_dict.get("username") or None,
        "wallet_balance": available_bal,
        "referral_earnings": referral_bal,
        "total_balance": round(available_bal + referral_bal, 2),
        "total_orders": total_orders,
        "today_spent": round(today_spent, 2),
        "previous_days_spent": round(previous_days_spent, 2),
        "total_spent": round(total_spent, 2),
        "referrals_count": int(user_dict.get("referrals_count", 0)),
    }


def fetch_user_orders_page(user_id: int, page: int = 0) -> tuple[list[dict[str, Any]], int, int]:
    safe_page = max(0, page)
    all_orders = fb_ref("orders").get()
    user_orders: list[dict[str, Any]] = []
    if isinstance(all_orders, dict):
        for o in all_orders.values():
            if isinstance(o, dict) and int(o.get("user_id", 0)) == user_id:
                user_orders.append(o)

    user_orders.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    total_orders = len(user_orders)
    total_pages = max(1, (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE)
    if safe_page >= total_pages:
        safe_page = total_pages - 1

    start_idx = safe_page * ORDERS_PER_PAGE
    page_slice = user_orders[start_idx : start_idx + ORDERS_PER_PAGE]

    items: list[dict[str, Any]] = []
    for r in page_slice:
        raw_ts = str(r.get("created_at", ""))
        try:
            dt = datetime.fromisoformat(raw_ts).astimezone()
            date_str = dt.strftime("%d %b %Y")
            time_str = dt.strftime("%I:%M:%S %p")
        except ValueError:
            date_str = raw_ts
            time_str = ""
        items.append(
            {
                "order_id": str(r.get("order_id", "")),
                "coupon_name": str(r.get("coupon_name", "")),
                "price": float(r.get("price", 0.0)),
                "quantity": int(r.get("quantity", 1)),
                "date_str": date_str,
                "time_str": time_str,
            }
        )
    return items, total_orders, safe_page


def fetch_leaderboard(limit: int = 10) -> list[dict[str, Any]]:
    users_raw = fb_ref("users").get()
    orders_raw = fb_ref("orders").get()
    if not isinstance(orders_raw, dict):
        return []

    users_map = users_raw if isinstance(users_raw, dict) else {}
    agg: dict[int, dict[str, Any]] = {}

    for o in orders_raw.values():
        if not isinstance(o, dict):
            continue
        uid = int(o.get("user_id", 0))
        if not uid:
            continue
        qty = int(o.get("quantity", 0))
        spend = float(o.get("price", 0.0)) * qty
        if uid not in agg:
            uinfo = users_map.get(str(uid), {})
            agg[uid] = {
                "user_id": uid,
                "username": uinfo.get("username") or o.get("username") or None,
                "first_name": uinfo.get("first_name") or o.get("first_name") or "User",
                "total_coupons": 0,
                "total_spend": 0.0,
            }
        agg[uid]["total_coupons"] += qty
        agg[uid]["total_spend"] = round(agg[uid]["total_spend"] + spend, 2)

    ranked = [v for v in agg.values() if v["total_coupons"] > 0]
    ranked.sort(key=lambda x: (x["total_coupons"], x["total_spend"]), reverse=True)
    return ranked[:limit]


def format_username(username: str | None) -> str:
    if username:
        return f"@{html.escape(username)}"
    return "Not set"


def build_delivered_codes_file(
    codes: list[Any], base_label: str
) -> io.BytesIO:
    """Builds a downloadable .json or .txt BytesIO buffer when quantity > 1."""
    clean_items = [str(raw).strip() for raw in codes if str(raw).strip()]
    parsed_strict_objs: list[Any] = []
    all_strict_json = bool(clean_items)

    for c in clean_items:
        ok, parsed, is_strict = _parse_structured_object(c)
        if ok and is_strict:
            parsed_strict_objs.append(parsed)
        else:
            all_strict_json = False
            break

    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", base_label).strip("_") or "order"

    if all_strict_json:
        content_str = json.dumps(parsed_strict_objs, indent=2, ensure_ascii=False)
        bio = io.BytesIO(content_str.encode("utf-8"))
        bio.name = f"{safe_slug}_{len(clean_items)}_items.json"
    else:
        formatted_lines: list[str] = []
        for c in clean_items:
            ok, parsed, is_strict = _parse_structured_object(c)
            if ok and is_strict and "\n" not in c:
                formatted_lines.append(json.dumps(parsed, indent=2, ensure_ascii=False))
            else:
                formatted_lines.append(c)
        content_str = "\n\n".join(formatted_lines) if any(is_valid_json_item(x) for x in clean_items) else "\n".join(formatted_lines)
        bio = io.BytesIO(content_str.encode("utf-8"))
        bio.name = f"{safe_slug}_{len(clean_items)}_codes.txt"

    bio.seek(0)
    return bio


def format_delivered_codes_block(codes: list[Any]) -> str:
    if len(codes) > 1:
        return f"• <i>{len(codes)} items attached in the file below.</i>"
    lines: list[str] = []
    for raw in codes:
        c = str(raw).strip()
        ok, parsed, is_strict = _parse_structured_object(c)
        if ok:
            if is_strict and "\n" not in c:
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            else:
                pretty = c
            lines.append(f"<pre>{html.escape(pretty)}</pre>")
        else:
            lines.append(f"• <code>{html.escape(c)}</code>")
    return "\n".join(lines)


async def send_order_attachment_if_multi(
    bot: Any,
    chat_id: int,
    res: dict[str, Any],
) -> None:
    codes = res.get("delivered_codes") or []
    if len(codes) <= 1:
        return
    bio = build_delivered_codes_file(
        codes, base_label=str(res.get("order_id") or res.get("coupon_name") or "order")
    )
    try:
        await bot.send_document(
            chat_id=chat_id,
            document=bio,
            caption=(
                f"📄 <b>Order ID:</b> <code>{html.escape(str(res.get('order_id', '')))}</code>\n"
                f"• <b>Item:</b> {html.escape(str(res.get('coupon_name', '')))}\n"
                f"• <b>Delivered Quantity:</b> {len(codes)}"
            ),
            parse_mode="HTML",
        )
    except TelegramError as exc:
        logger.error("Failed to send multi-item order file to %s: %s", chat_id, exc)


# =====================================================================
# QR Auto-Expiry Background Job
# =====================================================================


def cancel_expiry_job(context: ContextTypes.DEFAULT_TYPE, txid: str) -> None:
    if not context.job_queue:
        return
    for job in context.job_queue.get_jobs_by_name(f"qr_expire:{txid}"):
        job.schedule_removal()


def schedule_expiry_job(
    job_queue: Any, txid: str, delay_seconds: float
) -> None:
    if not job_queue:
        return
    for job in job_queue.get_jobs_by_name(f"qr_expire:{txid}"):
        job.schedule_removal()
    job_queue.run_once(
        qr_expiry_timeout_callback,
        when=max(1.0, float(delay_seconds)),
        data={"txid": txid},
        name=f"qr_expire:{txid}",
    )


async def qr_expiry_timeout_callback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data if context.job else {}
    txid = str(job_data.get("txid", ""))
    if not txid:
        return

    expired_row = mark_deposit_expired(txid)
    if not expired_row:
        return

    chat_id = expired_row.get("chat_id") or expired_row.get("user_id")
    qr_msg_id = expired_row.get("qr_message_id")
    amount = float(expired_row.get("amount", 0.0))

    if chat_id and qr_msg_id:
        try:
            await context.bot.edit_message_caption(
                chat_id=chat_id,
                message_id=qr_msg_id,
                caption=(
                    f"⛔ <b>Payment QR Expired</b>\n\n"
                    f"• <b>Order / TXID:</b> <code>{html.escape(txid)}</code>\n"
                    f"• <b>Amount:</b> ₹{amount:.2f}\n\n"
                    "⚠️ <b>Payment QR Expired:</b> Your payment session has timed out. "
                    "Please start a new purchase to generate a fresh QR code."
                ),
                reply_markup=None,
                parse_mode="HTML",
            )
        except TelegramError:
            pass

    if chat_id:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⛔ <b>Order ID / TXID:</b> <code>{html.escape(txid)}</code>\n\n"
                    "⚠️ <b>Payment QR Expired</b>\n"
                    "Your payment session has timed out. Please start a new purchase to generate a fresh QR code."
                ),
                parse_mode="HTML",
            )
        except TelegramError as exc:
            logger.warning("Failed to send QR expiry notice for %s: %s", txid, exc)


def restore_pending_expiry_jobs(job_queue: Any) -> None:
    if not job_queue:
        return
    now_ts = int(time.time())
    all_deps = fb_ref("wallet_deposits").get()
    if not isinstance(all_deps, dict):
        return
    for txid, dep in all_deps.items():
        if isinstance(dep, dict) and dep.get("status") == "pending":
            remaining = max(1, int(dep.get("expires_at", now_ts)) - now_ts)
            schedule_expiry_job(job_queue, txid, remaining)


# =====================================================================
# Admin Notification Helpers (Logs sent directly to ADMIN_ID = 8053042225)
# =====================================================================


async def notify_admin_wallet_delivery(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user_id: int,
    first_name: str | None,
    username: str | None,
    txid: str,
    utr: str,
    payer_name: str,
    credited_amount: float,
    previous_available: float,
    new_available: float,
    referral_balance: float,
) -> None:
    now_ist = datetime.now(IST).strftime("%d %b %Y, %I:%M:%S %p IST")
    safe_name = html.escape(first_name or "User")
    safe_username = format_username(username)
    safe_payer = html.escape(payer_name or "Unknown")
    total_bal = new_available + referral_balance

    log_text = (
        "📥 <b>WALLET TOP-UP DELIVERED &amp; VERIFIED</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Order / Transaction ID:</b> <code>{html.escape(txid)}</code>\n"
        f"• <b>12-Digit UTR:</b> <code>{html.escape(utr)}</code>\n"
        f"• <b>UPI Payer Name:</b> {safe_payer}\n\n"
        "<b>Customer Details</b>\n"
        f"• <b>Name:</b> {safe_name}\n"
        f"• <b>Telegram User ID:</b> <code>{user_id}</code>\n"
        f"• <b>Username:</b> {safe_username}\n\n"
        "<b>Financial Summary</b>\n"
        f"• <b>Amount Credited:</b> <b>₹{credited_amount:.2f}</b>\n"
        f"• <b>Previous Available Balance:</b> ₹{previous_available:.2f}\n"
        f"• <b>Updated Available Balance:</b> <b>₹{new_available:.2f}</b>\n"
        f"• <b>Referral Balance:</b> ₹{referral_balance:.2f}\n"
        f"• <b>Total Combined Balance:</b> <b>₹{total_bal:.2f}</b>\n\n"
        f"• <b>Timestamp:</b> {now_ist}"
    )
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=log_text,
            parse_mode="HTML",
        )
    except TelegramError as exc:
        logger.error("Failed to send admin wallet delivery log to %s: %s", ADMIN_ID, exc)


async def notify_admin_coupon_order_delivery(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    user_id: int,
    first_name: str | None,
    username: str | None,
    order_id: str,
    txid: str,
    payment_method: str,
    utr: str | None,
    coupon_name: str,
    quantity: int,
    total_price: float,
    delivered_codes: list[str],
    remaining_total_balance: float,
) -> None:
    now_ist = datetime.now(IST).strftime("%d %b %Y, %I:%M:%S %p IST")
    safe_name = html.escape(first_name or "User")
    safe_username = format_username(username)
    codes_block = format_delivered_codes_block(delivered_codes)
    utr_line = f"• <b>12-Digit UTR:</b> <code>{html.escape(utr)}</code>\n" if utr else ""

    log_text = (
        "📦 <b>COUPON ORDER DELIVERED TO USER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Order ID:</b> <code>{html.escape(order_id)}</code>\n"
        f"• <b>Transaction ID:</b> <code>{html.escape(txid)}</code>\n"
        f"• <b>Payment Method:</b> <b>{html.escape(payment_method)}</b>\n"
        f"{utr_line}"
        f"• <b>Product / Item:</b> <b>{html.escape(coupon_name)}</b>\n"
        f"• <b>Quantity:</b> <b>{format_qty_expression(quantity)}</b> ({quantity})\n"
        f"• <b>Amount Paid:</b> <b>₹{total_price:.2f}</b>\n\n"
        "<b>Customer Details</b>\n"
        f"• <b>Name:</b> {safe_name}\n"
        f"• <b>Telegram User ID:</b> <code>{user_id}</code>\n"
        f"• <b>Username:</b> {safe_username}\n"
        f"• <b>Remaining Wallet Balance:</b> ₹{remaining_total_balance:.2f}\n\n"
        "<b>Exact Coupon(s) / Link(s) / JSON Delivered to User</b>\n"
        f"{codes_block}\n\n"
        f"• <b>Timestamp:</b> {now_ist}"
    )
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=log_text,
            parse_mode="HTML",
        )
        if len(delivered_codes) > 1:
            bio = build_delivered_codes_file(delivered_codes, base_label=order_id)
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=bio,
                caption=f"📄 Admin Copy — Order {order_id} ({len(delivered_codes)} items)",
            )
    except TelegramError as exc:
        logger.error("Failed to send admin order delivery log to %s: %s", ADMIN_ID, exc)


# =====================================================================
# Colored Keyboards (Solid Red / Green / Sky-Blue) & Message Formatters
# =====================================================================


def build_main_menu_keyboard() -> ReplyKeyboardMarkup:
    rows = [
        [
            styled_kb_btn(BTN_STOCK, style="primary"),       # Sky Blue
            styled_kb_btn(BTN_BUY, style="success"),         # Solid Green
        ],
        [
            styled_kb_btn(BTN_PROFILE, style="primary"),     # Blue
            styled_kb_btn(BTN_ORDERS, style="primary"),      # Blue
        ],
        [
            styled_kb_btn(BTN_LEADERBOARD, style="primary"), # Blue
            styled_kb_btn(BTN_REFER, style="success"),       # Solid Green
        ],
        [
            styled_kb_btn(BTN_SUPPORT, style="danger"),      # Solid Red
            styled_kb_btn(BTN_WALLET, style="success"),      # Solid Green
        ],
        [
            styled_kb_btn(BTN_MAIN_CHANNELS, style="primary"),  # Blue
        ],
    ]
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        input_field_placeholder="Select an option from the menu...",
    )


def build_admin_inbox_menu_keyboard() -> InlineKeyboardMarkup:
    """Broadcast, User List, Check Order ID, Maintenance Mode, Create Coupon for Bot, Refund User + Cancel button."""
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="📢 Broadcast",
                    style="success",
                    callback_data="adm_broadcast",
                ),
                styled_inline_btn(
                    text="👥 User List",
                    style="primary",
                    callback_data="adm_users:0",
                ),
            ],
            [
                styled_inline_btn(
                    text="🔍 Check Order ID",
                    style="primary",
                    callback_data="adm_check_order",
                ),
                styled_inline_btn(
                    text="🛠️ Maintenance Mode",
                    style="primary",
                    callback_data="adm_maintenance",
                ),
            ],
            [
                styled_inline_btn(
                    text="🎟️ Create Coupon for Bot",
                    style="success",
                    callback_data="adm_create_coupon",
                ),
                styled_inline_btn(
                    text="💸 Refund User",
                    style="primary",
                    callback_data="adm_refund_user",
                ),
            ],
            [
                styled_inline_btn(
                    text="❌ Cancel",
                    style="danger",
                    callback_data="back_to_home",
                )
            ],
        ]
    )


def build_admin_maintenance_toggle_keyboard() -> InlineKeyboardMarkup:
    active = is_maintenance_enabled()
    if active:
        toggle_btn = styled_inline_btn(
            text="🟢 Maintenance Mode: ON (Tap to Turn OFF)",
            style="success",
            callback_data="adm_maint_toggle",
        )
    else:
        toggle_btn = styled_inline_btn(
            text="🔴 Maintenance Mode: OFF (Tap to Turn ON)",
            style="danger",
            callback_data="adm_maint_toggle",
        )
    return InlineKeyboardMarkup(
        [
            [toggle_btn],
            [
                styled_inline_btn(
                    text="❌ Cancel",
                    style="danger",
                    callback_data="adm_menu",
                )
            ],
        ]
    )


def format_admin_maintenance_message() -> str:
    state_txt = "<b>ON (Green)</b> — Public users are paused." if is_maintenance_enabled() else "<b>OFF (Red)</b> — Bot is live for users."
    return (
        "🛠️ <b>Maintenance Mode Control</b>\n\n"
        f"• <b>Current Status:</b> {state_txt}\n\n"
        "Tap the toggle button below to switch ON / OFF:"
    )


def build_admin_users_pagination_keyboard(
    page: int, total_users: int
) -> InlineKeyboardMarkup:
    total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            styled_inline_btn(
                text="⏮️ Prev", style="primary", callback_data=f"adm_users:{page - 1}"
            )
        )
    if page + 1 < total_pages:
        nav_row.append(
            styled_inline_btn(
                text="⏭️ Next", style="primary", callback_data=f"adm_users:{page + 1}"
            )
        )
    rows: list[list[InlineKeyboardButton]] = []
    if nav_row:
        rows.append(nav_row)
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back", style="primary", callback_data="adm_menu"
            ),
            styled_inline_btn(
                text="❌ Cancel", style="danger", callback_data="back_to_home"
            ),
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="➕ New Slot", style="success", callback_data="ap_new_slot"
                ),
                styled_inline_btn(
                    text="⚡ Direct Add Coupon",
                    style="primary",
                    callback_data="ap_direct_add",
                ),
            ],
            [
                styled_inline_btn(
                    text="📥 Download Codes",
                    style="success",
                    callback_data="ap_dl_codes",
                ),
                styled_inline_btn(
                    text="💲 Change Price Per Unit",
                    style="primary",
                    callback_data="ap_change_price",
                ),
            ],
            [
                styled_inline_btn(
                    text="🗑️ Delete Slots",
                    style="danger",
                    callback_data="ap_del_slots",
                ),
                styled_inline_btn(
                    text="📊 Check Live Quantity",
                    style="primary",
                    callback_data="ap_check_qty",
                ),
            ],
            [
                styled_inline_btn(
                    text="🏠 Back to Home",
                    style="danger",
                    callback_data="back_to_home",
                )
            ],
        ]
    )


def build_admin_delete_slots_keyboard() -> InlineKeyboardMarkup:
    slots = fetch_all_slots()
    rows: list[list[InlineKeyboardButton]] = []
    for sl in slots:
        sid = str(sl["slot_id"])
        name = str(sl["name"])
        stk = int(sl["stock"])
        if sl.get("is_folder"):
            rows.append(
                [
                    styled_inline_btn(
                        text=f"📁 {name} (Folder • {stk} total)",
                        style="primary",
                        callback_data=f"ap_del_fld:{sid}",
                    )
                ]
            )
        else:
            price = float(sl["price"])
            rows.append(
                [
                    styled_inline_btn(
                        text=f"🎟️ {name} — ₹{price:g} (Qty: {stk})",
                        style="danger",
                        callback_data=f"ap_del_ask:{sid}:",
                    )
                ]
            )
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Admin Panel",
                style="primary",
                callback_data="ap_home",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_delete_subitems_keyboard(folder_slot: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = str(folder_slot["slot_id"])
    rows: list[list[InlineKeyboardButton]] = []
    for sub in folder_slot.get("sub_items", []):
        sub_id = str(sub["sub_id"])
        name = str(sub["name"])
        price = float(sub["price"])
        stk = int(sub["stock"])
        rows.append(
            [
                styled_inline_btn(
                    text=f"🎟️ {name} — ₹{price:g} (Qty: {stk})",
                    style="danger",
                    callback_data=f"ap_del_ask:{sid}:{sub_id}",
                )
            ]
        )
    rows.append(
        [
            styled_inline_btn(
                text=f"🗑️ Delete Entire Folder ({stk_total})",
                style="danger",
                callback_data=f"ap_del_ask:{sid}:ALL",
            )
            if (stk_total := int(folder_slot.get("stock", 0))) >= 0
            else styled_inline_btn(
                text="🗑️ Delete Entire Folder",
                style="danger",
                callback_data=f"ap_del_ask:{sid}:ALL",
            )
        ]
    )
    rows.append(
        [
            styled_inline_btn(
                text="⬅️ Back",
                style="primary",
                callback_data="ap_del_slots",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_delete_confirm_keyboard(sid: str, sub_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="✅ Confirm Delete",
                    style="danger",
                    callback_data=f"ap_del_yes:{sid}:{sub_id}",
                ),
                styled_inline_btn(
                    text="❌ Cancel",
                    style="primary",
                    callback_data="ap_del_slots",
                ),
            ]
        ]
    )


def build_admin_price_slots_keyboard() -> InlineKeyboardMarkup:
    slots = fetch_all_slots()
    rows: list[list[InlineKeyboardButton]] = []
    for sl in slots:
        sid = str(sl["slot_id"])
        name = str(sl["name"])
        if sl.get("is_folder"):
            rows.append(
                [
                    styled_inline_btn(
                        text=f"📁 {name} (Folder)",
                        style="primary",
                        callback_data=f"ap_prc_fld:{sid}",
                    )
                ]
            )
        else:
            price = float(sl["price"])
            rows.append(
                [
                    styled_inline_btn(
                        text=f"🎟️ {name} — ₹{price:g}/unit",
                        style="success",
                        callback_data=f"ap_prc_itm:{sid}:",
                    )
                ]
            )
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Admin Panel",
                style="danger",
                callback_data="ap_home",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_price_subitems_keyboard(folder_slot: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = str(folder_slot["slot_id"])
    rows: list[list[InlineKeyboardButton]] = []
    for sub in folder_slot.get("sub_items", []):
        sub_id = str(sub["sub_id"])
        name = str(sub["name"])
        price = float(sub["price"])
        rows.append(
            [
                styled_inline_btn(
                    text=f"🎟️ {name} — ₹{price:g}/unit",
                    style="success",
                    callback_data=f"ap_prc_itm:{sid}:{sub_id}",
                )
            ]
        )
    rows.append(
        [
            styled_inline_btn(
                text="⬅️ Back",
                style="danger",
                callback_data="ap_change_price",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_folder_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="✅ Yes (Create Folder)",
                    style="success",
                    callback_data="ap_folder_yes",
                ),
                styled_inline_btn(
                    text="❌ No (Direct Slot)",
                    style="primary",
                    callback_data="ap_folder_no",
                ),
            ],
            [
                styled_inline_btn(
                    text="🔙 Cancel",
                    style="danger",
                    callback_data="ap_home",
                )
            ],
        ]
    )


def build_admin_direct_slots_keyboard() -> InlineKeyboardMarkup:
    slots = fetch_all_slots()
    rows: list[list[InlineKeyboardButton]] = []
    for sl in slots:
        sid = str(sl["slot_id"])
        name = str(sl["name"])
        stk = int(sl["stock"])
        if sl.get("is_folder"):
            rows.append(
                [
                    styled_inline_btn(
                        text=f"📁 {name} (Folder • {stk} total)",
                        style="primary",
                        callback_data=f"ap_dir_fld:{sid}",
                    )
                ]
            )
        else:
            price = float(sl["price"])
            rows.append(
                [
                    styled_inline_btn(
                        text=f"🎟️ {name} — ₹{price:g} (Stock: {stk})",
                        style="success" if stk > 0 else "primary",
                        callback_data=f"ap_dir_itm:{sid}:",
                    )
                ]
            )
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Admin Panel",
                style="danger",
                callback_data="ap_home",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_direct_subitems_keyboard(folder_slot: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = str(folder_slot["slot_id"])
    rows: list[list[InlineKeyboardButton]] = []
    for sub in folder_slot.get("sub_items", []):
        sub_id = str(sub["sub_id"])
        name = str(sub["name"])
        price = float(sub["price"])
        stk = int(sub["stock"])
        rows.append(
            [
                styled_inline_btn(
                    text=f"🎟️ {name} — ₹{price:g} (Stock: {stk})",
                    style="success" if stk > 0 else "primary",
                    callback_data=f"ap_dir_itm:{sid}:{sub_id}",
                )
            ]
        )
    rows.append(
        [
            styled_inline_btn(
                text="⬅️ Back",
                style="danger",
                callback_data="ap_direct_add",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_download_slots_keyboard() -> InlineKeyboardMarkup:
    slots = fetch_all_slots()
    rows: list[list[InlineKeyboardButton]] = []
    for sl in slots:
        sid = str(sl["slot_id"])
        name = str(sl["name"])
        stk = int(sl["stock"])
        if sl.get("is_folder"):
            rows.append(
                [
                    styled_inline_btn(
                        text=f"📁 {name} (Folder • {stk} live)",
                        style="primary",
                        callback_data=f"ap_dl_fld:{sid}",
                    )
                ]
            )
        else:
            price = float(sl["price"])
            rows.append(
                [
                    styled_inline_btn(
                        text=f"🎟️ {name} — ₹{price:g} (Live: {stk})",
                        style="success" if stk > 0 else "danger",
                        callback_data=f"ap_dl_itm:{sid}:",
                    )
                ]
            )
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Admin Panel",
                style="danger",
                callback_data="ap_home",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_download_subitems_keyboard(folder_slot: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = str(folder_slot["slot_id"])
    rows: list[list[InlineKeyboardButton]] = []
    for sub in folder_slot.get("sub_items", []):
        sub_id = str(sub["sub_id"])
        name = str(sub["name"])
        price = float(sub["price"])
        stk = int(sub["stock"])
        rows.append(
            [
                styled_inline_btn(
                    text=f"🎟️ {name} — ₹{price:g} (Live: {stk})",
                    style="success" if stk > 0 else "danger",
                    callback_data=f"ap_dl_itm:{sid}:{sub_id}",
                )
            ]
        )
    rows.append(
        [
            styled_inline_btn(
                text="⬅️ Back",
                style="danger",
                callback_data="ap_dl_codes",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_admin_post_add_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="📊 Check Quantity",
                    style="primary",
                    callback_data="ap_check_qty",
                ),
                styled_inline_btn(
                    text="⚡ Direct Add More",
                    style="success",
                    callback_data="ap_direct_add",
                ),
            ],
            [
                styled_inline_btn(
                    text="➕ New Slot",
                    style="success",
                    callback_data="ap_new_slot",
                ),
                styled_inline_btn(
                    text="🛠️ Admin Panel",
                    style="primary",
                    callback_data="ap_home",
                ),
            ],
        ]
    )


def build_buy_catalog_keyboard() -> InlineKeyboardMarkup:
    slots = fetch_all_slots()
    rows: list[list[InlineKeyboardButton]] = []
    for sl in slots:
        sid = str(sl["slot_id"])
        name = str(sl["name"])
        stk = int(sl["stock"])
        if sl.get("is_folder"):
            rows.append(
                [
                    styled_inline_btn(
                        text=f"📁 {name} ({stk})",
                        style="success" if stk > 0 else "danger",
                        callback_data=f"buy_folder:{sid}",
                    )
                ]
            )
        else:
            rows.append(
                [
                    styled_inline_btn(
                        text=f"🎟️ {name} ({stk})",
                        style="success" if stk > 0 else "danger",
                        callback_data=f"buy_itm:{sid}:",
                    )
                ]
            )
    rows.append(
        [
            styled_inline_btn(
                text="🏠 Back to Home", style="primary", callback_data="back_to_home"
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_buy_folder_subitems_keyboard(folder_slot: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = str(folder_slot["slot_id"])
    rows: list[list[InlineKeyboardButton]] = []
    for sub in folder_slot.get("sub_items", []):
        sub_id = str(sub["sub_id"])
        name = str(sub["name"])
        stk = int(sub["stock"])
        rows.append(
            [
                styled_inline_btn(
                    text=f"🎟️ {name} ({stk})",
                    style="success" if stk > 0 else "danger",
                    callback_data=f"buy_itm:{sid}:{sub_id}",
                )
            ]
        )
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Shop",
                style="danger",
                callback_data="open_buy_menu",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_product_quantity_keyboard(item: dict[str, Any]) -> InlineKeyboardMarkup:
    sid = str(item["slot_id"])
    sub_id = str(item.get("sub_id", ""))
    unit_price = float(item["price"])
    stock = int(item["stock"])
    rows: list[list[InlineKeyboardButton]] = []

    qty_row: list[InlineKeyboardButton] = []
    if stock >= 1:
        qty_row.append(
            styled_inline_btn(
                text=f"1 Coupon — ₹{unit_price:g}",
                style="success",
                callback_data=f"buy_qty:{sid}:{sub_id}:1",
            )
        )
    if stock >= 2:
        qty_row.append(
            styled_inline_btn(
                text=f"2 Coupons — ₹{unit_price * 2:g}",
                style="success",
                callback_data=f"buy_qty:{sid}:{sub_id}:2",
            )
        )
    if qty_row:
        rows.append(qty_row)

    if stock >= 1:
        rows.append(
            [
                styled_inline_btn(
                    text="✏️ Custom Quantity",
                    style="primary",
                    callback_data=f"buy_cqty:{sid}:{sub_id}",
                )
            ]
        )

    back_cb = f"buy_folder:{sid}" if sub_id else "open_buy_menu"
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Shop",
                style="danger",
                callback_data=back_cb,
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_order_checkout_keyboard(
    slot_id: str,
    sub_id: str,
    quantity: int,
    total_amount: float,
    wallet_total_balance: float,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text=f"💳 Pay with UPI (₹{total_amount:g})",
                    style="success",
                    callback_data=f"chk_upi:{slot_id}:{sub_id}:{quantity}",
                )
            ],
            [
                styled_inline_btn(
                    text=f"💰 Pay with Wallet (₹{wallet_total_balance:g})",
                    style="primary",
                    callback_data=f"chk_wlt:{slot_id}:{sub_id}:{quantity}",
                )
            ],
            [
                styled_inline_btn(
                    text="🛍️ Shop",
                    style="primary",
                    callback_data="open_buy_menu",
                ),
                styled_inline_btn(
                    text="❌ Cancel",
                    style="danger",
                    callback_data=f"chk_cnl:{slot_id}:{sub_id}:{quantity}",
                ),
            ],
            [
                styled_inline_btn(
                    text="⬅️ Back",
                    style="primary",
                    callback_data=f"buy_itm:{slot_id}:{sub_id}",
                ),
                styled_inline_btn(
                    text="🏠 Home",
                    style="primary",
                    callback_data="back_to_home",
                ),
            ],
        ]
    )


def build_wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="🎟️ Claim Coupon",
                    style="primary",
                    callback_data="wallet_claim_coupon",
                )
            ],
            [
                styled_inline_btn(text="₹15", style="success", callback_data="wallet_amt:15"),
                styled_inline_btn(text="₹50", style="success", callback_data="wallet_amt:50"),
            ],
            [
                styled_inline_btn(
                    text="✏️ Custom Amount", style="primary", callback_data="wallet_custom"
                )
            ],
            [
                styled_inline_btn(
                    text="❌ Cancel", style="danger", callback_data="back_to_home"
                )
            ],
        ]
    )


def build_payment_session_keyboard(txid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="✅ I Have Paid",
                    style="success",
                    callback_data=f"pay_paid:{txid}",
                ),
                styled_inline_btn(
                    text="❌ Cancel",
                    style="danger",
                    callback_data=f"pay_cancel:{txid}",
                ),
            ],
            [
                styled_inline_btn(
                    text="🔙 Back to Wallet",
                    style="primary",
                    callback_data="open_wallet",
                )
            ],
        ]
    )


def build_utr_retry_keyboard(txid: str, attempts_left: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            styled_inline_btn(
                text="🔄 Refresh / Recheck",
                style="primary",
                callback_data=f"utr_recheck:{txid}",
            )
        ]
    ]
    if attempts_left > 0:
        rows.append(
            [
                styled_inline_btn(
                    text=f"✏️ Re-submit UTR ({attempts_left} left)",
                    style="success",
                    callback_data=f"utr_resubmit:{txid}",
                )
            ]
        )
    rows.append(
        [
            styled_inline_btn(
                text="🔙 Back to Wallet",
                style="danger",
                callback_data="open_wallet",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def build_stock_web_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="🔄 Refresh", style="primary", callback_data="stock_refresh"
                ),
                styled_inline_btn(
                    text="🛒 Buy Menu", style="success", callback_data="open_buy_menu"
                ),
            ],
            [
                styled_inline_btn(
                    text="🏠 Back to Home", style="danger", callback_data="back_to_home"
                ),
            ],
        ]
    )


def build_profile_web_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="📦 My Orders", style="primary", callback_data="orders_page:0"
                ),
                styled_inline_btn(
                    text="🤝 Refer & Earn", style="success", callback_data="open_refer"
                ),
            ],
            [
                styled_inline_btn(
                    text="⬅️ Back", style="danger", callback_data="back_to_home"
                ),
            ],
        ]
    )


def build_refer_keyboard(ref_link: str) -> InlineKeyboardMarkup:
    share_url = (
        f"https://t.me/share/url?url={ref_link}"
        "&text=Join%20this%20coupon%20bot%20and%20get%20%E2%82%B92%20instant%20wallet%20bonus!"
    )
    return InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="📤 Share Referral Link", style="success", url=share_url
                )
            ],
            [
                styled_inline_btn(
                    text="🏠 Back to Home", style="primary", callback_data="back_to_home"
                )
            ],
        ]
    )


def build_orders_web_keyboard(page: int, total_orders: int) -> InlineKeyboardMarkup:
    total_pages = max(1, (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE)
    nav_row: list[InlineKeyboardButton] = []
    if page > 0:
        nav_row.append(
            styled_inline_btn(
                text="⏮️ Prev", style="primary", callback_data=f"orders_page:{page - 1}"
            )
        )
    if page + 1 < total_pages:
        nav_row.append(
            styled_inline_btn(
                text="⏭️ Next", style="primary", callback_data=f"orders_page:{page + 1}"
            )
        )

    rows: list[list[InlineKeyboardButton]] = []
    if nav_row:
        rows.append(nav_row)
    rows.append(
        [
            styled_inline_btn(
                text="🏠 Home", style="primary", callback_data="back_to_home"
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def format_admin_users_list_page(page: int = 0) -> tuple[str, int, int]:
    users = fetch_all_registered_users()
    total_users = len(users)
    total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    safe_page = max(0, min(page, total_pages - 1))

    start_idx = safe_page * USERS_PER_PAGE
    page_items = users[start_idx : start_idx + USERS_PER_PAGE]

    lines = [
        "👥 <b>Registered Bot Users (Firebase RTDB)</b>",
        f"• <b>Total Users:</b> <b>{total_users}</b>",
        f"• <b>Page:</b> {safe_page + 1}/{total_pages}",
        "",
    ]

    if not page_items:
        lines.append("No users recorded yet.")
        return "\n".join(lines), total_users, safe_page

    for idx, u in enumerate(page_items, start=start_idx + 1):
        uid = u["user_id"]
        uname = u.get("username", "")
        if uname:
            lines.append(f"{idx}. <code>{uid}</code> — @{html.escape(uname)}")
        else:
            lines.append(f"{idx}. <code>{uid}</code>")

    return "\n".join(lines), total_users, safe_page


def format_admin_order_lookup_report(order: dict[str, Any]) -> str:
    oid = html.escape(str(order.get("order_id", "N/A")))
    txid = html.escape(str(order.get("txid", "N/A")))
    pmethod = html.escape(str(order.get("payment_method", "N/A")))
    utr = str(order.get("utr") or "").strip()
    utr_line = f"• <b>12-Digit UTR:</b> <code>{html.escape(utr)}</code>\n" if utr else ""

    uid = order.get("user_id", "N/A")
    fname = html.escape(str(order.get("first_name") or "User"))
    uname = str(order.get("username") or "").strip()
    uname_line = f"• <b>Username:</b> @{html.escape(uname)}\n" if uname else ""

    cname = html.escape(str(order.get("coupon_name", "Item")))
    qty = int(order.get("quantity", 1))
    unit_p = float(order.get("price", 0.0))
    total_p = float(order.get("total_price", unit_p * qty))
    refunded_qty = int(order.get("refunded_qty", 0))
    refunded_amt = float(order.get("refunded_amount", 0.0))
    refund_line = (
        f"• <b>Refunded:</b> {refunded_qty}/{qty} unit(s) (₹{refunded_amt:.2f})\n"
        if refunded_qty > 0
        else ""
    )

    raw_ts = str(order.get("created_at", ""))
    try:
        dt = datetime.fromisoformat(raw_ts).astimezone(IST)
        ts_str = dt.strftime("%d %b %Y, %I:%M:%S %p IST")
    except ValueError:
        ts_str = html.escape(raw_ts)

    codes = order.get("delivered_codes") or []
    if isinstance(codes, list) and codes:
        codes_block = format_delivered_codes_block(codes)
    else:
        codes_block = "• <i>No codes recorded</i>"

    return (
        "🔍 <b>ORDER DETAILS FOUND</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Order ID:</b> <code>{oid}</code>\n"
        f"• <b>Transaction ID:</b> <code>{txid}</code>\n"
        f"• <b>Payment Method:</b> <b>{pmethod}</b>\n"
        f"{utr_line}"
        f"• <b>Date &amp; Time:</b> {ts_str}\n\n"
        "<b>Customer Details</b>\n"
        f"• <b>Name:</b> {fname}\n"
        f"• <b>Telegram User ID:</b> <code>{uid}</code>\n"
        f"{uname_line}\n"
        "<b>Purchase Details</b>\n"
        f"• <b>Product / Item:</b> <b>{cname}</b>\n"
        f"• <b>Unit Price:</b> ₹{unit_p:g}\n"
        f"• <b>Quantity:</b> <b>{format_qty_expression(qty)}</b> ({qty})\n"
        f"• <b>Total Paid:</b> <b>₹{total_p:.2f}</b>\n"
        f"{refund_line}\n"
        "<b>Delivered Coupon(s) / Link(s) / JSON</b>\n"
        f"{codes_block}"
    )


def format_admin_panel_overview() -> str:
    slots = fetch_all_slots()
    total_slots = len(slots)
    total_units = sum(int(i["stock"]) for i in slots)
    lines = [
        "🛠️ <b>Admin Control Panel (Firebase RTDB)</b>",
        "",
        f"• <b>Total Categories / Slots:</b> <b>{total_slots}</b>",
        f"• <b>Total Live Available Quantity:</b> <b>{total_units}</b>",
        "",
        "Select an option below:",
        "• <b>➕ New Slot:</b> Create a standalone coupon slot or a Folder containing multiple sub-items.",
        "• <b>⚡ Direct Add Coupon:</b> Append new coupons/links/JSON directly into an existing slot or folder item.",
        "• <b>📥 Download Codes:</b> Withdraw &amp; download live codes/links as a <code>.txt</code> file (excluded from Leaderboard).",
        "• <b>💲 Change Price Per Unit:</b> Update unit price for any slot or folder item.",
        "• <b>🗑️ Delete Slots:</b> Delete a slot, folder item, or entire folder from Firebase.",
    ]
    return "\n".join(lines)


def format_admin_live_quantity_report() -> str:
    slots = fetch_all_slots()
    lines = [
        "📊 <b>Live Firebase Inventory &amp; Quantity Report</b>",
        "",
    ]
    if not slots:
        lines.append("No slots added yet. Tap <b>➕ New Slot</b> to add your first stock.")
        return "\n".join(lines)

    total_units = 0
    for idx, sl in enumerate(slots, start=1):
        stk = int(sl["stock"])
        total_units += stk
        if sl.get("is_folder"):
            lines.append(
                f"{idx}. 📁 <b>{html.escape(str(sl['name']))}</b> (Folder) — Total Live Qty: <b>{stk}</b>"
            )
            for sub in sl.get("sub_items", []):
                lines.append(
                    f"   └ <b>{html.escape(str(sub['name']))}</b> — ₹{float(sub['price']):g} | Qty: <b>{int(sub['stock'])}</b>"
                )
        else:
            lines.append(
                f"{idx}. 🎟️ <b>{html.escape(str(sl['name']))}</b> — "
                f"₹{float(sl['price']):g} | Live Qty: <b>{stk}</b>"
            )
    lines.extend(["", f"• <b>Total Available Units:</b> <b>{total_units}</b>"])
    return "\n".join(lines)


def format_buy_catalog_message() -> str:
    slots = fetch_all_slots()
    if not slots:
        return (
            "🛒 <b>Coupon Store</b>\n\n"
            "No coupons are currently listed in stock. Please check back shortly."
        )
    return (
        "🛒 <b>Coupon Store — Live Stock</b>\n\n"
        "Here is all our live stock. Check availability and select an item or folder below:"
    )


def format_folder_contents_message(folder_slot: dict[str, Any]) -> str:
    fname = html.escape(str(folder_slot["name"]))
    subs = folder_slot.get("sub_items", [])
    if not subs:
        return (
            f"📁 <b>{fname}</b>\n\n"
            "No items are currently available inside this folder."
        )
    return (
        f"📁 <b>{fname}</b>\n\n"
        "Select an item inside this folder to view details and choose quantity:"
    )


def format_product_detail_message(item: dict[str, Any]) -> str:
    name = html.escape(str(item["display_name"]))
    desc = html.escape(str(item["description"]))
    price = float(item["price"])
    stock = int(item["stock"])
    stock_label = f"<b>{stock}</b> available" if stock > 0 else "<b>0 (Out of Stock)</b>"

    lines = [
        f"🎟️ <b>Selected Coupon:</b> <b>{name}</b>",
        "",
        "<b>Description &amp; Terms</b>",
        f"{desc}",
        "",
        f"• <b>Price Per Unit:</b> <b>₹{price:g}</b>",
        f"• <b>Total Stock:</b> {stock_label}",
        "",
        "👇 <b>Select Quantity:</b>" if stock > 0 else "⚠️ <i>This coupon is currently out of stock.</i>",
    ]
    return "\n".join(lines)


def format_order_summary_message(
    item: dict[str, Any], quantity: int, wallet_total_balance: float
) -> str:
    name = html.escape(str(item["display_name"]))
    desc = html.escape(str(item["description"]))
    unit_price = float(item["price"])
    stock = int(item["stock"])
    total_amount = round(unit_price * quantity, 2)
    qty_display = format_qty_expression(quantity)

    return (
        "🧾 <b>Order Summary &amp; Checkout</b>\n\n"
        "<b>Terms &amp; Description</b>\n"
        f"{desc}\n\n"
        "<b>Purchase Details</b>\n"
        f"• <b>Product / Item:</b> <b>{name}</b>\n"
        f"• <b>Available Stock:</b> <b>{stock}</b>\n"
        f"• <b>Quantity:</b> <b>{qty_display}</b>\n"
        f"• <b>Total Amount:</b> <b>₹{total_amount:g}</b>\n"
        f"• <b>Your Wallet Balance:</b> ₹{wallet_total_balance:.2f}\n\n"
        "Choose a payment method below:"
    )


def format_wallet_message(user_id: int) -> str:
    stats = fetch_user_profile_stats(user_id)
    lines = [
        "💰 <b>My Wallet</b>",
        "",
        "Manage your funds and top up instantly via UPI QR.",
        "",
        f"• <b>Available Balance:</b> <b>₹{stats['wallet_balance']:.2f}</b>",
        f"• <b>Referral Balance:</b> <b>₹{stats['referral_earnings']:.2f}</b>",
        f"• <b>Total Balance:</b> <b>₹{stats['total_balance']:.2f}</b>",
        "",
        f"➕ <b>Add Minimum ₹{MIN_WALLET_TOPUP:g}</b>",
        "Please select a top-up amount below or enter a custom amount:",
    ]
    return "\n".join(lines)


def format_payment_caption(
    txid: str,
    amount: float,
    item_name: str | None = None,
    quantity: int | None = None,
) -> str:
    if item_name and quantity is not None:
        qty_str = format_qty_expression(quantity)
        header = (
            "💳 <b>Payment Request — Coupon Purchase</b>\n\n"
            f"• <b>Item:</b> <b>{html.escape(item_name)}</b>\n"
            f"• <b>Quantity:</b> <b>{qty_str}</b>\n"
            f"• <b>Total Amount:</b> <b>₹{amount:.2f}</b>\n"
            f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
            f"• <b>UPI ID:</b> <code>{html.escape(UPI_ID)}</code>\n\n"
        )
    else:
        header = (
            "💳 <b>Wallet Top-Up Payment</b>\n\n"
            f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
            f"• <b>Amount:</b> <b>₹{amount:.2f}</b>\n"
            f"• <b>UPI ID:</b> <code>{html.escape(UPI_ID)}</code>\n\n"
        )

    return (
        header
        + "Scan the QR code above or pay using the UPI ID below.\n"
        "• Payment will be verified automatically via 12-digit UTR.\n"
        "• <b>Verification timeout:</b> 5 minutes.\n"
        "• After paying the <b>exact amount</b>, tap <b>✅ I Have Paid</b>.\n"
        "• Your order/wallet is credited immediately upon verification (or manual admin check if delayed).\n"
        f"• Need help? Contact {SUPPORT_BOT_URL}\n"
        "• <i>This payment session will automatically expire in 15 minutes.</i>"
    )


def format_delivered_receipt(res: dict[str, Any]) -> str:
    codes_block = format_delivered_codes_block(res["delivered_codes"])
    utr_line = (
        f"• <b>UTR Number:</b> <code>{html.escape(res['utr'])}</code>\n"
        if res.get("utr")
        else ""
    )
    bal_line = (
        f"• <b>Remaining Wallet Balance:</b> <b>₹{res['remaining_total_balance']:.2f}</b>\n"
        if "remaining_total_balance" in res
        else ""
    )
    return (
        "✅ <b>Order Confirmed &amp; Delivered!</b>\n\n"
        "<b>Payment Details</b>\n"
        f"• <b>Payment Method:</b> <b>{html.escape(res['payment_method'])}</b>\n"
        f"• <b>Transaction ID:</b> <code>{html.escape(res['txid'])}</code>\n"
        f"{utr_line}"
        f"• <b>Order ID:</b> <code>{html.escape(res['order_id'])}</code>\n\n"
        "<b>Purchase Details</b>\n"
        f"• <b>Item:</b> <b>{html.escape(res['coupon_name'])}</b>\n"
        f"• <b>Quantity:</b> <b>{format_qty_expression(int(res['quantity']))}</b>\n"
        f"• <b>Total Paid:</b> <b>₹{float(res['total_price']):.2f}</b>\n"
        f"{bal_line}\n"
        "<b>Your Coupon Code(s) / Link(s) / JSON</b>\n"
        f"{codes_block}"
    )


async def is_user_in_chat(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int
) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member.status in JOINED_STATUSES:
            return True
        if member.status == ChatMemberStatus.RESTRICTED:
            return bool(getattr(member, "is_member", False))
        return False
    except TelegramError as exc:
        logger.warning(
            "Membership check failed for user_id=%s in chat_id=%s: %s",
            user_id,
            chat_id,
            exc,
        )
        return False


async def get_missing_channels(
    context: ContextTypes.DEFAULT_TYPE, user_id: int
) -> list[tuple[int, dict[str, str]]]:
    missing: list[tuple[int, dict[str, str]]] = []
    for chat_id, info in CHANNELS.items():
        if not await is_user_in_chat(context, chat_id, user_id):
            missing.append((chat_id, info))
    return missing


def build_force_join_keyboard(
    missing_channels: list[tuple[int, dict[str, str]]],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [styled_inline_btn(text=info["name"], style="primary", url=info["url"])]
        for _, info in missing_channels
    ]
    rows.append(
        [
            styled_inline_btn(
                text="✅ Verify Membership",
                style="success",
                callback_data="verify_joins",
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def format_start_message(
    first_name: str,
    user_id: int,
    username: str | None,
    missing_channels: list[tuple[int, dict[str, str]]],
) -> str:
    safe_name = html.escape(first_name or "User")
    safe_username = format_username(username)
    lines = [
        f"👋 <b>Welcome, {safe_name}!</b>",
        "",
        "<b>Account Details</b>",
        f"• <b>Telegram ID:</b> <code>{user_id}</code>",
        f"• <b>Username:</b> {safe_username}",
        "",
        "Please join all required channels and groups below to continue:",
        "",
    ]
    for _, info in missing_channels:
        lines.append(f"• {html.escape(info['name'])}")
    return "\n".join(lines)


def format_recheck_message(
    first_name: str,
    user_id: int,
    username: str | None,
    missing_channels: list[tuple[int, dict[str, str]]],
) -> str:
    safe_name = html.escape(first_name or "User")
    safe_username = format_username(username)
    lines = [
        "⚠️ <b>Membership Verification Incomplete</b>",
        "",
        f"Hello <b>{safe_name}</b> (<code>{user_id}</code> | {safe_username}), you have not joined all required channels yet.",
        "Please join the remaining channels/groups below and tap <b>Verify Membership</b>:",
        "",
    ]
    for _, info in missing_channels:
        lines.append(f"• {html.escape(info['name'])}")
    return "\n".join(lines)


def format_stock_status_message() -> str:
    slots = fetch_all_slots()
    lines = [
        "📊 <b>Live Coupon Stock Status</b>",
        "",
    ]
    if not slots:
        lines.append("No coupons are currently available.")
        return "\n".join(lines)

    for idx, sl in enumerate(slots, start=1):
        name = html.escape(str(sl["name"]))
        stock = int(sl["stock"])
        if sl.get("is_folder"):
            lines.append(f"{idx}. 📁 <b>{name}</b> — Total Stock: <b>{stock}</b>")
            for sub in sl.get("sub_items", []):
                sub_name = html.escape(str(sub["name"]))
                sub_price = float(sub["price"])
                sub_stk = int(sub["stock"])
                st_tag = "In Stock" if sub_stk > 0 else "Out of Stock"
                lines.append(
                    f"   └ <b>{sub_name}</b> — ₹{sub_price:g} | Stock: <b>{sub_stk}</b> ({st_tag})"
                )
        else:
            price = float(sl["price"])
            status_tag = "In Stock" if stock > 0 else "Out of Stock"
            lines.append(
                f"{idx}. <b>{name}</b> — ₹{price:g} | Stock: <b>{stock}</b> ({status_tag})"
            )
    return "\n".join(lines)


def format_profile_message(user_id: int, username: str | None) -> str:
    stats = fetch_user_profile_stats(user_id)
    safe_username = format_username(username or stats["username"])
    lines = [
        "👤 <b>My Profile</b>",
        "",
        f"• <b>ID:</b> <code>{stats['user_id']}</code>",
        f"• <b>Username:</b> {safe_username}",
        f"• <b>Total Orders:</b> <b>{stats['total_orders']}</b>",
        "",
        "<b>Total Purchase Summary</b>",
        f"• <b>Today Spent:</b> ₹{stats['today_spent']:g}",
        f"• <b>Previous Days Spent:</b> ₹{stats['previous_days_spent']:g}",
        f"• <b>Total Amount:</b> <b>₹{stats['total_spent']:g}</b>",
        "",
        "<b>Referral Status</b>",
        f"• <b>Successful Referrals:</b> <b>{stats['referrals_count']}</b>",
        f"• <b>Total Earnings:</b> <b>₹{stats['referral_earnings']:g}</b>",
    ]
    return "\n".join(lines)


def format_refer_message(user_id: int, bot_username: str) -> tuple[str, str]:
    stats = fetch_user_profile_stats(user_id)
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    lines = [
        "🤝 <b>Refer &amp; Earn Program</b>",
        "",
        f"Invite your friends using your personal referral link below. Both you and your friend receive <b>₹{REFERRAL_REWARD_AMOUNT:g}</b> in your Referral Wallet once they join all required channels and verify.",
        "",
        "<b>Your Referral Link</b>",
        f"<code>{html.escape(ref_link)}</code>",
        "",
        "<b>Referral Wallet Summary</b>",
        f"• <b>Reward Per Successful Referral:</b> ₹{REFERRAL_REWARD_AMOUNT:g}",
        f"• <b>Successful Referrals:</b> <b>{stats['referrals_count']}</b>",
        f"• <b>Referral Wallet Earnings:</b> <b>₹{stats['referral_earnings']:g}</b>",
    ]
    return "\n".join(lines), ref_link


def format_orders_message(user_id: int, page: int = 0) -> tuple[str, int, int]:
    items, total_orders, safe_page = fetch_user_orders_page(user_id, page)
    total_pages = max(1, (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE)

    lines = [
        "📦 <b>Your Order History</b>",
        f"• <b>Total Orders:</b> <b>{total_orders}</b>",
        f"• <b>Page:</b> {safe_page + 1}/{total_pages}",
        "",
    ]

    if not items:
        lines.append("You have not placed any orders yet.")
        return "\n".join(lines), total_orders, safe_page

    start_num = safe_page * ORDERS_PER_PAGE + 1
    for offset, order in enumerate(items):
        num = start_num + offset
        time_part = f" | {html.escape(order['time_str'])}" if order["time_str"] else ""
        lines.append(
            f"{num}. <b>{html.escape(order['coupon_name'])}</b> — "
            f"{html.escape(order['date_str'])}{time_part} | "
            f"₹{order['price']:g} | Qty: <b>{order['quantity']}</b> | "
            f"Order ID: <code>{html.escape(order['order_id'])}</code>"
        )

    return "\n".join(lines), total_orders, safe_page


def format_leaderboard_message() -> str:
    leaders = fetch_leaderboard(limit=10)
    lines = [
        "🏆 <b>Live Coupon Leaderboard</b>",
        "<i>Top buyers ranked by highest coupons purchased:</i>",
        "",
    ]
    if not leaders:
        lines.append("No coupon purchases recorded yet.")
        return "\n".join(lines)

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for rank, row in enumerate(leaders, start=1):
        prefix = medals.get(rank, f"#{rank}")
        uname = format_username(row.get("username"))
        coupons_qty = int(row.get("total_coupons", 0))
        spend = float(row.get("total_spend", 0.0))
        lines.append(
            f"{prefix} <b>{uname}</b> (<code>{row['user_id']}</code>) — "
            f"<b>{coupons_qty}</b> coupons (₹{spend:g})"
        )
    return "\n".join(lines)


def parse_start_referrer(args: list[str] | None) -> int | None:
    if not args:
        return None
    payload = args[0].strip()
    if payload.startswith("ref_"):
        candidate = payload[4:]
        if candidate.isdigit():
            return int(candidate)
    elif payload.isdigit():
        return int(payload)
    return None


def clear_all_pending_input_states(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_custom_amount", None)
    context.user_data.pop("awaiting_custom_qty_target", None)
    context.user_data.pop("awaiting_utr_txid", None)
    context.user_data.pop("awaiting_curl_upload", None)
    context.user_data.pop("awaiting_promo_coupon", None)
    context.user_data.pop("admin_panel_state", None)
    context.user_data.pop("admin_cmd_state", None)


async def send_or_edit_home(
    update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False
) -> None:
    user = update.effective_user
    if not user:
        return
    clear_all_pending_input_states(context)
    ensure_user_record(user.id, user.username, user.first_name)
    safe_name = html.escape(user.first_name or "User")
    safe_username = format_username(user.username)
    text = (
        f"🏠 <b>Home Menu</b>\n\n"
        f"Welcome, <b>{safe_name}</b>!\n"
        f"• <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"• <b>Username:</b> {safe_username}\n\n"
        "Use the menu buttons below to navigate."
    )
    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, parse_mode="HTML")
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=build_main_menu_keyboard(),
                    parse_mode="HTML",
                )
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=build_main_menu_keyboard(),
            parse_mode="HTML",
        )


async def on_access_granted(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    if not user:
        return
    clear_all_pending_input_states(context)
    ensure_user_record(user.id, user.username, user.first_name)

    async with get_user_lock(user.id):
        ref_res = claim_referral_reward_if_eligible(user.id)

    safe_name = html.escape(user.first_name or "User")
    safe_username = format_username(user.username)
    text = (
        f"✅ <b>Access Granted</b>\n\n"
        f"Welcome, <b>{safe_name}</b>! All required channels are verified.\n"
        f"• <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"• <b>Username:</b> {safe_username}\n\n"
        "Choose an option from the menu below:"
    )
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text=text, parse_mode="HTML")
        except TelegramError:
            pass
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="📋 <b>Main Menu</b>",
                reply_markup=build_main_menu_keyboard(),
                parse_mode="HTML",
            )
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=build_main_menu_keyboard(),
            parse_mode="HTML",
        )

    if ref_res.get("rewarded"):
        reward_amt = float(ref_res.get("amount", REFERRAL_REWARD_AMOUNT))
        referrer_id = ref_res.get("referrer_id")
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=(
                    f"🎉 <b>Referral Bonus Credited!</b>\n\n"
                    f"<b>₹{reward_amt:g}</b> has been added to your Referral Wallet for joining via referral and verifying channels."
                ),
                parse_mode="HTML",
            )
        except TelegramError as exc:
            logger.warning("Failed to notify referee %s: %s", user.id, exc)

        if referrer_id:
            try:
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=(
                        f"🎉 <b>New Successful Referral!</b>\n\n"
                        f"User <code>{user.id}</code> ({safe_username}) verified all channels.\n"
                        f"<b>₹{reward_amt:g}</b> has been credited to your Referral Wallet!"
                    ),
                    parse_mode="HTML",
                )
            except TelegramError as exc:
                logger.warning("Failed to notify referrer %s: %s", referrer_id, exc)


async def enforce_force_join(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    user = update.effective_user
    if not user:
        return False

    missing = await get_missing_channels(context, user.id)
    if not missing:
        return True

    keyboard = build_force_join_keyboard(missing)
    text = format_recheck_message(
        user.first_name or "User", user.id, user.username, missing
    )

    if update.callback_query:
        await update.callback_query.answer(
            "Access denied. Please join all required channels first.",
            show_alert=True,
        )
        try:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    elif update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    return False


# =====================================================================
# Commands (/start, /curl, /admin, /adminpanel, unknown commands)
# =====================================================================


async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if await guard_maintenance_mode(update, context):
        return
    user = update.effective_user
    if not user or not update.message:
        return

    clear_all_pending_input_states(context)
    referrer_id = parse_start_referrer(context.args)
    ensure_user_record(user.id, user.username, user.first_name, referrer_id=referrer_id)

    missing = await get_missing_channels(context, user.id)
    if not missing:
        await on_access_granted(update, context)
        return

    await update.message.reply_text(
        text=format_start_message(
            user.first_name or "User", user.id, user.username, missing
        ),
        reply_markup=build_force_join_keyboard(missing),
        parse_mode="HTML",
    )


async def curl_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    clear_all_pending_input_states(context)
    if user.id != ADMIN_ID:
        if await guard_maintenance_mode(update, context):
            return
        await update.message.reply_text(
            "⛔ <b>Access Denied:</b> This command is restricted to the administrator only.",
            parse_mode="HTML",
        )
        return

    context.user_data["awaiting_curl_upload"] = True
    await update.message.reply_text(
        "🔑 <b>BharatPe Token / cURL Update</b>\n\n"
        "Send your browser-copied <code>Copy as cURL</code> text or upload the <code>.txt</code> file directly now.\n"
        "The bot will automatically extract the session token and verify the API connection.",
        parse_mode="HTML",
    )


async def admin_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Unlocked /admin command with Broadcast, User List, Check Order ID, Maintenance Mode, Create Coupon for Bot, Refund User + Cancel."""
    user = update.effective_user
    if not user or not update.message:
        return

    clear_all_pending_input_states(context)
    if user.id != ADMIN_ID:
        if await guard_maintenance_mode(update, context):
            return
        await update.message.reply_text(
            "⛔ <b>Access Denied:</b> This command is restricted to the administrator only.",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        "🛡️ <b>Admin Controls</b>\n\nSelect an action below:",
        reply_markup=build_admin_inbox_menu_keyboard(),
        parse_mode="HTML",
    )


async def adminpanel_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    clear_all_pending_input_states(context)
    if user.id != ADMIN_ID:
        if await guard_maintenance_mode(update, context):
            return
        await update.message.reply_text(
            "⛔ <b>Access Denied:</b> This command is restricted to the administrator only.",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        text=format_admin_panel_overview(),
        reply_markup=build_admin_panel_keyboard(),
        parse_mode="HTML",
    )


async def unknown_command_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if await guard_maintenance_mode(update, context):
        return
    if not update.message or not update.effective_user:
        return
    clear_all_pending_input_states(context)
    allowed = await enforce_force_join(update, context)
    if not allowed:
        return
    await update.message.reply_text(
        "ℹ️ Unknown command. Previous input session cleared — please select a valid option from the menu below.",
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML",
    )


async def apply_admin_curl_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE, raw_content: str
) -> None:
    if not update.message:
        return

    new_token = extract_token_from_curl(raw_content)
    if not new_token:
        await update.message.reply_text(
            "❌ <b>Invalid cURL Format</b>\n\n"
            "Could not find a valid <code>token: &lt;hex_token&gt;</code> header in your input.\n"
            "Please paste the full <b>Copy as cURL</b> command or upload a valid <code>.txt</code> file.",
            parse_mode="HTML",
        )
        return

    cfg = load_bharatpe_config()
    cfg["token"] = new_token
    cfg["token_alert_sent"] = False
    save_bharatpe_config(cfg)
    context.user_data.pop("awaiting_curl_upload", None)

    status_msg = await update.message.reply_text(
        "🔍 <b>Verifying new BharatPe token...</b>", parse_mode="HTML"
    )
    status_code, _ = await fetch_bharatpe_transactions(page_size=1)
    if status_code == 200:
        await status_msg.edit_text(
            f"✅ <b>BharatPe Token Updated &amp; Verified!</b>\n\n"
            f"• <b>Token:</b> <code>{html.escape(new_token)}</code>\n"
            f"• <b>API Status:</b> Active (200 OK)",
            parse_mode="HTML",
        )
    else:
        await status_msg.edit_text(
            f"⚠️ <b>Token Saved, But API Check Failed</b> (HTTP <code>{status_code}</code>).\n"
            "Please verify your BharatPe dashboard login and send a fresh cURL.",
            parse_mode="HTML",
        )


# =====================================================================
# Buy Coupon Flow Views & Helpers
# =====================================================================


async def show_buy_catalog(
    update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False
) -> None:
    clear_all_pending_input_states(context)
    text = format_buy_catalog_message()
    keyboard = build_buy_catalog_keyboard()

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
            return
        except TelegramError:
            pass
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_buy_folder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slot_id: str,
    from_callback: bool = False,
) -> None:
    clear_all_pending_input_states(context)
    slots = fetch_all_slots()
    folder_slot = next((s for s in slots if s["slot_id"] == slot_id and s.get("is_folder")), None)
    if not folder_slot:
        if update.callback_query:
            await update.callback_query.answer("Folder not found.", show_alert=True)
        await show_buy_catalog(update, context, from_callback=from_callback)
        return

    text = format_folder_contents_message(folder_slot)
    keyboard = build_buy_folder_subitems_keyboard(folder_slot)

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
            return
        except TelegramError:
            pass
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_product_detail(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slot_id: str,
    sub_id: str = "",
    from_callback: bool = False,
) -> None:
    clear_all_pending_input_states(context)
    item = fetch_sellable_item(slot_id, sub_id)
    if not item:
        if update.callback_query:
            await update.callback_query.answer("Coupon not found.", show_alert=True)
        await show_buy_catalog(update, context, from_callback=from_callback)
        return

    text = format_product_detail_message(item)
    keyboard = build_product_quantity_keyboard(item)

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
            return
        except TelegramError:
            pass
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def show_order_summary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    slot_id: str,
    sub_id: str,
    quantity: int,
    from_callback: bool = False,
) -> None:
    user = update.effective_user
    if not user:
        return
    clear_all_pending_input_states(context)
    item = fetch_sellable_item(slot_id, sub_id)
    if not item:
        if update.callback_query:
            await update.callback_query.answer("Coupon not found.", show_alert=True)
        await show_buy_catalog(update, context, from_callback=from_callback)
        return

    stock = int(item["stock"])
    if stock <= 0:
        if update.callback_query:
            await update.callback_query.answer(
                "This coupon is currently out of stock.", show_alert=True
            )
        await show_product_detail(update, context, slot_id, sub_id, from_callback=from_callback)
        return

    if quantity < 1 or quantity > stock:
        if update.callback_query:
            await update.callback_query.answer(
                f"Invalid quantity. Please choose between 1 and {stock}.",
                show_alert=True,
            )
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Please choose a quantity between <b>1</b> and <b>{stock}</b>.",
                parse_mode="HTML",
            )
        return

    stats = fetch_user_profile_stats(user.id)
    wallet_total = float(stats["total_balance"])
    total_amount = round(float(item["price"]) * quantity, 2)

    text = format_order_summary_message(item, quantity, wallet_total)
    keyboard = build_order_checkout_keyboard(
        slot_id=slot_id,
        sub_id=sub_id,
        quantity=quantity,
        total_amount=total_amount,
        wallet_total_balance=wallet_total,
    )

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
            return
        except TelegramError:
            pass
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


# =====================================================================
# Wallet & UPI Payment Flow Handlers
# =====================================================================


async def show_wallet(
    update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False
) -> None:
    user = update.effective_user
    if not user:
        return
    clear_all_pending_input_states(context)
    ensure_user_record(user.id, user.username, user.first_name)
    text = format_wallet_message(user.id)
    keyboard = build_wallet_keyboard()

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
            return
        except TelegramError:
            pass
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def start_upi_payment_session(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    amount: float,
    purpose: str = "wallet",
    item: dict[str, Any] | None = None,
    quantity: int = 1,
) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return

    async with get_user_lock(user.id):
        clear_all_pending_input_states(context)
        slot_id = str(item["slot_id"]) if item else ""
        sub_id = str(item.get("sub_id", "")) if item else ""
        session, cancelled_txids = create_payment_session(
            user_id=user.id,
            amount=amount,
            chat_id=chat.id,
            purpose=purpose,
            slot_id=slot_id,
            sub_id=sub_id,
            quantity=quantity,
        )
        for old_txid in cancelled_txids:
            cancel_expiry_job(context, old_txid)

        txid = session["txid"]
        qr_bio, _ = generate_upi_qr(amount, order_note=txid)
        caption = format_payment_caption(
            txid=txid,
            amount=amount,
            item_name=str(item["display_name"]) if item else None,
            quantity=quantity if item else None,
        )
        keyboard = build_payment_session_keyboard(txid)

        if update.callback_query and update.callback_query.message:
            try:
                await update.callback_query.message.delete()
            except TelegramError:
                pass

        sent_msg = await context.bot.send_photo(
            chat_id=chat.id,
            photo=qr_bio,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        attach_qr_message_id(txid, sent_msg.message_id)
        schedule_expiry_job(context.job_queue, txid, PAYMENT_SESSION_TTL_SECONDS)


async def run_utr_verification_flow(
    chat_id: int,
    user_id: int,
    txid: str,
    raw_input: str,
    context: ContextTypes.DEFAULT_TYPE,
    increment_attempt: bool = True,
    status_message_to_edit: Any = None,
) -> None:
    async with get_user_lock(user_id):
        clean_utr = (raw_input or "").strip()

        deposit = get_deposit_session(txid, user_id)
        if not deposit:
            context.user_data.pop("awaiting_utr_txid", None)
            err = "❌ <b>Session Not Found</b>\n\nPlease start a new payment session from the menu."
            if status_message_to_edit:
                await status_message_to_edit.edit_text(err, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=chat_id, text=err, parse_mode="HTML")
            return

        if deposit["status"] == "expired" or int(time.time()) > int(deposit["expires_at"]):
            mark_deposit_expired(txid)
            cancel_expiry_job(context, txid)
            context.user_data.pop("awaiting_utr_txid", None)
            exp_text = (
                f"⛔ <b>Order ID / TXID:</b> <code>{html.escape(txid)}</code>\n\n"
                "⚠️ <b>Payment QR Expired</b>\n"
                "Your payment session has timed out. Please start a new purchase to generate a fresh QR code."
            )
            if status_message_to_edit:
                await status_message_to_edit.edit_text(exp_text, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=chat_id, text=exp_text, parse_mode="HTML")
            return

        if contains_url(clean_utr):
            err_text = (
                "❌ <b>Links / URLs Are Not Allowed</b>\n\n"
                f"Expected a <b>12-digit numeric UTR number</b> for TXID <code>{html.escape(txid)}</code> (Example: <code>432910482910</code>).\n"
                "Please enter your original 12-digit UPI Reference / UTR number:"
            )
            await context.bot.send_message(chat_id=chat_id, text=err_text, parse_mode="HTML")
            return

        if not re.fullmatch(r"\d{12}", clean_utr):
            err_text = (
                "❌ <b>Invalid UTR Format</b>\n\n"
                f"You entered: <code>{html.escape(clean_utr[:40])}</code>\n"
                "A valid UPI UTR must be <b>exactly 12 numeric digits</b> (no spaces, letters, or symbols — e.g., <code>432910482910</code>).\n\n"
                f"Please send the correct <b>12-digit UTR</b> for TXID <code>{html.escape(txid)}</code>:"
            )
            if status_message_to_edit:
                await status_message_to_edit.edit_text(err_text, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=chat_id, text=err_text, parse_mode="HTML")
            return

        if is_utr_already_used(clean_utr):
            err_text = (
                "❌ <b>Duplicate UTR Rejected</b>\n\n"
                f"UTR <code>{html.escape(clean_utr)}</code> has already been redeemed on an earlier verified payment.\n"
                "Please enter your own unused <b>12-digit UTR number</b>:"
            )
            if status_message_to_edit:
                await status_message_to_edit.edit_text(err_text, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=chat_id, text=err_text, parse_mode="HTML")
            return

        allowed, attempts_used, limit_reason = record_utr_attempt_and_check_limit(
            txid=txid,
            user_id=user_id,
            utr=clean_utr,
            increment_attempt=increment_attempt,
        )
        if not allowed:
            context.user_data.pop("awaiting_utr_txid", None)
            fail_text = f"❌ <b>Verification Blocked</b>\n\n{html.escape(limit_reason)}"
            if status_message_to_edit:
                await status_message_to_edit.edit_text(fail_text, parse_mode="HTML")
            else:
                await context.bot.send_message(chat_id=chat_id, text=fail_text, parse_mode="HTML")
            return

        expected_amount = float(deposit["amount"])
        attempts_left = max(0, MAX_UTR_ATTEMPTS - attempts_used)

        if status_message_to_edit:
            msg = status_message_to_edit
            try:
                await msg.edit_text(
                    f"⏳ <b>Verifying your payment...</b>\n\n"
                    f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
                    f"• <b>UTR:</b> <code>{html.escape(clean_utr)}</code>\n"
                    f"• <b>Attempt:</b> {attempts_used}/{MAX_UTR_ATTEMPTS}",
                    parse_mode="HTML",
                )
            except TelegramError:
                pass
        else:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"⏳ <b>Verifying your payment...</b>\n\n"
                    f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
                    f"• <b>UTR:</b> <code>{html.escape(clean_utr)}</code>\n"
                    f"• <b>Attempt:</b> {attempts_used}/{MAX_UTR_ATTEMPTS}"
                ),
                parse_mode="HTML",
            )

        result = await verify_bharatpe_payment(clean_utr, expected_amount)

        if result.get("ok"):
            context.user_data.pop("awaiting_utr_txid", None)
            cancel_expiry_job(context, txid)

            if deposit.get("purpose") == "coupon" and deposit.get("slot_id"):
                async with _INVENTORY_LOCK:
                    order_res = finalize_upi_coupon_purchase(
                        txid=txid,
                        user_id=user_id,
                        utr=clean_utr,
                        paid_amount=expected_amount,
                    )
                if not order_res.get("ok"):
                    await msg.edit_text(
                        "❌ <b>Order Could Not Be Processed</b>\n\nThis UTR or transaction has already been redeemed.",
                        parse_mode="HTML",
                    )
                    return

                if order_res.get("fallback_credited"):
                    new_avail = order_res["new_available_balance"]
                    ref_bal = order_res["referral_balance"]
                    await msg.edit_text(
                        f"⚠️ <b>Item Sold Out During Payment — Wallet Credited Instead!</b>\n\n"
                        f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
                        f"• <b>UTR:</b> <code>{html.escape(clean_utr)}</code>\n"
                        f"• <b>Credited to Available Balance:</b> <b>₹{expected_amount:.2f}</b>\n"
                        f"• <b>Total Wallet Balance:</b> <b>₹{new_avail + ref_bal:.2f}</b>",
                        parse_mode="HTML",
                    )
                    await notify_admin_wallet_delivery(
                        context=context,
                        user_id=user_id,
                        first_name=order_res.get("first_name"),
                        username=order_res.get("username"),
                        txid=txid,
                        utr=clean_utr,
                        payer_name=str(result.get("payer", "User")),
                        credited_amount=expected_amount,
                        previous_available=order_res["previous_available_balance"],
                        new_available=new_avail,
                        referral_balance=ref_bal,
                    )
                    return

                await msg.edit_text(
                    format_delivered_receipt(order_res),
                    parse_mode="HTML",
                )
                await send_order_attachment_if_multi(context.bot, chat_id, order_res)
                await notify_admin_coupon_order_delivery(
                    context=context,
                    user_id=user_id,
                    first_name=order_res.get("first_name"),
                    username=order_res.get("username"),
                    order_id=order_res["order_id"],
                    txid=txid,
                    payment_method="UPI",
                    utr=clean_utr,
                    coupon_name=order_res["coupon_name"],
                    quantity=int(order_res["quantity"]),
                    total_price=float(order_res["total_price"]),
                    delivered_codes=order_res["delivered_codes"],
                    remaining_total_balance=float(order_res["remaining_total_balance"]),
                )
                return

            credit_res = finalize_wallet_deposit(
                txid=txid,
                user_id=user_id,
                utr=clean_utr,
                credited_amount=expected_amount,
            )
            if not credit_res.get("ok"):
                await msg.edit_text(
                    "❌ <b>Payment Could Not Be Credited</b>\n\nThis UTR or transaction has already been processed.",
                    parse_mode="HTML",
                )
                return

            new_avail = credit_res["new_available_balance"]
            ref_bal = credit_res["referral_balance"]
            total_bal = new_avail + ref_bal
            await msg.edit_text(
                f"✅ <b>Payment Verified &amp; Wallet Credited!</b>\n\n"
                f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
                f"• <b>UTR:</b> <code>{html.escape(clean_utr)}</code>\n"
                f"• <b>Amount Added:</b> <b>₹{expected_amount:.2f}</b>\n\n"
                f"<b>Updated Wallet Summary</b>\n"
                f"• <b>Available Balance:</b> <b>₹{new_avail:.2f}</b>\n"
                f"• <b>Referral Balance:</b> <b>₹{ref_bal:.2f}</b>\n"
                f"• <b>Total Balance:</b> <b>₹{total_bal:.2f}</b>",
                parse_mode="HTML",
            )

            await notify_admin_wallet_delivery(
                context=context,
                user_id=user_id,
                first_name=credit_res.get("first_name"),
                username=credit_res.get("username"),
                txid=txid,
                utr=clean_utr,
                payer_name=str(result.get("payer", "User")),
                credited_amount=expected_amount,
                previous_available=credit_res["previous_available_balance"],
                new_available=new_avail,
                referral_balance=ref_bal,
            )
            return

        context.user_data.pop("awaiting_utr_txid", None)
        reason = result.get("reason", "NOT_FOUND")

        if reason == "TOKEN_EXPIRED":
            detail = (
                "Payment gateway session is currently under maintenance. "
                "The administrator has been notified — please tap <b>Refresh / Recheck</b> shortly."
            )
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=(
                        f"🚨 <b>Urgent Alert:</b> User <code>{user_id}</code> tried verifying UTR "
                        f"<code>{html.escape(clean_utr)}</code> (₹{expected_amount:.2f}), "
                        "but the BharatPe token is expired! Send /curl with a fresh cURL right away."
                    ),
                    parse_mode="HTML",
                )
            except TelegramError:
                pass
        elif reason == "AMOUNT_MISMATCH":
            rec_amt = result.get("received_amount", 0.0)
            detail = (
                f"Received amount (<b>₹{rec_amt:.2f}</b>) is less than the required order amount "
                f"(<b>₹{expected_amount:.2f}</b>). Please check your UTR or contact support."
            )
        else:
            detail = (
                "Payment was not found yet for this UTR. If you just paid, wait 30–60 seconds "
                "and tap <b>🔄 Refresh / Recheck</b>, or re-submit a corrected 12-digit UTR."
            )

        retry_kb = build_utr_retry_keyboard(txid, attempts_left)
        await msg.edit_text(
            f"⚠️ <b>Payment Not Verified Yet</b>\n\n"
            f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
            f"• <b>Submitted UTR:</b> <code>{html.escape(clean_utr)}</code>\n"
            f"• <b>Attempts Used:</b> {attempts_used}/{MAX_UTR_ATTEMPTS}\n\n"
            f"{detail}",
            reply_markup=retry_kb,
            parse_mode="HTML",
        )


# =====================================================================
# Standard Views & Callbacks
# =====================================================================


async def verify_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.effective_chat and update.effective_chat.type != ChatType.PRIVATE:
        return
    if await guard_maintenance_mode(update, context):
        return

    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    ensure_user_record(user.id, user.username, user.first_name)
    missing = await get_missing_channels(context, user.id)
    if not missing:
        await query.answer("Membership verified. Access granted.", show_alert=False)
        await on_access_granted(update, context)
        return

    await query.answer(
        "Access denied. Please join all remaining channels before verifying.",
        show_alert=True,
    )
    keyboard = build_force_join_keyboard(missing)
    text = format_recheck_message(
        user.first_name or "User", user.id, user.username, missing
    )
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except TelegramError:
        pass


async def show_stock_status(
    update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False
) -> None:
    clear_all_pending_input_states(context)
    text = format_stock_status_message()
    keyboard = build_stock_web_keyboard()
    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    elif update.message:
        await update.message.reply_text(
            text=text, reply_markup=keyboard, parse_mode="HTML"
        )


async def show_profile(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    if not user or not update.message:
        return
    clear_all_pending_input_states(context)
    ensure_user_record(user.id, user.username, user.first_name)
    text = format_profile_message(user.id, user.username)
    await update.message.reply_text(
        text=text, reply_markup=build_profile_web_keyboard(), parse_mode="HTML"
    )


async def show_refer_and_earn(
    update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback: bool = False
) -> None:
    user = update.effective_user
    if not user:
        return
    clear_all_pending_input_states(context)
    ensure_user_record(user.id, user.username, user.first_name)
    bot_username = context.bot.username or (await context.bot.get_me()).username
    text, ref_link = format_refer_message(user.id, bot_username)
    keyboard = build_refer_keyboard(ref_link)

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    elif update.message:
        await update.message.reply_text(
            text=text, reply_markup=keyboard, parse_mode="HTML"
        )


async def show_orders(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
    from_callback: bool = False,
) -> None:
    user = update.effective_user
    if not user:
        return
    clear_all_pending_input_states(context)
    ensure_user_record(user.id, user.username, user.first_name)
    text, total_orders, safe_page = format_orders_message(user.id, page=page)
    keyboard = build_orders_web_keyboard(safe_page, total_orders)

    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    elif update.message:
        await update.message.reply_text(
            text=text, reply_markup=keyboard, parse_mode="HTML"
        )


async def show_leaderboard(update: Update) -> None:
    if not update.message:
        return
    text = format_leaderboard_message()
    await update.message.reply_text(text=text, parse_mode="HTML")


async def handle_menu_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if await guard_maintenance_mode(update, context):
        return
    if not update.message or not update.effective_user:
        return
    clear_all_pending_input_states(context)
    allowed = await enforce_force_join(update, context)
    if not allowed:
        return

    user = update.effective_user
    ensure_user_record(user.id, user.username, user.first_name)
    choice = (update.message.text or "").strip()

    if choice == BTN_STOCK:
        await show_stock_status(update, context, from_callback=False)
    elif choice == BTN_BUY:
        await show_buy_catalog(update, context, from_callback=False)
    elif choice == BTN_PROFILE:
        await show_profile(update, context)
    elif choice == BTN_ORDERS:
        await show_orders(update, context, page=0, from_callback=False)
    elif choice == BTN_LEADERBOARD:
        await show_leaderboard(update)
    elif choice == BTN_REFER:
        await show_refer_and_earn(update, context, from_callback=False)
    elif choice == BTN_SUPPORT:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    styled_inline_btn(
                        text="🆘 Contact Support", style="danger", url=SUPPORT_BOT_URL
                    )
                ]
            ]
        )
        await update.message.reply_text(
            f"🆘 <b>Support</b>\n\nReach our support desk here: {SUPPORT_BOT_URL}",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    elif choice == BTN_WALLET:
        await show_wallet(update, context, from_callback=False)
    elif choice == BTN_MAIN_CHANNELS:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    styled_inline_btn(
                        text="📢 Open Main Channel",
                        style="primary",
                        url=MAIN_CHANNEL_URL,
                    )
                ]
            ]
        )
        await update.message.reply_text(
            f"📢 <b>Our Main Channels</b>\n\nJoin our main channel here: {MAIN_CHANNEL_URL}",
            reply_markup=keyboard,
            parse_mode="HTML",
        )


async def handle_inline_callbacks(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if update.effective_chat and update.effective_chat.type != ChatType.PRIVATE:
        return

    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    data = query.data or ""

    # /admin callbacks (strictly ADMIN_ID only)
    if data.startswith("adm_"):
        if user.id != ADMIN_ID:
            if await guard_maintenance_mode(update, context):
                return
            await query.answer("Access Denied: Administrator only.", show_alert=True)
            return

        if data == "adm_menu":
            clear_all_pending_input_states(context)
            await query.answer()
            await query.edit_message_text(
                text="🛡️ <b>Admin Controls</b>\n\nSelect an action below:",
                reply_markup=build_admin_inbox_menu_keyboard(),
                parse_mode="HTML",
            )
            return

        if data == "adm_maintenance":
            clear_all_pending_input_states(context)
            await query.answer()
            await query.edit_message_text(
                text=format_admin_maintenance_message(),
                reply_markup=build_admin_maintenance_toggle_keyboard(),
                parse_mode="HTML",
            )
            return

        if data == "adm_maint_toggle":
            new_state = not is_maintenance_enabled()
            set_maintenance_enabled(new_state)
            await query.answer(
                f"Maintenance Mode {'ON' if new_state else 'OFF'}",
                show_alert=False,
            )
            await query.edit_message_text(
                text=format_admin_maintenance_message(),
                reply_markup=build_admin_maintenance_toggle_keyboard(),
                parse_mode="HTML",
            )
            return

        if data == "adm_broadcast":
            clear_all_pending_input_states(context)
            await query.answer()
            context.user_data["admin_cmd_state"] = {"mode": "broadcast"}
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="adm_menu"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    "📢 <b>Global User Broadcast</b>\n\n"
                    "Send the message you want to broadcast to <b>all registered users</b> now.\n"
                    "<i>You can send any text, photo, video, link, sticker, document, or voice note.</i>"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data.startswith("adm_users:"):
            clear_all_pending_input_states(context)
            try:
                page_num = int(data.split(":", 1)[1])
            except ValueError:
                page_num = 0
            await query.answer()
            text, total_users, safe_page = format_admin_users_list_page(page_num)
            kb = build_admin_users_pagination_keyboard(safe_page, total_users)
            await query.edit_message_text(
                text=text, reply_markup=kb, parse_mode="HTML"
            )
            return

        if data == "adm_check_order":
            clear_all_pending_input_states(context)
            await query.answer()
            context.user_data["admin_cmd_state"] = {"mode": "check_order"}
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="adm_menu"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    "🔍 <b>Check Order ID</b>\n\n"
                    "Please enter the <b>Order ID</b> (e.g., <code>ORD...</code>) or <b>Transaction ID</b> (<code>TXN...</code>) to inspect full details:"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data == "adm_create_coupon":
            clear_all_pending_input_states(context)
            await query.answer()
            context.user_data["admin_cmd_state"] = {
                "mode": "create_coupon",
                "step": "amount",
            }
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="adm_menu"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    "🎟️ <b>Create Coupon for Bot</b>\n\n"
                    "Enter the <b>Coupon Reward Amount (₹)</b> that each user will receive upon claiming (e.g., <code>10</code> or <code>25</code>):"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data == "adm_refund_user":
            clear_all_pending_input_states(context)
            await query.answer()
            context.user_data["admin_cmd_state"] = {
                "mode": "refund_user",
                "step": "order_id",
            }
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="adm_menu"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    "💸 <b>Refund User — Step 1</b>\n\n"
                    "Please enter the <b>Order ID</b> (e.g., <code>ORD...</code>) to initiate a wallet refund:"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data == "adm_rfd_yes":
            cmd_state = context.user_data.get("admin_cmd_state")
            if (
                not isinstance(cmd_state, dict)
                or cmd_state.get("mode") != "refund_user"
                or cmd_state.get("step") != "confirm"
            ):
                await query.answer("Refund session expired. Please start again.", show_alert=True)
                return

            order_id_val = str(cmd_state.get("order_id", ""))
            refund_qty_val = int(cmd_state.get("refund_qty", 0))
            context.user_data.pop("admin_cmd_state", None)

            async with _INVENTORY_LOCK:
                res = process_order_wallet_refund(order_id_val, refund_qty_val)

            if not res.get("ok"):
                await query.answer(str(res.get("reason", "Refund failed.")), show_alert=True)
                await query.edit_message_text(
                    text=f"❌ <b>Refund Failed</b>\n\n{html.escape(str(res.get('reason', 'Unable to process refund.')))}",
                    reply_markup=build_admin_inbox_menu_keyboard(),
                    parse_mode="HTML",
                )
                return

            await query.answer("Refund initiated!")
            target_uid = int(res["user_id"])
            uname_str = format_username(res.get("username"))

            await query.edit_message_text(
                text=(
                    "✅ <b>Wallet Refund Completed!</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• <b>Refund ID:</b> <code>{html.escape(res['refund_id'])}</code>\n"
                    f"• <b>Order ID:</b> <code>{html.escape(res['order_id'])}</code>\n"
                    f"• <b>User ID:</b> <code>{target_uid}</code> ({uname_str})\n"
                    f"• <b>Item:</b> <b>{html.escape(res['coupon_name'])}</b>\n"
                    f"• <b>Refunded Quantity:</b> <b>{res['refund_qty']}/{res['total_order_qty']}</b>\n"
                    f"• <b>Amount Credited to Wallet:</b> <b>₹{res['refund_amount']:.2f}</b>\n"
                    f"• <b>User's New Available Balance:</b> <b>₹{res['new_available_balance']:.2f}</b>"
                ),
                reply_markup=build_admin_inbox_menu_keyboard(),
                parse_mode="HTML",
            )

            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        "💸 <b>Order Refund Credited to Your Wallet!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"• <b>Refund ID:</b> <code>{html.escape(res['refund_id'])}</code>\n"
                        f"• <b>Order ID:</b> <code>{html.escape(res['order_id'])}</code>\n"
                        f"• <b>Item:</b> <b>{html.escape(res['coupon_name'])}</b>\n"
                        f"• <b>Refunded Quantity:</b> <b>{res['refund_qty']}</b>\n"
                        f"• <b>Refund Amount Credited:</b> <b>₹{res['refund_amount']:.2f}</b>\n\n"
                        f"• <b>Updated Available Balance:</b> <b>₹{res['new_available_balance']:.2f}</b>\n"
                        f"• <b>Total Wallet Balance:</b> <b>₹{res['total_balance']:.2f}</b>"
                    ),
                    parse_mode="HTML",
                )
            except TelegramError as exc:
                logger.warning("Failed to notify user %s of refund: %s", target_uid, exc)
            return

    # /adminpanel callbacks (strictly ADMIN_ID only)
    if data.startswith("ap_"):
        if user.id != ADMIN_ID:
            if await guard_maintenance_mode(update, context):
                return
            await query.answer("Access Denied: Administrator only.", show_alert=True)
            return

        if data == "ap_home":
            clear_all_pending_input_states(context)
            await query.answer()
            await query.edit_message_text(
                text=format_admin_panel_overview(),
                reply_markup=build_admin_panel_keyboard(),
                parse_mode="HTML",
            )
            return

        if data == "ap_check_qty":
            clear_all_pending_input_states(context)
            await query.answer("Fetched live Firebase inventory.")
            await query.edit_message_text(
                text=format_admin_live_quantity_report(),
                reply_markup=build_admin_panel_keyboard(),
                parse_mode="HTML",
            )
            return

        if data == "ap_del_slots":
            clear_all_pending_input_states(context)
            slots = fetch_all_slots()
            if not slots:
                await query.answer("No slots available to delete.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    "🗑️ <b>Delete Slots</b>\n\n"
                    "Select a slot or folder below to delete:"
                ),
                reply_markup=build_admin_delete_slots_keyboard(),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_del_fld:"):
            sid = data.split(":", 1)[1]
            slots = fetch_all_slots()
            folder_slot = next((s for s in slots if s["slot_id"] == sid and s.get("is_folder")), None)
            if not folder_slot:
                await query.answer("Folder not found.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    f"📁 <b>Folder: {html.escape(str(folder_slot['name']))}</b>\n\n"
                    "Select an item inside this folder or delete the entire folder:"
                ),
                reply_markup=build_admin_delete_subitems_keyboard(folder_slot),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_del_ask:"):
            parts = data.split(":", 2)
            sid = parts[1] if len(parts) > 1 else ""
            sub_id = parts[2] if len(parts) > 2 else ""
            if sub_id == "ALL":
                slots = fetch_all_slots()
                folder_slot = next((s for s in slots if s["slot_id"] == sid and s.get("is_folder")), None)
                if not folder_slot:
                    await query.answer("Folder not found.", show_alert=True)
                    return
                label = f"Folder: {folder_slot['name']} (Total Qty: {int(folder_slot['stock'])})"
            else:
                item = fetch_sellable_item(sid, sub_id)
                if not item:
                    await query.answer("Item not found.", show_alert=True)
                    return
                label = f"{item['display_name']} (₹{float(item['price']):g} | Qty: {int(item['stock'])})"

            await query.answer()
            await query.edit_message_text(
                text=(
                    "⚠️ <b>Confirm Deletion</b>\n\n"
                    f"Are you sure you want to delete <b>{html.escape(label)}</b>?\n"
                    "<i>This will remove the slot and its unsold codes from Firebase.</i>"
                ),
                reply_markup=build_admin_delete_confirm_keyboard(sid, sub_id),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_del_yes:"):
            parts = data.split(":", 2)
            sid = parts[1] if len(parts) > 1 else ""
            sub_id = parts[2] if len(parts) > 2 else ""
            target_sub = "" if sub_id == "ALL" else sub_id

            async with _INVENTORY_LOCK:
                res = delete_slot_or_subitem_in_firebase(sid, target_sub)

            if not res.get("ok"):
                await query.answer(str(res.get("reason", "Delete failed.")), show_alert=True)
                return

            await query.answer("Deleted!")
            await query.edit_message_text(
                text=(
                    "🗑️ <b>Deleted Successfully!</b>\n\n"
                    f"• <b>Removed:</b> <b>{html.escape(str(res['deleted_name']))}</b>"
                ),
                reply_markup=build_admin_panel_keyboard(),
                parse_mode="HTML",
            )
            return

        if data == "ap_change_price":
            clear_all_pending_input_states(context)
            slots = fetch_all_slots()
            if not slots:
                await query.answer("No slots available in inventory.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    "💲 <b>Change Price Per Unit</b>\n\n"
                    "Select a slot or folder below to update its price per unit:"
                ),
                reply_markup=build_admin_price_slots_keyboard(),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_prc_fld:"):
            sid = data.split(":", 1)[1]
            slots = fetch_all_slots()
            folder_slot = next((s for s in slots if s["slot_id"] == sid and s.get("is_folder")), None)
            if not folder_slot:
                await query.answer("Folder not found.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    f"📁 <b>Folder: {html.escape(str(folder_slot['name']))}</b>\n\n"
                    "Select an item inside this folder to change its price per unit:"
                ),
                reply_markup=build_admin_price_subitems_keyboard(folder_slot),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_prc_itm:"):
            parts = data.split(":", 2)
            sid = parts[1] if len(parts) > 1 else ""
            sub_id = parts[2] if len(parts) > 2 else ""
            item = fetch_sellable_item(sid, sub_id)
            if not item:
                await query.answer("Slot item not found.", show_alert=True)
                return
            await query.answer()
            context.user_data["admin_panel_state"] = {
                "mode": "change_price",
                "step": "price",
                "slot_id": sid,
                "sub_id": sub_id,
            }
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="ap_home"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    f"💲 <b>Change Price: {html.escape(str(item['display_name']))}</b>\n"
                    f"• <b>Current Price Per Unit:</b> <b>₹{float(item['price']):g}</b>\n\n"
                    "Enter the <b>new price per unit</b> in INR (e.g., <code>25</code> or <code>49.50</code>):"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data == "ap_new_slot":
            clear_all_pending_input_states(context)
            await query.answer()
            context.user_data["admin_panel_state"] = {"mode": "new_slot", "step": "name"}
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="ap_home"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    "➕ <b>Create New Slot — Step 1</b>\n\n"
                    "Please enter the <b>Slot / Folder Name</b> (e.g., <code>Swiggy Vouchers</code>):"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data in ("ap_folder_yes", "ap_folder_no"):
            ap_state = context.user_data.get("admin_panel_state")
            if not isinstance(ap_state, dict) or ap_state.get("mode") != "new_slot" or not ap_state.get("name"):
                await query.answer("Session expired. Please start again.", show_alert=True)
                return
            await query.answer()
            cancel_kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="ap_home"
                        )
                    ]
                ]
            )
            if data == "ap_folder_yes":
                ap_state["is_folder"] = True
                ap_state["step"] = "sub_name"
                await query.edit_message_text(
                    text=(
                        f"📁 <b>Folder Selected:</b> <b>{html.escape(str(ap_state['name']))}</b>\n\n"
                        "Please enter the <b>Sub-Item Name</b> to create inside this folder "
                        "(e.g., <code>Swiggy ₹100 Off</code>):"
                    ),
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
            else:
                ap_state["is_folder"] = False
                ap_state["sub_name"] = ""
                ap_state["step"] = "description"
                await query.edit_message_text(
                    text=(
                        f"🎟️ <b>Direct Slot:</b> <b>{html.escape(str(ap_state['name']))}</b>\n\n"
                        "📝 Please paste the <b>Description &amp; Terms</b> for this coupon:"
                    ),
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
            return

        if data == "ap_direct_add":
            clear_all_pending_input_states(context)
            slots = fetch_all_slots()
            if not slots:
                await query.answer(
                    "No existing slots found. Please create a New Slot first.",
                    show_alert=True,
                )
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    "⚡ <b>Direct Add Coupon</b>\n\n"
                    "Select a slot or folder below to add coupons, links, or JSON directly:"
                ),
                reply_markup=build_admin_direct_slots_keyboard(),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_dir_fld:"):
            sid = data.split(":", 1)[1]
            slots = fetch_all_slots()
            folder_slot = next((s for s in slots if s["slot_id"] == sid and s.get("is_folder")), None)
            if not folder_slot:
                await query.answer("Folder not found.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    f"📁 <b>Folder: {html.escape(str(folder_slot['name']))}</b>\n\n"
                    "Select the sub-item inside this folder where you want to add coupons/links/JSON:"
                ),
                reply_markup=build_admin_direct_subitems_keyboard(folder_slot),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_dir_itm:"):
            parts = data.split(":", 2)
            sid = parts[1] if len(parts) > 1 else ""
            sub_id = parts[2] if len(parts) > 2 else ""
            item = fetch_sellable_item(sid, sub_id)
            if not item:
                await query.answer("Slot item not found.", show_alert=True)
                return
            await query.answer()
            context.user_data["admin_panel_state"] = {
                "mode": "direct_add",
                "step": "codes",
                "slot_id": sid,
                "sub_id": sub_id,
            }
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="❌ Cancel", style="danger", callback_data="ap_home"
                        )
                    ]
                ]
            )
            await query.edit_message_text(
                text=(
                    f"⚡ <b>Direct Add to: {html.escape(str(item['display_name']))}</b>\n"
                    f"• <b>Current Live Stock:</b> <b>{int(item['stock'])}</b>\n\n"
                    "Send your coupon codes, links, or JSON data now:\n"
                    "• Upload a <code>.txt</code> / <code>.json</code> file, <b>OR</b>\n"
                    "• Paste them directly in chat (single-line or multi-line JSON, links &amp; codes are preserved)."
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data == "ap_dl_codes":
            clear_all_pending_input_states(context)
            slots = fetch_all_slots()
            if not slots:
                await query.answer("No slots available in inventory.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    "📥 <b>Download / Withdraw Codes</b>\n\n"
                    "Select a live slot or folder below to withdraw codes/links:\n"
                    "<i>(Admin withdrawals do not appear on the Leaderboard.)</i>"
                ),
                reply_markup=build_admin_download_slots_keyboard(),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_dl_fld:"):
            sid = data.split(":", 1)[1]
            slots = fetch_all_slots()
            folder_slot = next((s for s in slots if s["slot_id"] == sid and s.get("is_folder")), None)
            if not folder_slot:
                await query.answer("Folder not found.", show_alert=True)
                return
            await query.answer()
            await query.edit_message_text(
                text=(
                    f"📁 <b>Folder: {html.escape(str(folder_slot['name']))}</b>\n\n"
                    "Select a sub-item to withdraw codes/links from:"
                ),
                reply_markup=build_admin_download_subitems_keyboard(folder_slot),
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_dl_itm:"):
            parts = data.split(":", 2)
            sid = parts[1] if len(parts) > 1 else ""
            sub_id = parts[2] if len(parts) > 2 else ""
            item = fetch_sellable_item(sid, sub_id)
            if not item:
                await query.answer("Slot item not found.", show_alert=True)
                return
            avail = int(item["stock"])
            if avail <= 0:
                await query.answer("0 live codes available in this slot.", show_alert=True)
                return
            await query.answer()
            context.user_data["admin_panel_state"] = {
                "mode": "download_codes",
                "step": "qty",
                "slot_id": sid,
                "sub_id": sub_id,
            }
            kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text=f"📤 Withdraw ALL ({avail})",
                            style="success",
                            callback_data=f"ap_dl_all:{sid}:{sub_id}",
                        )
                    ],
                    [
                        styled_inline_btn(
                            text="❌ Cancel",
                            style="danger",
                            callback_data="ap_home",
                        )
                    ],
                ]
            )
            await query.edit_message_text(
                text=(
                    f"📥 <b>Withdraw Codes: {html.escape(str(item['display_name']))}</b>\n"
                    f"• <b>Available Live Stock:</b> <b>{avail}</b>\n\n"
                    f"Enter the quantity you want to withdraw (<code>1</code> to <code>{avail}</code>), "
                    "or type <code>ALL</code> (or tap <b>Withdraw ALL</b> below):"
                ),
                reply_markup=kb,
                parse_mode="HTML",
            )
            return

        if data.startswith("ap_dl_all:"):
            parts = data.split(":", 2)
            sid = parts[1] if len(parts) > 1 else ""
            sub_id = parts[2] if len(parts) > 2 else ""
            clear_all_pending_input_states(context)
            async with _INVENTORY_LOCK:
                res = withdraw_codes_for_admin(sid, sub_id, requested_qty=None)
            if not res.get("ok"):
                await query.answer(str(res.get("reason", "Withdrawal failed.")), show_alert=True)
                return
            await query.answer("Withdrawn all codes!")
            await send_withdrawn_codes_file(update, context, res, from_callback=True)
            return

    if await guard_maintenance_mode(update, context):
        return

    allowed = await enforce_force_join(update, context)
    if not allowed:
        return

    if data == "stock_refresh":
        await query.answer("Refreshing live stock...")
        await show_stock_status(update, context, from_callback=True)
    elif data == "open_buy_menu":
        await query.answer()
        await show_buy_catalog(update, context, from_callback=True)
    elif data.startswith("buy_folder:"):
        sid = data.split(":", 1)[1]
        await query.answer()
        await show_buy_folder(update, context, slot_id=sid, from_callback=True)
    elif data.startswith("buy_itm:"):
        parts = data.split(":", 2)
        sid = parts[1] if len(parts) > 1 else ""
        sub_id = parts[2] if len(parts) > 2 else ""
        await query.answer()
        await show_product_detail(
            update, context, slot_id=sid, sub_id=sub_id, from_callback=True
        )
    elif data.startswith("buy_qty:"):
        parts = data.split(":", 3)
        try:
            sid = parts[1]
            sub_id = parts[2]
            qty = int(parts[3])
        except (IndexError, ValueError):
            await query.answer("Invalid selection.", show_alert=True)
            return
        await query.answer()
        await show_order_summary(
            update, context, slot_id=sid, sub_id=sub_id, quantity=qty, from_callback=True
        )
    elif data.startswith("buy_cqty:"):
        parts = data.split(":", 2)
        sid = parts[1] if len(parts) > 1 else ""
        sub_id = parts[2] if len(parts) > 2 else ""
        item = fetch_sellable_item(sid, sub_id)
        if not item or int(item["stock"]) <= 0:
            await query.answer("This coupon is currently out of stock.", show_alert=True)
            return
        await query.answer()
        clear_all_pending_input_states(context)
        context.user_data["awaiting_custom_qty_target"] = {"slot_id": sid, "sub_id": sub_id}
        kb = InlineKeyboardMarkup(
            [
                [
                    styled_inline_btn(
                        text="⬅️ Back",
                        style="danger",
                        callback_data=f"buy_itm:{sid}:{sub_id}",
                    )
                ]
            ]
        )
        prompt = (
            f"✏️ <b>Enter Custom Quantity</b>\n\n"
            f"• <b>Coupon:</b> {html.escape(str(item['display_name']))}\n"
            f"• <b>Price Per Unit:</b> ₹{float(item['price']):g}\n"
            f"• <b>Available Stock:</b> <b>{int(item['stock'])}</b>\n\n"
            f"Please enter a whole number between <b>1</b> and <b>{int(item['stock'])}</b>:"
        )
        try:
            await query.edit_message_text(text=prompt, reply_markup=kb, parse_mode="HTML")
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=prompt,
                    reply_markup=kb,
                    parse_mode="HTML",
                )
    elif data.startswith("chk_upi:"):
        parts = data.split(":", 3)
        try:
            sid = parts[1]
            sub_id = parts[2]
            qty = int(parts[3])
        except (IndexError, ValueError):
            await query.answer("Invalid order request.", show_alert=True)
            return
        item = fetch_sellable_item(sid, sub_id)
        if not item or int(item["stock"]) < qty or qty < 1:
            await query.answer(
                "Requested stock is no longer available. Please re-check stock.",
                show_alert=True,
            )
            await show_buy_catalog(update, context, from_callback=True)
            return
        total_amount = round(float(item["price"]) * qty, 2)
        await query.answer(f"Generating ₹{total_amount:g} UPI QR...")
        await start_upi_payment_session(
            update=update,
            context=context,
            amount=total_amount,
            purpose="coupon",
            item=item,
            quantity=qty,
        )
    elif data.startswith("chk_wlt:"):
        parts = data.split(":", 3)
        try:
            sid = parts[1]
            sub_id = parts[2]
            qty = int(parts[3])
        except (IndexError, ValueError):
            await query.answer("Invalid order request.", show_alert=True)
            return

        async with get_user_lock(user.id), _INVENTORY_LOCK:
            item = fetch_sellable_item(sid, sub_id)
            if not item or int(item["stock"]) < qty or qty < 1:
                await query.answer(
                    "Requested stock is no longer available.", show_alert=True
                )
                await show_buy_catalog(update, context, from_callback=True)
                return

            total_amount = round(float(item["price"]) * qty, 2)
            stats = fetch_user_profile_stats(user.id)
            if float(stats["total_balance"]) + 1e-6 < total_amount:
                await query.answer(
                    f"Insufficient wallet balance (₹{stats['total_balance']:.2f}). Opening Wallet top-up...",
                    show_alert=True,
                )
                await show_wallet(update, context, from_callback=True)
                return

            purchase_res = execute_wallet_coupon_purchase(
                user_id=user.id, slot_id=sid, sub_id=sub_id, quantity=qty
            )
            if not purchase_res.get("ok"):
                if purchase_res.get("reason") == "INSUFFICIENT_BALANCE":
                    await query.answer(
                        "Insufficient wallet balance. Please add funds first.",
                        show_alert=True,
                    )
                    await show_wallet(update, context, from_callback=True)
                else:
                    await query.answer(
                        "Unable to complete order due to live stock change.",
                        show_alert=True,
                    )
                    await show_buy_catalog(update, context, from_callback=True)
                return

            await query.answer("Order purchased successfully!")
            receipt_text = format_delivered_receipt(purchase_res)
            try:
                await query.edit_message_text(text=receipt_text, parse_mode="HTML")
            except TelegramError:
                if update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=receipt_text,
                        parse_mode="HTML",
                    )

            target_chat_id = update.effective_chat.id if update.effective_chat else user.id
            await send_order_attachment_if_multi(context.bot, target_chat_id, purchase_res)

            await notify_admin_coupon_order_delivery(
                context=context,
                user_id=user.id,
                first_name=purchase_res.get("first_name"),
                username=purchase_res.get("username"),
                order_id=purchase_res["order_id"],
                txid=purchase_res["txid"],
                payment_method="Wallet",
                utr=None,
                coupon_name=purchase_res["coupon_name"],
                quantity=int(purchase_res["quantity"]),
                total_price=float(purchase_res["total_price"]),
                delivered_codes=purchase_res["delivered_codes"],
                remaining_total_balance=float(purchase_res["remaining_total_balance"]),
            )
    elif data.startswith("chk_cnl:"):
        cancelled_order_id = f"ORD{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"
        clear_all_pending_input_states(context)
        await query.answer("Order cancelled.")
        cancel_text = (
            "❌ <b>Order Cancelled</b>\n\n"
            f"• <b>Order ID:</b> <code>{cancelled_order_id}</code>\n\n"
            "Your payment session was cancelled. Tap <b>🛒 Buy Coupon</b> to start again."
        )
        try:
            await query.edit_message_text(text=cancel_text, parse_mode="HTML")
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=cancel_text,
                    parse_mode="HTML",
                )
    elif data == "open_refer":
        await query.answer()
        await show_refer_and_earn(update, context, from_callback=True)
    elif data == "open_wallet":
        await query.answer()
        try:
            if query.message and query.message.photo:
                await query.message.delete()
        except TelegramError:
            pass
        await show_wallet(update, context, from_callback=True)
    elif data == "wallet_claim_coupon":
        await query.answer()
        clear_all_pending_input_states(context)
        context.user_data["awaiting_promo_coupon"] = True
        kb = InlineKeyboardMarkup(
            [
                [
                    styled_inline_btn(
                        text="🔙 Back to Wallet",
                        style="danger",
                        callback_data="open_wallet",
                    )
                ]
            ]
        )
        prompt_text = (
            "🎟️ <b>Claim Bot Coupon</b>\n\n"
            "Please enter your <b>Coupon Code</b> below to redeem your instant wallet bonus:"
        )
        try:
            await query.edit_message_text(
                text=prompt_text,
                reply_markup=kb,
                parse_mode="HTML",
            )
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=prompt_text,
                    reply_markup=kb,
                    parse_mode="HTML",
                )
    elif data == "back_to_home":
        await query.answer()
        try:
            if query.message and query.message.photo:
                await query.message.delete()
        except TelegramError:
            pass
        await send_or_edit_home(update, context, from_callback=True)
    elif data.startswith("orders_page:"):
        await query.answer()
        try:
            page_num = int(data.split(":", 1)[1])
        except ValueError:
            page_num = 0
        await show_orders(update, context, page=page_num, from_callback=True)
    elif data.startswith("wallet_amt:"):
        try:
            amount = float(data.split(":", 1)[1])
        except ValueError:
            await query.answer("Invalid amount.", show_alert=True)
            return
        if amount < MIN_WALLET_TOPUP:
            await query.answer(
                f"Minimum top-up amount is ₹{MIN_WALLET_TOPUP:g}.", show_alert=True
            )
            return
        await query.answer(f"Generating ₹{amount:g} UPI QR...")
        await start_upi_payment_session(
            update=update, context=context, amount=amount, purpose="wallet"
        )
    elif data == "wallet_custom":
        await query.answer()
        clear_all_pending_input_states(context)
        context.user_data["awaiting_custom_amount"] = True
        kb = InlineKeyboardMarkup(
            [
                [
                    styled_inline_btn(
                        text="🔙 Back to Wallet",
                        style="danger",
                        callback_data="open_wallet",
                    )
                ]
            ]
        )
        prompt_text = (
            f"✏️ <b>Enter Custom Top-Up Amount</b>\n\n"
            f"Please enter a numeric amount in INR between <b>₹{MIN_WALLET_TOPUP:g}</b> and <b>₹{MAX_WALLET_TOPUP:g}</b> (e.g., <code>25</code> or <code>100</code>):"
        )
        try:
            await query.edit_message_text(
                text=prompt_text,
                reply_markup=kb,
                parse_mode="HTML",
            )
        except TelegramError:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=prompt_text,
                    reply_markup=kb,
                    parse_mode="HTML",
                )
    elif data.startswith("pay_paid:"):
        txid = data.split(":", 1)[1]
        dep = get_deposit_session(txid, user.id)
        if not dep or dep["status"] != "pending":
            await query.answer("This payment session is no longer active.", show_alert=True)
            return
        if int(time.time()) > int(dep["expires_at"]):
            mark_deposit_expired(txid)
            cancel_expiry_job(context, txid)
            await query.answer(
                "Payment QR Expired — Your payment session has timed out. Please start a new purchase to generate a fresh QR code.",
                show_alert=True,
            )
            return
        if int(dep["attempts"]) >= MAX_UTR_ATTEMPTS:
            await query.answer("Maximum 3 UTR attempts already used for this session.", show_alert=True)
            return

        await query.answer()
        clear_all_pending_input_states(context)
        context.user_data["awaiting_utr_txid"] = txid
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"🧾 <b>Submit 12-Digit UTR Number</b>\n\n"
                    f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n"
                    f"• <b>Amount:</b> <b>₹{float(dep['amount']):.2f}</b>\n\n"
                    "Please enter your <b>12-digit numeric UPI Reference / UTR number</b> (e.g., <code>432910482910</code>):"
                ),
                parse_mode="HTML",
            )
    elif data.startswith("pay_cancel:"):
        txid = data.split(":", 1)[1]
        cancel_deposit_session(txid, user.id)
        cancel_expiry_job(context, txid)
        clear_all_pending_input_states(context)
        await query.answer("Payment cancelled.")
        try:
            if query.message and query.message.photo:
                await query.message.delete()
        except TelegramError:
            pass
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "❌ <b>Order Cancelled</b>\n\n"
                    f"• <b>Order ID / TXID:</b> <code>{html.escape(txid)}</code>\n\n"
                    "Your payment session was cancelled. Tap <b>🛒 Buy Coupon</b> or <b>💰 Wallet</b> to start again."
                ),
                parse_mode="HTML",
            )
    elif data.startswith("utr_recheck:"):
        txid = data.split(":", 1)[1]
        dep = get_deposit_session(txid, user.id)
        if not dep or dep["status"] != "pending" or not dep.get("utr"):
            await query.answer("No active UTR session found to recheck.", show_alert=True)
            return
        await query.answer("Rechecking payment status...")
        if update.effective_chat:
            await run_utr_verification_flow(
                chat_id=update.effective_chat.id,
                user_id=user.id,
                txid=txid,
                raw_input=str(dep["utr"]),
                context=context,
                increment_attempt=False,
                status_message_to_edit=query.message,
            )
    elif data.startswith("utr_resubmit:"):
        txid = data.split(":", 1)[1]
        dep = get_deposit_session(txid, user.id)
        if not dep or dep["status"] != "pending":
            await query.answer("This payment session is no longer active.", show_alert=True)
            return
        if int(time.time()) > int(dep["expires_at"]):
            mark_deposit_expired(txid)
            cancel_expiry_job(context, txid)
            await query.answer(
                "Payment QR Expired — Your payment session has timed out. Please start a new purchase to generate a fresh QR code.",
                show_alert=True,
            )
            return
        attempts_used = int(dep["attempts"])
        if attempts_used >= MAX_UTR_ATTEMPTS:
            await query.answer(
                "Maximum 3 UTR submission attempts reached for this order.",
                show_alert=True,
            )
            return
        await query.answer()
        clear_all_pending_input_states(context)
        context.user_data["awaiting_utr_txid"] = txid
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"✏️ <b>Re-submit 12-Digit UTR</b> (Attempt {attempts_used + 1}/{MAX_UTR_ATTEMPTS})\n\n"
                    f"• <b>TXID:</b> <code>{html.escape(txid)}</code>\n\n"
                    "Please enter the corrected <b>12-digit numeric UTR number</b> (e.g., <code>432910482910</code>):"
                ),
                parse_mode="HTML",
            )


async def send_withdrawn_codes_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    res: dict[str, Any],
    from_callback: bool = False,
) -> None:
    chat = update.effective_chat
    if not chat:
        return

    codes: list[str] = res.get("codes", [])
    content_bytes = "\n".join(codes).encode("utf-8")
    bio = io.BytesIO(content_bytes)
    export_fname = str(res.get("filename") or "").strip()
    if not export_fname:
        safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(res["display_name"])).strip("_") or "codes"
        export_fname = f"{safe_slug}_{res['withdrawn_count']}_codes.txt"
    bio.name = export_fname
    bio.seek(0)

    summary_text = (
        "📥 <b>Codes Withdrawn Successfully</b>\n\n"
        f"• <b>Withdrawal ID:</b> <code>{html.escape(res['withdrawal_id'])}</code>\n"
        f"• <b>Slot / Item:</b> <b>{html.escape(res['display_name'])}</b>\n"
        f"• <b>Withdrawn Quantity:</b> <b>{res['withdrawn_count']}</b>\n"
        f"• <b>Remaining Live Stock:</b> <b>{res['remaining_stock']}</b>\n"
        "• <i>Excluded from Leaderboard.</i>"
    )
    if from_callback and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=summary_text,
                reply_markup=build_admin_panel_keyboard(),
                parse_mode="HTML",
            )
        except TelegramError:
            pass
    elif update.message:
        await update.message.reply_text(
            text=summary_text,
            reply_markup=build_admin_panel_keyboard(),
            parse_mode="HTML",
        )

    await context.bot.send_document(
        chat_id=chat.id,
        document=bio,
        caption=f"📄 {res['withdrawn_count']} withdrawn code(s) for {res['display_name']}",
    )


async def handle_admin_cmd_inputs(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Handles /admin Broadcast, Check Order ID, Create Coupon for Bot, and Refund User."""
    user = update.effective_user
    msg = update.message
    if not user or not msg or user.id != ADMIN_ID:
        return False

    cmd_state = context.user_data.get("admin_cmd_state")
    if not isinstance(cmd_state, dict):
        return False

    mode = cmd_state.get("mode")
    cancel_kb = InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="❌ Cancel", style="danger", callback_data="adm_menu"
                )
            ]
        ]
    )

    if mode == "broadcast":
        context.user_data.pop("admin_cmd_state", None)
        all_users = fetch_all_registered_users()
        if not all_users:
            await msg.reply_text(
                "⚠️ No registered users found in Firebase database to broadcast to.",
                reply_markup=build_admin_inbox_menu_keyboard(),
            )
            return True

        status_msg = await msg.reply_text(
            f"📡 <b>Broadcasting message to {len(all_users)} users...</b>",
            parse_mode="HTML",
        )

        sent_ok = 0
        blocked_cnt = 0
        failed_cnt = 0

        for u in all_users:
            target_uid = int(u["user_id"])
            try:
                await context.bot.copy_message(
                    chat_id=target_uid,
                    from_chat_id=msg.chat_id,
                    message_id=msg.message_id,
                )
                sent_ok += 1
            except RetryAfter as exc:
                await asyncio.sleep(float(exc.retry_after) + 0.5)
                try:
                    await context.bot.copy_message(
                        chat_id=target_uid,
                        from_chat_id=msg.chat_id,
                        message_id=msg.message_id,
                    )
                    sent_ok += 1
                except TelegramError:
                    failed_cnt += 1
            except Forbidden:
                blocked_cnt += 1
            except TelegramError:
                failed_cnt += 1
            await asyncio.sleep(0.04)

        await status_msg.edit_text(
            "✅ <b>Broadcast Completed!</b>\n\n"
            f"• <b>Total Users in Firebase:</b> <b>{len(all_users)}</b>\n"
            f"• <b>Delivered:</b> <b>{sent_ok}</b>\n"
            f"• <b>Blocked / Deactivated:</b> {blocked_cnt}\n"
            f"• <b>Failed:</b> {failed_cnt}",
            reply_markup=build_admin_inbox_menu_keyboard(),
            parse_mode="HTML",
        )
        return True

    if mode == "check_order":
        if not msg.text or not msg.text.strip():
            await msg.reply_text(
                "❌ Please type a valid <b>Order ID</b> (e.g., <code>ORD...</code>) or <b>TXID</b>:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        query_id = msg.text.strip()
        order = lookup_order_by_id(query_id)
        if not order:
            await msg.reply_text(
                f"❌ <b>Order ID Not Found</b>\n\n"
                f"No order matching <code>{html.escape(query_id)}</code> exists in the Firebase database.\n"
                "Please check the ID and try again, or tap <b>❌ Cancel</b>:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        context.user_data.pop("admin_cmd_state", None)
        await msg.reply_text(
            text=format_admin_order_lookup_report(order),
            reply_markup=build_admin_inbox_menu_keyboard(),
            parse_mode="HTML",
        )
        return True

    if mode == "create_coupon":
        step = cmd_state.get("step")
        if step == "amount":
            if not msg.text:
                await msg.reply_text(
                    "❌ Please enter a valid numeric amount in INR (e.g., <code>10</code> or <code>25</code>):",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True
            cleaned = msg.text.strip().replace("₹", "").replace(",", "").strip()
            if not re.fullmatch(r"\d+(\.\d{1,2})?", cleaned):
                await msg.reply_text(
                    "❌ <b>Invalid Amount Format</b>\n\nPlease enter numbers only (e.g., <code>10</code> or <code>50</code>):",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True
            amt = round(float(cleaned), 2)
            if not math.isfinite(amt) or amt <= 0 or amt > MAX_WALLET_TOPUP:
                await msg.reply_text(
                    f"❌ Please enter a valid amount between <b>₹1</b> and <b>₹{MAX_WALLET_TOPUP:g}</b>:",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            cmd_state["amount"] = amt
            cmd_state["step"] = "max_users"
            await msg.reply_text(
                f"✅ <b>Coupon Amount Saved:</b> <b>₹{amt:g}</b>\n\n"
                "👥 <b>How many users can claim this coupon?</b>\n"
                "Enter the maximum number of users (e.g., <code>10</code> or <code>20</code>):",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        if step == "max_users":
            if not msg.text or not re.fullmatch(r"\d+", msg.text.strip()):
                await msg.reply_text(
                    "❌ Please enter a valid whole number of users (e.g., <code>10</code> or <code>20</code>):",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True
            max_users = int(msg.text.strip())
            if max_users < 1 or max_users > 100000:
                await msg.reply_text(
                    "❌ User limit must be between <b>1</b> and <b>100000</b>. Please enter again:",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            coupon_amt = float(cmd_state["amount"])
            async with _PROMO_LOCK:
                created = create_bot_promo_coupon(coupon_amt, max_users)
            context.user_data.pop("admin_cmd_state", None)

            await msg.reply_text(
                "✅ <b>Bot Wallet Coupon Created!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Coupon Code:</b> <code>{html.escape(created['code'])}</code>\n"
                f"• <b>Wallet Credit Per User:</b> <b>₹{created['amount']:g}</b>\n"
                f"• <b>Max Claim Limit:</b> <b>{created['max_users']}</b> user(s)\n\n"
                "<i>Users can redeem this code from 💰 Wallet → 🎟️ Claim Coupon.</i>",
                reply_markup=build_admin_inbox_menu_keyboard(),
                parse_mode="HTML",
            )
            return True

    if mode == "refund_user":
        step = cmd_state.get("step")
        if step == "order_id":
            if not msg.text or not msg.text.strip():
                await msg.reply_text(
                    "❌ Please enter a valid <b>Order ID</b> (e.g., <code>ORD...</code>):",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            query_id = msg.text.strip()
            order = lookup_order_by_id(query_id)
            if not order:
                await msg.reply_text(
                    f"❌ <b>Order ID Not Found</b>\n\n"
                    f"No order matching <code>{html.escape(query_id)}</code> exists in Firebase.\n"
                    "Please enter a valid <b>Order ID</b> or tap <b>❌ Cancel</b>:",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            actual_oid = str(order.get("order_id", "")).strip()
            total_qty = int(order.get("quantity", 1))
            already_rfd = int(order.get("refunded_qty", 0))
            refundable_qty = max(0, total_qty - already_rfd)
            unit_price = float(order.get("price", 0.0))
            target_uid = int(order.get("user_id", 0))
            uname = format_username(order.get("username"))

            if refundable_qty <= 0:
                context.user_data.pop("admin_cmd_state", None)
                await msg.reply_text(
                    f"⚠️ <b>Order Already Fully Refunded</b>\n\n"
                    f"• <b>Order ID:</b> <code>{html.escape(actual_oid)}</code>\n"
                    f"• <b>Total Quantity:</b> {total_qty} (All {already_rfd} unit(s) already refunded).",
                    reply_markup=build_admin_inbox_menu_keyboard(),
                    parse_mode="HTML",
                )
                return True

            cmd_state["order_id"] = actual_oid
            cmd_state["refundable_qty"] = refundable_qty
            cmd_state["unit_price"] = unit_price
            cmd_state["user_id"] = target_uid
            cmd_state["coupon_name"] = str(order.get("coupon_name", "Item"))
            cmd_state["step"] = "qty"

            await msg.reply_text(
                "💸 <b>Refund User — Step 2</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Order ID:</b> <code>{html.escape(actual_oid)}</code>\n"
                f"• <b>Customer:</b> <code>{target_uid}</code> ({uname})\n"
                f"• <b>Product:</b> <b>{html.escape(str(order.get('coupon_name', 'Item')))}</b>\n"
                f"• <b>Unit Price:</b> ₹{unit_price:g}\n"
                f"• <b>Purchased Quantity:</b> {total_qty}\n"
                f"• <b>Available to Refund:</b> <b>{refundable_qty}</b> unit(s)\n\n"
                f"How many quantities do you want to refund? (Enter a number between <b>1</b> and <b>{refundable_qty}</b>):",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        if step == "qty":
            refundable_qty = int(cmd_state.get("refundable_qty", 1))
            if not msg.text or not re.fullmatch(r"\d+", msg.text.strip()):
                await msg.reply_text(
                    f"❌ Please enter a valid whole number between <b>1</b> and <b>{refundable_qty}</b>:",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            req_qty = int(msg.text.strip())
            if req_qty < 1 or req_qty > refundable_qty:
                await msg.reply_text(
                    f"❌ Quantity out of range. Please enter a number between <b>1</b> and <b>{refundable_qty}</b>:",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            unit_price = float(cmd_state.get("unit_price", 0.0))
            refund_amt = round(unit_price * req_qty, 2)
            cmd_state["refund_qty"] = req_qty
            cmd_state["step"] = "confirm"

            confirm_kb = InlineKeyboardMarkup(
                [
                    [
                        styled_inline_btn(
                            text="✅ Yes, Refund Now",
                            style="success",
                            callback_data="adm_rfd_yes",
                        ),
                        styled_inline_btn(
                            text="❌ No, Cancel",
                            style="danger",
                            callback_data="adm_menu",
                        ),
                    ]
                ]
            )

            await msg.reply_text(
                "⚠️ <b>Confirm Wallet Refund</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• <b>Order ID:</b> <code>{html.escape(str(cmd_state['order_id']))}</code>\n"
                f"• <b>Customer User ID:</b> <code>{cmd_state['user_id']}</code>\n"
                f"• <b>Product:</b> <b>{html.escape(str(cmd_state['coupon_name']))}</b>\n"
                f"• <b>Refund Quantity:</b> <b>{req_qty}</b> unit(s)\n"
                f"• <b>Total Refund Amount:</b> <b>₹{refund_amt:.2f}</b>\n\n"
                "Do you want to initiate this refund to the user's wallet?",
                reply_markup=confirm_kb,
                parse_mode="HTML",
            )
            return True

    return False


async def handle_admin_panel_inputs(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Handles step-by-step inputs for /adminpanel (New Slot / Folder, Direct Add & Download Codes)."""
    user = update.effective_user
    msg = update.message
    if not user or not msg or user.id != ADMIN_ID:
        return False

    ap_state = context.user_data.get("admin_panel_state")
    if not isinstance(ap_state, dict):
        return False

    mode = ap_state.get("mode")
    step = ap_state.get("step")
    cancel_kb = InlineKeyboardMarkup(
        [
            [
                styled_inline_btn(
                    text="❌ Cancel", style="danger", callback_data="ap_home"
                )
            ]
        ]
    )

    if mode == "change_price" and step == "price":
        sid = str(ap_state.get("slot_id", ""))
        sub_id = str(ap_state.get("sub_id", ""))
        if not msg.text:
            await msg.reply_text(
                "❌ Please enter a valid numeric price per unit in INR (e.g., <code>25</code>):",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True
        cleaned = msg.text.strip().replace("₹", "").replace(",", "").strip()
        if not re.fullmatch(r"\d+(\.\d{1,2})?", cleaned):
            await msg.reply_text(
                "❌ <b>Invalid Price Format</b>\n\nPlease enter numbers only (e.g., <code>25</code> or <code>49.50</code>):",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True
        new_price = round(float(cleaned), 2)
        if not math.isfinite(new_price) or new_price <= 0:
            await msg.reply_text(
                "❌ Price must be greater than ₹0. Please enter a valid price:",
                reply_markup=cancel_kb,
            )
            return True

        async with _INVENTORY_LOCK:
            res = update_item_price_in_firebase(sid, sub_id, new_price)
        context.user_data.pop("admin_panel_state", None)

        if not res.get("ok"):
            await msg.reply_text(
                f"❌ {html.escape(str(res.get('reason', 'Failed to update price.')))}",
                reply_markup=build_admin_panel_keyboard(),
                parse_mode="HTML",
            )
            return True

        await msg.reply_text(
            "✅ <b>Price Per Unit Updated!</b>\n\n"
            f"• <b>Item:</b> <b>{html.escape(str(res['display_name']))}</b>\n"
            f"• <b>Previous Price:</b> ₹{float(res['old_price']):g}\n"
            f"• <b>New Price Per Unit:</b> <b>₹{float(res['new_price']):g}</b>",
            reply_markup=build_admin_panel_keyboard(),
            parse_mode="HTML",
        )
        return True

    if mode == "new_slot":
        if step == "name":
            if not msg.text or not msg.text.strip():
                await msg.reply_text(
                    "❌ Please enter a valid text name for the slot/folder:",
                    reply_markup=cancel_kb,
                )
                return True
            slot_name = msg.text.strip()[:100]
            ap_state["name"] = slot_name
            ap_state["step"] = "folder_choice"
            await msg.reply_text(
                f"✅ <b>Name Saved:</b> <b>{html.escape(slot_name)}</b>\n\n"
                "📁 <b>Do you want to make this a Folder-type slot?</b>\n"
                "• Choose <b>Yes</b> to create sub-items inside this folder.\n"
                "• Choose <b>No</b> to create a direct standalone coupon slot.",
                reply_markup=build_admin_folder_choice_keyboard(),
                parse_mode="HTML",
            )
            return True

        if step == "folder_choice":
            if msg.text and msg.text.strip().lower() in ("yes", "y", "no", "n"):
                is_fld = msg.text.strip().lower() in ("yes", "y")
                if is_fld:
                    ap_state["is_folder"] = True
                    ap_state["step"] = "sub_name"
                    await msg.reply_text(
                        f"📁 <b>Folder Selected:</b> <b>{html.escape(str(ap_state['name']))}</b>\n\n"
                        "Please enter the <b>Sub-Item Name</b> to create inside this folder:",
                        reply_markup=cancel_kb,
                        parse_mode="HTML",
                    )
                else:
                    ap_state["is_folder"] = False
                    ap_state["sub_name"] = ""
                    ap_state["step"] = "description"
                    await msg.reply_text(
                        f"🎟️ <b>Direct Slot:</b> <b>{html.escape(str(ap_state['name']))}</b>\n\n"
                        "📝 Please paste the <b>Description &amp; Terms</b> for this coupon:",
                        reply_markup=cancel_kb,
                        parse_mode="HTML",
                    )
                return True

            await msg.reply_text(
                "⚠️ Please select <b>✅ Yes (Create Folder)</b> or <b>❌ No (Direct Slot)</b> below (or type <code>Yes</code> / <code>No</code>):",
                reply_markup=build_admin_folder_choice_keyboard(),
                parse_mode="HTML",
            )
            return True

        if step == "sub_name":
            if not msg.text or not msg.text.strip():
                await msg.reply_text(
                    "❌ Please enter a valid sub-item name inside the folder:",
                    reply_markup=cancel_kb,
                )
                return True
            sub_name = msg.text.strip()[:100]
            ap_state["sub_name"] = sub_name
            ap_state["step"] = "description"
            await msg.reply_text(
                f"✅ <b>Sub-Item Name Saved:</b> <b>{html.escape(sub_name)}</b>\n\n"
                "📝 Please paste the <b>Description &amp; Terms</b> for this item:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        if step == "description":
            if not msg.text or not msg.text.strip():
                await msg.reply_text(
                    "❌ Please paste a valid text description:",
                    reply_markup=cancel_kb,
                )
                return True
            desc = msg.text.strip()[:1000]
            ap_state["description"] = desc
            ap_state["step"] = "price"
            await msg.reply_text(
                "✅ <b>Description Saved!</b>\n\n"
                "💰 <b>Enter Unit Price (₹):</b>\n"
                "Please enter the price for <b>1 unit / 1 coupon</b> (e.g., <code>25</code> or <code>49.50</code>):",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        if step == "price":
            if not msg.text:
                await msg.reply_text(
                    "❌ Please enter a numeric unit price in INR (e.g., <code>25</code>):",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True
            cleaned = msg.text.strip().replace("₹", "").replace(",", "").strip()
            if not re.fullmatch(r"\d+(\.\d{1,2})?", cleaned):
                await msg.reply_text(
                    "❌ <b>Invalid Price Format</b>\n\nPlease enter numbers only (e.g., <code>25</code> or <code>100</code>):",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True
            unit_price = round(float(cleaned), 2)
            if not math.isfinite(unit_price) or unit_price <= 0:
                await msg.reply_text(
                    "❌ Unit price must be greater than ₹0. Please enter a valid price:",
                    reply_markup=cancel_kb,
                )
                return True

            ap_state["price"] = unit_price
            ap_state["step"] = "codes"
            await msg.reply_text(
                f"✅ <b>Unit Price Saved:</b> <b>₹{unit_price:g}</b>\n\n"
                "🎟️ <b>Upload Coupons, Links, or JSON:</b>\n"
                "Send your items now:\n"
                "• Upload a <code>.txt</code> / <code>.json</code> file, <b>OR</b>\n"
                "• Paste them directly (single-line or multi-line JSON, codes, and URLs are accurately extracted and saved to Firebase).",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        if step == "codes":
            raw_content = ""
            source_filename = ""
            if msg.document:
                source_filename = (msg.document.file_name or "").strip()
                fname = source_filename.lower()
                if not fname.endswith((".txt", ".json")):
                    await msg.reply_text(
                        "❌ Please upload a valid <code>.txt</code> or <code>.json</code> file, or paste the items directly as text.",
                        reply_markup=cancel_kb,
                        parse_mode="HTML",
                    )
                    return True
                tg_file = await context.bot.get_file(msg.document.file_id)
                file_bytes = await tg_file.download_as_bytearray()
                raw_content = file_bytes.decode("utf-8", errors="ignore")
            elif msg.text:
                raw_content = msg.text
            else:
                await msg.reply_text(
                    "❌ Please send a <code>.txt</code> / <code>.json</code> file or paste your items directly.",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            parsed_items = parse_coupons_or_links(raw_content)
            if not parsed_items:
                await msg.reply_text(
                    "❌ No valid coupons, links, or JSON found in your input. Please send non-empty lines or a valid file:",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True

            async with _INVENTORY_LOCK:
                res = create_slot_or_folder_item(
                    main_name=str(ap_state["name"]),
                    is_folder=bool(ap_state.get("is_folder", False)),
                    sub_name=str(ap_state.get("sub_name", "")),
                    description=str(ap_state["description"]),
                    unit_price=float(ap_state["price"]),
                    codes=parsed_items,
                    source_filename=source_filename,
                )
            context.user_data.pop("admin_panel_state", None)

            folder_line = (
                f"• <b>Folder:</b> 📁 <b>{html.escape(res['folder_name'])}</b>\n"
                if res["is_folder"]
                else ""
            )
            await msg.reply_text(
                "✅ <b>Slot Created &amp; Saved to Firebase!</b>\n\n"
                f"{folder_line}"
                f"• <b>Item Name:</b> <b>{html.escape(res['item_name'])}</b>\n"
                f"• <b>Unit Price:</b> <b>₹{res['price']:g}</b>\n"
                f"• <b>Coupons / Links / JSON Added:</b> <b>{res['added_count']}</b>\n"
                f"• <b>Duplicates Skipped:</b> {res['duplicate_count']}\n"
                f"• <b>Current Live Stock:</b> <b>{res['total_stock']}</b>",
                reply_markup=build_admin_post_add_keyboard(),
                parse_mode="HTML",
            )
            return True

    if mode == "direct_add" and step == "codes":
        sid = str(ap_state.get("slot_id", ""))
        sub_id = str(ap_state.get("sub_id", ""))
        raw_content = ""
        source_filename = ""
        if msg.document:
            source_filename = (msg.document.file_name or "").strip()
            fname = source_filename.lower()
            if not fname.endswith((".txt", ".json")):
                await msg.reply_text(
                    "❌ Please upload a valid <code>.txt</code> or <code>.json</code> file, or paste the items directly as text.",
                    reply_markup=cancel_kb,
                    parse_mode="HTML",
                )
                return True
            tg_file = await context.bot.get_file(msg.document.file_id)
            file_bytes = await tg_file.download_as_bytearray()
            raw_content = file_bytes.decode("utf-8", errors="ignore")
        elif msg.text:
            raw_content = msg.text
        else:
            await msg.reply_text(
                "❌ Please send a <code>.txt</code> / <code>.json</code> file or paste your items directly.",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        parsed_items = parse_coupons_or_links(raw_content)
        if not parsed_items:
            await msg.reply_text(
                "❌ No valid coupons, links, or JSON found in your input. Please send non-empty lines or a valid file:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        async with _INVENTORY_LOCK:
            res = direct_add_to_target(
                slot_id=sid,
                sub_id=sub_id,
                codes=parsed_items,
                source_filename=source_filename,
            )
        context.user_data.pop("admin_panel_state", None)

        if not res.get("ok"):
            await msg.reply_text(
                f"❌ {html.escape(str(res.get('reason', 'Failed to update slot.')))}",
                reply_markup=build_admin_panel_keyboard(),
                parse_mode="HTML",
            )
            return True

        await msg.reply_text(
            "✅ <b>Coupons / Links / JSON Added to Live Firebase Stock!</b>\n\n"
            f"• <b>Item:</b> <b>{html.escape(res['display_name'])}</b>\n"
            f"• <b>Unit Price:</b> ₹{res['price']:g}\n"
            f"• <b>Newly Added:</b> <b>{res['added_count']}</b>\n"
            f"• <b>Duplicates Skipped:</b> {res['duplicate_count']}\n"
            f"• <b>Updated Live Stock:</b> <b>{res['total_stock']}</b>",
            reply_markup=build_admin_post_add_keyboard(),
            parse_mode="HTML",
        )
        return True

    if mode == "download_codes" and step == "qty":
        sid = str(ap_state.get("slot_id", ""))
        sub_id = str(ap_state.get("sub_id", ""))
        if not msg.text or not msg.text.strip():
            await msg.reply_text(
                "❌ Please enter a valid quantity number or type <code>ALL</code>:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        raw_q = msg.text.strip().upper()
        req_qty: int | None
        if raw_q == "ALL":
            req_qty = None
        elif re.fullmatch(r"\d+", raw_q) and int(raw_q) >= 1:
            req_qty = int(raw_q)
        else:
            await msg.reply_text(
                "❌ Invalid input. Please enter a positive whole number or type <code>ALL</code>:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        async with _INVENTORY_LOCK:
            res = withdraw_codes_for_admin(sid, sub_id, requested_qty=req_qty)

        if not res.get("ok"):
            await msg.reply_text(
                f"❌ {html.escape(str(res.get('reason', 'Unable to withdraw codes.')))}\n\n"
                "Please enter a valid quantity or type <code>ALL</code>:",
                reply_markup=cancel_kb,
                parse_mode="HTML",
            )
            return True

        context.user_data.pop("admin_panel_state", None)
        await send_withdrawn_codes_file(update, context, res, from_callback=False)
        return True

    return False


async def handle_free_text_and_docs(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    msg = update.message
    if not user or not msg:
        return

    # 1. /admin active wizard (Broadcast, Check Order ID, Create Coupon, Refund User)
    if user.id == ADMIN_ID and await handle_admin_cmd_inputs(update, context):
        return

    # 2. /adminpanel active wizard (New Slot / Folder, Direct Add, Download Codes & Change Price)
    if user.id == ADMIN_ID and await handle_admin_panel_inputs(update, context):
        return

    # 3. Admin cURL text or .txt upload
    if user.id == ADMIN_ID:
        if msg.document:
            fname = (msg.document.file_name or "").lower()
            if fname.endswith(".txt"):
                tg_file = await context.bot.get_file(msg.document.file_id)
                file_bytes = await tg_file.download_as_bytearray()
                content = file_bytes.decode("utf-8", errors="ignore")
                if context.user_data.get("awaiting_curl_upload") or (
                    "bharatpe.in" in content.lower() or "token:" in content.lower()
                ):
                    await apply_admin_curl_update(update, context, content)
                    return
            elif context.user_data.get("awaiting_curl_upload"):
                await msg.reply_text(
                    "❌ <b>Invalid File Type</b>\n\nPlease upload a <code>.txt</code> file containing your cURL command, or paste the cURL text directly.",
                    parse_mode="HTML",
                )
                return
        elif msg.text and (
            context.user_data.get("awaiting_curl_upload")
            or ("bharatpe.in" in msg.text.lower() and "token:" in msg.text.lower())
        ):
            await apply_admin_curl_update(update, context, msg.text)
            return

    if await guard_maintenance_mode(update, context):
        return

    # 4. Enforce force-join on all regular user interactions
    allowed = await enforce_force_join(update, context)
    if not allowed:
        return

    # 4.5 Context-aware Bot Promo Coupon Claim Input
    if context.user_data.get("awaiting_promo_coupon"):
        cancel_wallet_kb = InlineKeyboardMarkup(
            [
                [
                    styled_inline_btn(
                        text="🔙 Back to Wallet",
                        style="danger",
                        callback_data="open_wallet",
                    )
                ]
            ]
        )
        if not msg.text or not msg.text.strip():
            await msg.reply_text(
                "❌ Please type a valid <b>Coupon Code</b> to claim:",
                reply_markup=cancel_wallet_kb,
                parse_mode="HTML",
            )
            return

        raw_code = msg.text.strip()
        if contains_url(raw_code):
            await msg.reply_text(
                "❌ Links are not valid coupon codes. Please enter your <b>Coupon Code</b>:",
                reply_markup=cancel_wallet_kb,
                parse_mode="HTML",
            )
            return

        async with get_user_lock(user.id), _PROMO_LOCK:
            claim_res = redeem_bot_promo_coupon(user.id, raw_code)

        if not claim_res.get("ok"):
            await msg.reply_text(
                f"❌ <b>Coupon Claim Failed</b>\n\n"
                f"{html.escape(str(claim_res.get('reason', 'Invalid coupon code.')))}\n\n"
                "Please enter a valid coupon code or tap <b>🔙 Back to Wallet</b>:",
                reply_markup=cancel_wallet_kb,
                parse_mode="HTML",
            )
            return

        context.user_data.pop("awaiting_promo_coupon", None)
        await msg.reply_text(
            "🎉 <b>Coupon Claimed Successfully!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Coupon Code:</b> <code>{html.escape(claim_res['code'])}</code>\n"
            f"• <b>Amount Added:</b> <b>₹{claim_res['amount']:.2f}</b>\n\n"
            "<b>Updated Wallet Summary</b>\n"
            f"• <b>Available Balance:</b> <b>₹{claim_res['new_available_balance']:.2f}</b>\n"
            f"• <b>Referral Balance:</b> <b>₹{claim_res['referral_balance']:.2f}</b>\n"
            f"• <b>Total Balance:</b> <b>₹{claim_res['total_balance']:.2f}</b>",
            reply_markup=build_wallet_keyboard(),
            parse_mode="HTML",
        )
        return

    # 5. Context-aware Custom Coupon Quantity Input
    qty_target = context.user_data.get("awaiting_custom_qty_target")
    if isinstance(qty_target, dict):
        sid = str(qty_target.get("slot_id", ""))
        sub_id = str(qty_target.get("sub_id", ""))
        item = fetch_sellable_item(sid, sub_id)
        if not item or int(item["stock"]) <= 0:
            context.user_data.pop("awaiting_custom_qty_target", None)
            await msg.reply_text(
                "⚠️ This coupon is now out of stock. Please choose another item from <b>🛒 Buy Coupon</b>.",
                parse_mode="HTML",
            )
            return

        if not msg.text:
            await msg.reply_text(
                f"❌ <b>Invalid Format</b>\n\nPlease enter a whole number between <b>1</b> and <b>{int(item['stock'])}</b>:",
                parse_mode="HTML",
            )
            return

        raw_qty = msg.text.strip()
        if contains_url(raw_qty) or not re.fullmatch(r"\d+", raw_qty):
            await msg.reply_text(
                f"❌ <b>Invalid Quantity Format</b>\n\n"
                f"You entered: <code>{html.escape(raw_qty[:30])}</code>\n"
                f"Please enter a whole number only between <b>1</b> and <b>{int(item['stock'])}</b>:",
                parse_mode="HTML",
            )
            return

        qty = int(raw_qty)
        max_stock = int(item["stock"])
        if qty < 1 or qty > max_stock:
            await msg.reply_text(
                f"❌ <b>Quantity Out of Range</b>\n\nPlease enter a quantity between <b>1</b> and <b>{max_stock}</b>:",
                parse_mode="HTML",
            )
            return

        await show_order_summary(
            update, context, slot_id=sid, sub_id=sub_id, quantity=qty, from_callback=False
        )
        return

    # 6. Context-aware Custom Wallet Top-Up Amount Input
    if context.user_data.get("awaiting_custom_amount"):
        if not msg.text:
            await msg.reply_text(
                f"❌ <b>Invalid Input Format</b>\n\nPlease type a numeric amount in INR (Minimum <b>₹{MIN_WALLET_TOPUP:g}</b>, e.g., <code>25</code>).",
                parse_mode="HTML",
            )
            return

        raw_text = msg.text.strip()
        if contains_url(raw_text):
            await msg.reply_text(
                f"❌ <b>URLs Are Not Allowed</b>\n\nPlease enter a valid numeric top-up amount in INR (Minimum <b>₹{MIN_WALLET_TOPUP:g}</b>, e.g., <code>50</code>).",
                parse_mode="HTML",
            )
            return

        cleaned_amt = raw_text.replace("₹", "").replace(",", "").strip()
        if not re.fullmatch(r"\d+(\.\d{1,2})?", cleaned_amt):
            await msg.reply_text(
                f"❌ <b>Invalid Amount Format</b>\n\n"
                f"You entered: <code>{html.escape(raw_text[:30])}</code>\n"
                f"Please enter numbers only (e.g., <code>15</code>, <code>50</code>, or <code>125.50</code> — minimum <b>₹{MIN_WALLET_TOPUP:g}</b>):",
                parse_mode="HTML",
            )
            return

        amount = round(float(cleaned_amt), 2)
        if not math.isfinite(amount) or amount < MIN_WALLET_TOPUP or amount > MAX_WALLET_TOPUP:
            await msg.reply_text(
                f"❌ <b>Amount Out of Range</b>\n\nPlease enter an amount between <b>₹{MIN_WALLET_TOPUP:g}</b> and <b>₹{MAX_WALLET_TOPUP:g}</b>:",
                parse_mode="HTML",
            )
            return

        await start_upi_payment_session(
            update=update, context=context, amount=amount, purpose="wallet"
        )
        return

    # 7. Context-aware 12-Digit UTR Submission Input
    pending_txid = context.user_data.get("awaiting_utr_txid")
    if pending_txid:
        if not msg.text:
            await msg.reply_text(
                f"❌ <b>Text Input Required</b>\n\nPlease type your <b>12-digit numeric UTR number</b> (e.g., <code>432910482910</code>) for TXID <code>{html.escape(str(pending_txid))}</code>:",
                parse_mode="HTML",
            )
            return
        await run_utr_verification_flow(
            chat_id=msg.chat_id,
            user_id=user.id,
            txid=str(pending_txid),
            raw_input=msg.text,
            context=context,
            increment_attempt=True,
        )
        return

    # 8. Stray text / duplicate URL guard outside active prompts
    if msg.text and contains_url(msg.text):
        await msg.reply_text(
            "⛔ External links and duplicate URLs are not accepted here. Please use the menu buttons below.",
            reply_markup=build_main_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    await msg.reply_text(
        "ℹ️ Please select an option from the menu below to continue.",
        reply_markup=build_main_menu_keyboard(),
        parse_mode="HTML",
    )


async def run_bot() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Please set BOT_TOKEN in environment variables or code.")

    init_firebase()
    load_bharatpe_config()
    app = Application.builder().token(BOT_TOKEN).build()

    menu_texts = [
        BTN_STOCK,
        BTN_BUY,
        BTN_PROFILE,
        BTN_ORDERS,
        BTN_LEADERBOARD,
        BTN_REFER,
        BTN_SUPPORT,
        BTN_WALLET,
        BTN_MAIN_CHANNELS,
    ]
    escaped_menu = "|".join(
        s.replace("(", "\\(").replace(")", "\\)") for s in menu_texts
    )
    menu_filter = filters.TEXT & filters.Regex(f"^({escaped_menu})$")
    private_only = filters.ChatType.PRIVATE

    await app.bot.set_my_commands(
        [
            BotCommand("start", "Start the bot"),
            BotCommand("curl", "Update BharatPe cURL / session token (Admin)"),
            BotCommand("admin", "Broadcast, User List, Order Check, Coupon & Refund (Admin)"),
            BotCommand("adminpanel", "Manage coupon slots, folders & stock (Admin)"),
        ]
    )

    app.add_handler(CommandHandler("start", start_command, filters=private_only))
    app.add_handler(CommandHandler("curl", curl_command, filters=private_only))
    app.add_handler(CommandHandler("admin", admin_command, filters=private_only))
    app.add_handler(CommandHandler("adminpanel", adminpanel_command, filters=private_only))
    app.add_handler(MessageHandler(private_only & filters.COMMAND, unknown_command_handler))

    app.add_handler(
        CallbackQueryHandler(verify_callback, pattern=r"^verify_joins$")
    )
    app.add_handler(MessageHandler(private_only & menu_filter, handle_menu_text))
    app.add_handler(
        CallbackQueryHandler(
            handle_inline_callbacks,
            pattern=(
                r"^(adm_menu|adm_broadcast|adm_users:\d+|adm_check_order|"
                r"adm_maintenance|adm_maint_toggle|adm_create_coupon|"
                r"adm_refund_user|adm_rfd_yes|"
                r"ap_home|ap_new_slot|ap_folder_yes|ap_folder_no|ap_direct_add|ap_check_qty|"
                r"ap_change_price|ap_prc_fld:[a-zA-Z0-9_]+|ap_prc_itm:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"ap_del_slots|ap_del_fld:[a-zA-Z0-9_]+|ap_del_ask:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"ap_del_yes:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"ap_dir_fld:[a-zA-Z0-9_]+|ap_dir_itm:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"ap_dl_codes|ap_dl_fld:[a-zA-Z0-9_]+|ap_dl_itm:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"ap_dl_all:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"stock_refresh|open_buy_menu|buy_folder:[a-zA-Z0-9_]+|"
                r"buy_itm:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|buy_qty:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*:\d+|"
                r"buy_cqty:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*|"
                r"chk_upi:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*:\d+|"
                r"chk_wlt:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*:\d+|"
                r"chk_cnl:[a-zA-Z0-9_]+:[a-zA-Z0-9_]*:\d+|"
                r"open_refer|open_wallet|wallet_claim_coupon|back_to_home|"
                r"orders_page:\d+|wallet_amt:\d+(\.\d+)?|wallet_custom|"
                r"pay_paid:[A-Z0-9]+|pay_cancel:[A-Z0-9]+|"
                r"utr_recheck:[A-Z0-9]+|utr_resubmit:[A-Z0-9]+)$"
            ),
        )
    )

    app.add_handler(
        MessageHandler(
            private_only & ~filters.COMMAND & ~menu_filter,
            handle_free_text_and_docs,
        )
    )

    if app.job_queue:
        app.job_queue.run_repeating(token_health_check, interval=10800, first=15)
        restore_pending_expiry_jobs(app.job_queue)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram bot polling started...")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
