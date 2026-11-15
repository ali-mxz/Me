import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
PINNED_MSG_ID = os.environ.get("PINNED_MSG_ID", "").strip()

WATCHLIST = [
    {"symbol": "USDT", "type": "usdt"},
    {"symbol": "BTC", "type": "crypto", "lookup": "BTC"},
    {"symbol": "ETH", "type": "crypto", "lookup": "ETH"},
    {"symbol": "XRP", "type": "crypto", "lookup": "XRP"},
    {"symbol": "SOL", "type": "crypto", "lookup": "SOL"},
    {"symbol": "PAXG", "type": "crypto", "lookup": "PAXG"},
    {"symbol": "SLVON", "type": "commodity"},
    {"symbol": "COPXON", "type": "commodity"},
    {"symbol": "USOON", "type": "commodity"},
    {"symbol": "GRAM", "type": "crypto", "lookup": "TON"},
    {"symbol": "DOGE", "type": "crypto", "lookup": "DOGE"},
    {"symbol": "LINK", "type": "crypto", "lookup": "LINK"},
    {"symbol": "XMR", "type": "crypto", "lookup": "XMR"},
    {"symbol": "BNB", "type": "crypto", "lookup": "BNB"},
    {"symbol": "TRX", "type": "crypto", "lookup": "TRX"},
    {"symbol": "ADA", "type": "crypto", "lookup": "ADA"},
    {"symbol": "ZEC", "type": "crypto", "lookup": "ZEC"},
    {"symbol": "SUI", "type": "crypto", "lookup": "SUI"},
    {"symbol": "LTC", "type": "crypto", "lookup": "LTC"},
    {"symbol": "NOT", "type": "crypto", "lookup": "NOT"},
]

def to_arabic_digits(text):
    mapping = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    return text.translate(mapping)

def http_get_json(host, path):
    scheme = "https" + "://"
    url = scheme + host + path
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def format_usd(value):
    if value is None or value <= 0:
        return "—"
    if value >= 1000:
        return f"${value:,.0f}"
    elif value >= 10:
        return f"${value:,.2f}"
    elif value >= 1:
        return f"${value:,.3f}"
    else:
        return f"${value:,.5f}"

def format_irt(value):
    if value is None or value <= 0:
        return "—"
    return f"{value:,.0f}" if value >= 10 else f"{value:,.2f}"

def get_usdt_irt_rate():
    try:
        data = http_get_json("api.nobitex" + ".ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        rate = float(data["stats"]["usdt-rls"]["latest"]) / 10.0
        if rate > 10000:
            return rate
    except Exception:
        pass

    try:
        data = http_get_json("api.wallex" + ".ir", "/v1/markets")
        rate = float(data["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if rate > 10000:
            return rate
    except Exception:
        pass

    try:
        data = http_get_json("open" + ".er-api.com", "/v6/latest/USD")
        rate = float(data["rates"]["IRR"]) / 10.0
        if rate > 10000:
            return rate
    except Exception:
        pass

    return 0.0
def get_all_crypto_prices():
    prices = {}
    try:
        data = http_get_json("api.gateio" + ".ws", "/api/v4/spot/tickers")
        for item in data:
            pair = item.get("currency_pair", "")
            if pair.endswith("_USDT"):
                sym = pair.replace("_USDT", "")
                last = float(item.get("last", 0))
                chg = float(item.get("change_percentage", 0))
                if last > 0:
                    prices[sym] = {"price": last, "change": chg}
    except Exception:
        pass

    # دریافت تضمینی XMR و TON از صرافی Kraken
    kraken_pairs = {"XMR": "XXMRZUSD", "TON": "TONUSD"}
    for sym, k_pair in kraken_pairs.items():
        if sym not in prices:
            try:
                data = http_get_json("api.kraken" + ".com", "/0/public/Ticker?pair=" + k_pair)
                res = data.get("result", {})
                for _, info in res.items():
                    last = float(info["c"])
                    open_p = float(info["o"])
                    chg = ((last - open_p) / open_p * 100.0) if open_p > 0 else 0.0
                    if last > 0:
                        prices[sym] = {"price": last, "change": chg}
            except Exception:
                pass

    return prices

def get_commodities():
    comm = {}
    # دریافت قیمت نقره (XAG)
    try:
        xag = http_get_json("api.gold-api" + ".com", "/price/XAG")
        if xag and xag.get("price"):
            comm["SLVON"] = {"price": float(xag["price"]), "change": 0.0}
    except Exception:
        pass

    # دریافت مس و نفت خام از CNBC / Yahoo باز
    yahoo_tickers = {"COPXON": "HG=F", "USOON": "CL=F"}
    if "SLVON" not in comm:
        yahoo_tickers["SLVON"] = "SI=F"

    for sym, ticker in yahoo_tickers.items():
        try:
            data = http_get_json("query2.finance.yahoo" + ".com", "/v8/finance/chart/" + ticker + "?interval=1d&range=2d")
            for item in data.get("chart", {}).get("result", []):
                meta = item.get("meta", {})
                price = float(meta.get("regularMarketPrice", 0))
                prev = float(meta.get("chartPreviousClose", 0))
                if price > 0:
                    chg = ((price - prev) / prev * 100.0) if prev > 0 else 0.0
                    comm[sym] = {"price": price, "change": chg}
                    break
        except Exception:
            pass

    return comm

def build_post_content(usdt_irt, crypto_map, comm_map):
    tehran_tz = timezone(timedelta(hours=3, minutes=30))
    now_tehran = datetime.now(tehran_tz)

    gregorian_str = now_tehran.strftime("%Y-%m-%d")
    day_abbr = now_tehran.strftime("%a")  # Sun, Mon, Tue...
    time_str = now_tehran.strftime("%H:%M")
    jalali_now = jdatetime.datetime.fromgregorian(datetime=now_tehran)
    jalali_arabic = to_arabic_digits(jalali_now.strftime("%Y/%m/%d"))

    lines = [
        "🦎 <b>Watch Lizard</b>  •  Market Pulse",
        f"🗓 <code>{gregorian_str}</code>  |  {day_abbr} ⏰ <code>{time_str}</code>  |  <code>{jalali_arabic}</code> 🌻",
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    ]

    table_rows = []
    changes_tracker = []

    for item in WATCHLIST:
        sym = item["symbol"]
        item_type = item["type"]
        usd_price = 0.0
        change_24h = None

        if item_type == "usdt":
            irt_price = usdt_irt
            usd_price = 1.0
        elif item_type == "crypto":
            m_info = crypto_map.get(item["lookup"])
            if m_info:
                usd_price = m_info["price"]
                change_24h = m_info["change"]
            irt_price = usd_price * usdt_irt if (usd_price > 0 and usdt_irt > 0) else 0
        elif item_type == "commodity":
            c_info = comm_map.get(sym)
            if c_info:
                usd_price = c_info["price"]
                change_24h = c_info["change"]
            irt_price = usd_price * usdt_irt if (usd_price > 0 and usdt_irt > 0) else 0

        if change_24h is not None:
            dot = "🟢" if change_24h >= 0 else "🔴"
            sign = "+" if change_24h > 0 else ""
            pct_str = f"{sign}{change_24h:.1f}%"
            changes_tracker.append({"sym": sym, "chg": float(change_24h)})
        else:
            dot = "⚪️"
            pct_str = "0.0%"

        irt_str = format_irt(irt_price)

        if item_type == "usdt":
            # چیدمان تراز شده: نماد چپ، قیمت تومانی راست
            row = f"▫️ {sym:<6} {'—':<10} {irt_str:>13} IRT ⚪️"
        else:
            usd_str = format_usd(usd_price)
            # ستون صاف: نماد | قیمت دلاری | قیمت تومانی (راست‌چین) | درصد | دایره در منتهی‌الیه راست
            row = f"▫️ {sym:<6} {usd_str:<10} {irt_str:>13} {pct_str:>6} {dot}"

        table_rows.append(row)

    # قرار دادن جدول داخل pre برای صاف ماندن کامل ستون دایره‌ها و قیمت تومانی در سمت راست
    lines.append("<pre>" + "\n".join(table_rows) + "</pre>")

    if len(changes_tracker) >= 2:
        top_gainer = max(changes_tracker, key=lambda x: x["chg"])
        top_loser = min(changes_tracker, key=lambda x: x["chg"])

        lines.append("<blockquote expandable>📊 <b>24h Watchlist Summary</b>")
        lines.append(f"▲ Top Gainer: {top_gainer['sym']} (<code>{top_gainer['chg']:+.2f}%</code>)")
        lines.append(f"▼ Top Loser: {top_loser['sym']} (<code>{top_loser['chg']:+.2f}%</code>)</blockquote>")

    return "\n".join(lines)

def tg_api_call(method, payload):
    scheme = "https" + "://"
    tg_host = "api.telegram" + ".org"
    url = scheme + tg_host + "/bot" + BOT_TOKEN + "/" + method
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Telegram API error ({method}): {e}")
        return None

def send_or_update_telegram(text):
    tv_chart_url = "https" + "://www.tradingview" + ".com/chart/"
    reply_markup = {
        "inline_keyboard": [
            [{"text": "📈 Open Live Charts", "url": tv_chart_url}]
        ]
    }

    res = tg_api_call("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": reply_markup
    })

    if res and res.get("ok"):
        print(f"SUCCESS: Message sent. ID: {res.get('result', {}).get('message_id')}")

    if PINNED_MSG_ID and PINNED_MSG_ID.isdigit():
        tg_api_call("editMessageText", {
            "chat_id": CHANNEL_ID,
            "message_id": int(PINNED_MSG_ID),
            "text": text + "\n📌 Live Board • Auto-updated every 5m",
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup
        })

if __name__ == "__main__":
    if not BOT_TOKEN or not CHANNEL_ID:
        exit(1)

    usdt_rate = get_usdt_irt_rate()
    crypto_prices = get_all_crypto_prices()
    comm_prices = get_commodities()
    post_text = build_post_content(usdt_rate, crypto_prices, comm_prices)
    send_or_update_telegram(post_text)
