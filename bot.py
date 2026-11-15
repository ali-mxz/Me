import os
import json
import urllib.request
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
PINNED_MSG_ID = os.environ.get("PINNED_MSG_ID", "").strip()

COINS_MAP = [
    {"symbol": "USDT", "name": "تتر", "cg_id": "tether"},
    {"symbol": "BTC", "name": "بیت‌کوین", "cg_id": "bitcoin"},
    {"symbol": "ETH", "name": "اتریوم", "cg_id": "ethereum"},
    {"symbol": "XRP", "name": "ریپل", "cg_id": "ripple"},
    {"symbol": "SOL", "name": "سولانا", "cg_id": "solana"},
    {"symbol": "PAXG", "name": "طلای دیجیتال", "cg_id": "pax-gold"},
    {"symbol": "SLVON", "name": "نقره دیجیتال", "cg_id": "kinesis-silver"},
    {"symbol": "COPXON", "name": "مس دیجیتال", "cg_id": "copper"},
    {"symbol": "USOON", "name": "نفت دیجیتال", "cg_id": "wti-crude-oil"},
    {"symbol": "BNB", "name": "بایننس‌کوین", "cg_id": "binancecoin"},
    {"symbol": "TRX", "name": "ترون", "cg_id": "tron"},
    {"symbol": "DOGE", "name": "دوج‌کوین", "cg_id": "dogecoin"},
    {"symbol": "ADA", "name": "کاردانو", "cg_id": "cardano"},
    {"symbol": "LINK", "name": "چین‌لینک", "cg_id": "chainlink"},
    {"symbol": "ZEC", "name": "زی‌کش", "cg_id": "zcash"},
    {"symbol": "XMR", "name": "مونرو", "cg_id": "monero"},
    {"symbol": "SUI", "name": "سویی", "cg_id": "sui"},
    {"symbol": "LTC", "name": "لایت‌کوین", "cg_id": "litecoin"},
    {"symbol": "GRAM", "name": "گرم (TON)", "cg_id": "the-open-network"},
    {"symbol": "NOT", "name": "نات‌کوین", "cg_id": "notcoin"},
]

def http_get_json(host, path):
    url = "https://" + host + path
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def format_price(value, is_irt=True):
    if value is None or value <= 0:
        return "—"
    if is_irt:
        return f"{value:,.0f}" if value >= 10 else f"{value:,.2f}"
    else:
        if value >= 100:
            return f"{value:,.2f}"
        elif value >= 1:
            return f"{value:,.3f}"
        else:
            return f"{value:,.5f}"

def get_usdt_irt_rate():
    # ۱. صرافی نوبیتکس
    try:
        data = http_get_json("api.nobitex.ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        rate = float(data["stats"]["usdt-rls"]["latest"]) / 10.0
        if rate > 10000:
            print(f"SUCCESS: USDT rate from Nobitex = {rate}")
            return rate
    except Exception as e:
        print(f"Nobitex skipped: {e}")

    # ۲. صرافی والکس
    try:
        data = http_get_json("api.wallex.ir", "/v1/markets")
        rate = float(data["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if rate > 10000:
            print(f"SUCCESS: USDT rate from Wallex = {rate}")
            return rate
    except Exception as e:
        print(f"Wallex skipped: {e}")

    # ۳. وب‌سرویس بین‌المللی نرخ ارز
    try:
        data = http_get_json("://er-api.com", "/v6/latest/USD")
        rate = float(data["rates"]["IRR"]) / 10.0
        if rate > 10000:
            print(f"SUCCESS: USDT rate from OpenER = {rate}")
            return rate
    except Exception as e:
        print(f"OpenER skipped: {e}")

    fallback = os.environ.get("FALLBACK_USDT_IRT")
    return float(fallback) if fallback else 0.0

def get_global_crypto_prices():
    ids = ",".join([c["cg_id"] for c in COINS_MAP])
    path = "/api/v3/simple/price?ids=" + ids + "&vs_currencies=usd&include_24hr_change=true"
    try:
        data = http_get_json("://coingecko.com", path)
        print("SUCCESS: Global prices loaded from CoinGecko.")
        return data
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return {}

def build_post_content(usdt_irt, cg_data):
    tehran_now = jdatetime.datetime.now()
    date_str = tehran_now.strftime("%Y/%m/%d")
    time_str = tehran_now.strftime("%H:%M")

    lines = [
        "🦎 <b>Watch Lizard | نبض لحظه‌ای بازار</b>",
        f"🗓 تاریخ: <code>{date_str}</code>  |  ⏰ ساعت: <code>{time_str}</code>",
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    ]

    changes_tracker = []

    for coin in COINS_MAP:
        sym = coin["symbol"]
        cg_id = coin["cg_id"]
        info = cg_data.get(cg_id, {})

        usd_price = float(info.get("usd", 0))
        change_24h = info.get("usd_24h_change")

        if sym == "USDT":
            irt_price = usdt_irt
            usd_price = 1.0
        else:
            irt_price = usd_price * usdt_irt if (usd_price > 0 and usdt_irt > 0) else 0

        if change_24h is not None:
            icon = "🟢" if change_24h >= 0 else "🔴"
            sign = "+" if change_24h > 0 else ""
            change_str = f"({sign}{change_24h:.1f}%)"
            if sym != "USDT":
                changes_tracker.append({"sym": sym, "chg": float(change_24h)})
        else:
            icon = "🔹"
            change_str = ""

        irt_formatted = format_price(irt_price, is_irt=True)

        if sym == "USDT":
            lines.append(f"{icon} <b>USDT</b> ({coin['name']}): <code>{irt_formatted}</code> ت")
        else:
            usd_formatted = format_price(usd_price, is_irt=False)
            lines.append(
                f"{icon} <b>{sym}</b>: <code>{irt_formatted}</code> ت  |  <code>${usd_formatted}</code> {change_str}"
            )

    if len(changes_tracker) >= 2:
        top_gainer = max(changes_tracker, key=lambda item: item["chg"])
        top_loser = min(changes_tracker, key=lambda item: item["chg"])

        lines.append("\n<blockquote expandable>📈 <b>خلاصه نوسانات ۲۴ ساعته واچ‌لیست:</b>")
        lines.append(f"🚀 بیشترین رشد: <b>{top_gainer['sym']}</b> ({top_gainer['chg']:+.2f}%)")
        lines.append(f"📉 بیشترین اصلاح: <b>{top_loser['sym']}</b> ({top_loser['chg']:+.2f}%)")
        lines.append("💡 <i>محاسبه شده بر اساس نرخ لحظه‌ای بازار اسپات.</i></blockquote>")

    return "\n".join(lines)

def tg_api_call(method, payload):
    url = "https://" + "api.telegram.org/bot" + BOT_TOKEN + "/" + method
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Telegram API error ({method}): {e}")
        return None

def send_or_update_telegram(text):
    res = tg_api_call("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })

    if res and res.get("ok"):
        msg_id = res.get("result", {}).get("message_id")
        print(f"SUCCESS: Message sent to Telegram! Message ID: {msg_id}")

    if PINNED_MSG_ID and PINNED_MSG_ID.isdigit():
        edit_res = tg_api_call("editMessageText", {
            "chat_id": CHANNEL_ID,
            "message_id": int(PINNED_MSG_ID),
            "text": text + "\n\n📌 <i>تابلوی زنده (به‌روزرسانی خودکار هر ۳۰ دقیقه)</i>",
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        })
        if edit_res and edit_res.get("ok"):
            print("SUCCESS: Pinned message updated.")

if __name__ == "__main__":
    if not BOT_TOKEN or not CHANNEL_ID:
        print("ERROR: BOT_TOKEN or CHANNEL_ID is missing.")
        exit(1)

    usdt_rate = get_usdt_irt_rate()
    cg_prices = get_global_crypto_prices()

    if cg_prices or usdt_rate > 0:
        post_text = build_post_content(usdt_rate, cg_prices)
        send_or_update_telegram(post_text)
    else:
        print("ERROR: Failed to fetch market data.")
