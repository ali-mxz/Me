import os
import requests
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
PINNED_MSG_ID = os.environ.get("PINNED_MSG_ID")

# واچ‌لیست ۲۰ تایی با شناسه‌های دقیق CoinGecko
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

def format_price(value: float, is_irt: bool = True) -> str:
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

def get_usdt_irt_rate() -> float:
    """دریافت نرخ لحظه‌ای تتر به تومان با زنجیره پشتیبان ۵ لایه"""
    headers = {"User-Agent": "Mozilla/5.0"}

    # لایه ۱: صرافی نوبیتکس (ریال تقسیم بر ۱۰)
    try:
        res = requests.get("https://nobitex.ir", headers=headers, timeout=8).json()
        rate = float(res["stats"]["usdt-rls"]["latest"]) / 10.0
        if rate > 10000:
            print(f"USDT rate loaded from Nobitex: {rate}")
            return rate
    except Exception:
        pass

    # لایه ۲: صرافی والکس (تومان)
    try:
        res = requests.get("https://wallex.ir", headers=headers, timeout=8).json()
        rate = float(res["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if rate > 10000:
            print(f"USDT rate loaded from Wallex: {rate}")
            return rate
    except Exception:
        pass

    # لایه ۳: صرافی تترلند (تومان)
    try:
        res = requests.get("https://tetherland.com", headers=headers, timeout=8).json()
        rate = float(res["data"]["currencies"]["USDT"]["price"])
        if rate > 10000:
            print(f"USDT rate loaded from Tetherland: {rate}")
            return rate
    except Exception:
        pass

    # لایه ۴: منبع بین‌المللی نرخ ارز (بدون محدودیت جغرافیایی - ریال تقسیم بر ۱۰)
    try:
        res = requests.get("https://er-api.com", headers=headers, timeout=8).json()
        rate = float(res["rates"]["IRR"]) / 10.0
        if rate > 10000:
            print(f"USDT rate loaded from OpenER: {rate}")
            return rate
    except Exception:
        pass

    # لایه ۵: نرخ اضطراری ثبت شده در گیت‌هاب
    fallback = os.environ.get("FALLBACK_USDT_IRT")
    return float(fallback) if fallback else 0.0

def get_global_crypto_prices() -> dict:
    """دریافت قیمت دلاری و درصد تغییر ۲۴ ساعته از CoinGecko"""
    ids = ",".join([c["cg_id"] for c in COINS_MAP])
    url = f"https://coingecko.com{ids}&vs_currencies=usd&include_24hr_change=true"
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if res.status_code == 200:
            print("Global prices loaded from CoinGecko.")
            return res.json()
        else:
            print(f"CoinGecko status code: {res.status_code}")
    except Exception as e:
        print(f"CoinGecko error: {e}")
    return {}

def build_post_content(usdt_irt: float, cg_data: dict) -> str:
    tehran_now = jdatetime.datetime.now()
    date_str = tehran_now.strftime("%Y/%m/%d")
    time_str = tehran_now.strftime("%H:%M")

    lines = [
        f"📊 <b>نبض لحظه‌ای بازار کریپتو و کالا</b>",
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
                changes_tracker.append((sym, change_24h))
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

    if changes_tracker:
        changes_tracker.sort(key=lambda x: x[1], reverse=True)
        top_gainer = changes_tracker[0]
        top_loser = changes_tracker[-1]

        lines.append("\n<blockquote expandable>📈 <b>خلاصه نوسانات ۲۴ ساعته واچ‌لیست:</b>")
        lines.append(f"🚀 بیشترین رشد: <b>{top_gainer[0]}</b> ({top_gainer[1]:+.2f}%)")
        lines.append(f"📉 بیشترین اصلاح: <b>{top_loser[0]}</b> ({top_loser[1]:+.2f}%)")
        lines.append("💡 <i>محاسبه شده بر اساس نرخ لحظه‌ای بازار اسپات.</i></blockquote>")

    return "\n".join(lines)

def send_or_update_telegram(text: str):
    base_url = f"https://telegram.org{BOT_TOKEN}"

    res = requests.post(f"{base_url}/sendMessage", json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }, timeout=15)

    if res.status_code == 200:
        msg_id = res.json().get("result", {}).get("message_id")
        print(f"SUCCESS: Message sent to Telegram! Message ID: {msg_id}")
    else:
        print(f"ERROR sending message to Telegram: {res.text}")

    if PINNED_MSG_ID and PINNED_MSG_ID.strip().isdigit():
        edit_res = requests.post(f"{base_url}/editMessageText", json={
            "chat_id": CHANNEL_ID,
            "message_id": int(PINNED_MSG_ID.strip()),
            "text": text + "\n\n📌 <i>تابلوی زنده (به‌روزرسانی خودکار هر ۳۰ دقیقه)</i>",
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=15)
        if edit_res.status_code == 200:
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
