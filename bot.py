import os
import requests
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
PINNED_MSG_ID = os.environ.get("PINNED_MSG_ID")

WATCHLIST = [
    {"symbol": "USDT", "name": "تتر"},
    {"symbol": "BTC", "name": "بیت‌کوین"},
    {"symbol": "ETH", "name": "اتریوم"},
    {"symbol": "XRP", "name": "ریپل"},
    {"symbol": "SOL", "name": "سولانا"},
    {"symbol": "PAXG", "name": "طلای دیجیتال"},
    {"symbol": "SLVON", "name": "نقره دیجیتال"},
    {"symbol": "COPXON", "name": "مس دیجیتال"},
    {"symbol": "USOON", "name": "نفت دیجیتال"},
    {"symbol": "BNB", "name": "بایننس‌کوین"},
    {"symbol": "TRX", "name": "ترون"},
    {"symbol": "DOGE", "name": "دوج‌کوین"},
    {"symbol": "ADA", "name": "کاردانو"},
    {"symbol": "LINK", "name": "چین‌لینک"},
    {"symbol": "ZEC", "name": "زی‌کش"},
    {"symbol": "XMR", "name": "مونرو"},
    {"symbol": "SUI", "name": "سویی"},
    {"symbol": "LTC", "name": "لایت‌کوین"},
    {"symbol": "GRAM", "name": "گرم (TON)", "fallback": "TON"},
    {"symbol": "NOT", "name": "نات‌کوین"},
]

def format_price(value: float, is_irt: bool = True) -> str:
    if value is None or value == 0:
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

def fetch_bitpin_data():
    # لیست آدرس‌های رسمی و جایگزین API بیت‌پین
    endpoints = [
        "https://api.bitpin.org/v1/mkt/tickers/",
        "https://api.bitpin.org/v1/mkt/markets/",
        "https://bitpin.ir",
        "https://bitpin.ir"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    for url in endpoints:
        try:
            print(f"Trying {url} ...")
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                items = data if isinstance(data, list) else data.get("results", [])
                if items:
                    market_map = {}
                    for item in items:
                        code = item.get("symbol") or item.get("code")
                        if code:
                            market_map[code.upper()] = item
                    print(f"SUCCESS: Connected to {url} ({len(market_map)} markets loaded)")
                    return market_map
            else:
                print(f"Status {res.status_code} from {url}")
        except Exception as e:
            print(f"Failed {url}: {e}")
            
    return {}

def build_post_content(markets: dict) -> str:
    tehran_now = jdatetime.datetime.now()
    date_str = tehran_now.strftime("%Y/%m/%d")
    time_str = tehran_now.strftime("%H:%M")

    lines = [
        f"📊 <b>نبض لحظه‌ای بازار کریپتو و کالا (بیت‌پین)</b>",
        f"🗓 تاریخ: <code>{date_str}</code>  |  ⏰ ساعت: <code>{time_str}</code>",
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    ]

    changes_tracker = []

    for coin in WATCHLIST:
        sym = coin["symbol"]
        fb = coin.get("fallback")
        
        irt_data = markets.get(f"{sym}_IRT") or (markets.get(f"{fb}_IRT") if fb else None)
        usdt_data = markets.get(f"{sym}_USDT") or (markets.get(f"{fb}_USDT") if fb else None)

        irt_price = float(irt_data.get("price") or irt_data.get("last_price") or 0) if irt_data else 0
        usdt_price = float(usdt_data.get("price") or usdt_data.get("last_price") or 0) if usdt_data else 0
        
        change_raw = None
        if usdt_data and usdt_data.get("daily_change_price") is not None:
            change_raw = float(usdt_data["daily_change_price"])
        elif irt_data and irt_data.get("daily_change_price") is not None:
            change_raw = float(irt_data["daily_change_price"])
        elif usdt_data and usdt_data.get("change_24h") is not None:
            change_raw = float(usdt_data["change_24h"])

        if change_raw is not None:
            icon = "🟢" if change_raw >= 0 else "🔴"
            sign = "+" if change_raw > 0 else ""
            change_str = f"({sign}{change_raw:.1f}%)"
            if sym != "USDT":
                changes_tracker.append((sym, change_raw))
        else:
            icon = "🔹"
            change_str = ""

        irt_formatted = format_price(irt_price, is_irt=True)
        
        if sym == "USDT":
            lines.append(f"{icon} <b>USDT</b> ({coin['name']}): <code>{irt_formatted}</code> ت {change_str}")
        else:
            usdt_formatted = format_price(usdt_price, is_irt=False)
            lines.append(
                f"{icon} <b>{sym}</b>: <code>{irt_formatted}</code> ت  |  <code>${usdt_formatted}</code> {change_str}"
            )

    if changes_tracker:
        changes_tracker.sort(key=lambda x: x, reverse=True)
        top_gainer = changes_tracker[0]
        top_loser = changes_tracker[-1]
        
        lines.append("\n<blockquote expandable>📈 <b>خلاصه نوسانات ۲۴ ساعته واچ‌لیست:</b>")
        lines.append(f"🚀 بیشترین رشد: <b>{top_gainer[0]}</b> ({top_gainer[1]:+.2f}%)")
        lines.append(f"📉 بیشترین اصلاح: <b>{top_loser[0]}</b> ({top_loser[1]:+.2f}%)")
        lines.append("💡 <i>قیمت‌ها مستقیماً از بازار اسپات بیت‌پین استعلام شده‌اند.</i></blockquote>")

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
        
    markets_data = fetch_bitpin_data()
    if markets_data:
        post_text = build_post_content(markets_data)
        send_or_update_telegram(post_text)
    else:
        print("ERROR: No data received from any Bitpin endpoint.")
