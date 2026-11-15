import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
PINNED_MSG_ID = os.environ.get("PINNED_MSG_ID", "").strip()

WATCHLIST = [
    {"symbol": "USDT", "type": "usdt", "tv": "CRYPTO:USDTUSD"},
    {"symbol": "BTC", "type": "crypto", "lookup": "BTC", "tv": "BINANCE:BTCUSDT"},
    {"symbol": "ETH", "type": "crypto", "lookup": "ETH", "tv": "BINANCE:ETHUSDT"},
    {"symbol": "XRP", "type": "crypto", "lookup": "XRP", "tv": "BINANCE:XRPUSDT"},
    {"symbol": "SOL", "type": "crypto", "lookup": "SOL", "tv": "BINANCE:SOLUSDT"},
    {"symbol": "PAXG", "type": "crypto", "lookup": "PAXG", "tv": "BINANCE:PAXGUSDT"},
    {"symbol": "SLVON", "type": "commodity", "tv": "TVC:SILVER"},
    {"symbol": "COPXON", "type": "commodity", "tv": "COMEX:HG1!"},
    {"symbol": "USOON", "type": "commodity", "tv": "TVC:USOIL"},
    {"symbol": "GRAM", "type": "crypto", "lookup": "TON", "tv": "OKX:TONUSDT"},
    {"symbol": "DOGE", "type": "crypto", "lookup": "DOGE", "tv": "BINANCE:DOGEUSDT"},
    {"symbol": "LINK", "type": "crypto", "lookup": "LINK", "tv": "BINANCE:LINKUSDT"},
    {"symbol": "XMR", "type": "crypto", "lookup": "XMR", "tv": "KRAKEN:XMRUSD"},
    {"symbol": "BNB", "type": "crypto", "lookup": "BNB", "tv": "BINANCE:BNBUSDT"},
    {"symbol": "TRX", "type": "crypto", "lookup": "TRX", "tv": "BINANCE:TRXUSDT"},
    {"symbol": "ADA", "type": "crypto", "lookup": "ADA", "tv": "BINANCE:ADAUSDT"},
    {"symbol": "ZEC", "type": "crypto", "lookup": "ZEC", "tv": "BINANCE:ZECUSDT"},
    {"symbol": "SUI", "type": "crypto", "lookup": "SUI", "tv": "BINANCE:SUIUSDT"},
    {"symbol": "LTC", "type": "crypto", "lookup": "LTC", "tv": "BINANCE:LTCUSDT"},
    {"symbol": "NOT", "type": "crypto", "lookup": "NOT", "tv": "BINANCE:NOTUSDT"},
]

def to_arabic_digits(text):
    return text.translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

def to_persian_digits(text):
    return text.translate(str.maketrans("0123456789", "۱۲۳۴۵۶۷۸۹۰"))

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

def format_irt_persian(value):
    if value is None or value <= 0:
        return "—"
    raw = f"{value:,.0f}" if value >= 10 else f"{value:,.2f}"
    return to_persian_digits(raw)

def get_usdt_irt_rate():
    try:
        data = http_get_json("api.nobitex" + ".ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        rate = float(data["stats"]["usdt-rls"]["latest"]) / 10.0
        if 50000 < rate < 350000:
            return rate
    except Exception:
        pass

    try:
        data = http_get_json("api.wallex" + ".ir", "/v1/markets")
        rate = float(data["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if 50000 < rate < 350000:
            return rate
    except Exception:
        pass

    try:
        data = http_get_json("publicapi.ramzinex" + ".com", "/exchange/api/v1.0/exchange/pairs")
        for pair in data.get("data", []):
            if pair.get("url_name") == "usdt-irr":
                rate = float(pair.get("buy", 0)) / 10.0
                if 50000 < rate < 350000:
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

    try:
        data = http_get_json("api.kucoin" + ".com", "/api/v1/market/allTickers")
        for item in data.get("data", {}).get("ticker", []):
            pair = item.get("symbol", "")
            if pair.endswith("-USDT"):
                sym = pair.replace("-USDT", "")
                if sym not in prices:
                    last = float(item.get("last", 0))
                    chg = float(item.get("changeRate", 0)) * 100.0
                    if last > 0:
                        prices[sym] = {"price": last, "change": chg}
    except Exception:
        pass

    for sym in ["TON", "XMR"]:
        if sym not in prices:
            try:
                data = http_get_json("api.coinbase" + ".com", "/v2/prices/" + sym + "-USD/spot")
                amt = float(data.get("data", {}).get("amount", 0))
                if amt > 0:
                    prices[sym] = {"price": amt, "change": 0.0}
            except Exception:
                pass

    return prices

def get_commodities():
    comm = {}
    try:
        xag = http_get_json("api.gold-api" + ".com", "/price/XAG")
        if xag and xag.get("price"):
            comm["SLVON"] = {"price": float(xag["price"]), "change": 0.0}
    except Exception:
        pass

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

def pad_for_proportional_font(sym_text, usd_text):
    narrow_chars = set("I1.,$:")
    wide_chars = set("WMG@")

    def calc_width(s):
        w = 0.0
        for ch in s:
            if ch in narrow_chars:
                w += 0.55
            elif ch in wide_chars:
                w += 1.25
            else:
                w += 1.0
        return w

    sym_w = calc_width(sym_text)
    usd_w = calc_width(usd_text)

    gap1_units = max(1, round((7.2 - sym_w) * 2))
    gap1 = "\u2002" + ("\u2006" * gap1_units)

    gap2_units = max(1, round((10.8 - usd_w) * 2))
    gap2 = "\u2002" + ("\u2006" * gap2_units)

    return gap1, gap2

def build_post_content(usdt_irt, crypto_map, comm_map):
    tehran_tz = timezone(timedelta(hours=3, minutes=30))
    now_tehran = datetime.now(tehran_tz)

    gregorian_str = now_tehran.strftime("%Y-%m-%d")
    day_abbr = now_tehran.strftime("%a")
    time_str = now_tehran.strftime("%H:%M")
    jalali_now = jdatetime.datetime.fromgregorian(datetime=now_tehran)
    jalali_arabic = to_arabic_digits(jalali_now.strftime("%Y/%m/%d"))

    lines = [
        "🦎 <b>Watch Lizard</b>  •  Market Pulse",
        f"🗓 {gregorian_str}  |  {day_abbr} ⏰ {time_str}  |  {jalali_arabic} 🌻",
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    ]

    changes_tracker = []

    for item in WATCHLIST:
        sym = item["symbol"]
        item_type = item["type"]
        tv_url = "https" + "://www.tradingview" + ".com/chart/?symbol=" + item["tv"]
        sym_link = f'<a href="{tv_url}">{sym}</a>'

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
            pct_text = f"{sign}{change_24h:.1f}%"
            changes_tracker.append({"sym": sym, "chg": float(change_24h)})
        else:
            dot = "⚪️"
            pct_text = "0.0%"

        irt_fa = format_irt_persian(irt_price)
        usd_str = "$1.00" if item_type == "usdt" else format_usd(usd_price)
        gap1, gap2 = pad_for_proportional_font(sym, usd_str)

        if item_type == "usdt":
            lines.append(f"▫️ {sym_link}{gap1}{usd_str}{gap2}⚪️\u2002\u2066{irt_fa} تومن\u2069")
        else:
            lines.append(
                f"▫️ {sym_link}{gap1}{usd_str}{gap2}{dot} {pct_text}\u2002|\u2002\u2066{irt_fa} تومن\u2069"
            )

    if len(changes_tracker) >= 2:
        top_gainer = max(changes_tracker, key=lambda x: x["chg"])
        top_loser = min(changes_tracker, key=lambda x: x["chg"])

        lines.append("<blockquote expandable>📊 <b>24h Watchlist Summary</b>")
        lines.append(f"▲ Top Gainer: {top_gainer['sym']} ({top_gainer['chg']:+.2f}%)")
        lines.append(f"▼ Top Loser: {top_loser['sym']} ({top_loser['chg']:+.2f}%)</blockquote>")

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
    res = tg_api_call("sendMessage", {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })

    if res and res.get("ok"):
        print(f"SUCCESS: Message sent. ID: {res.get('result', {}).get('message_id')}")

    if PINNED_MSG_ID and PINNED_MSG_ID.isdigit():
        tg_api_call("editMessageText", {
            "chat_id": CHANNEL_ID,
            "message_id": int(PINNED_MSG_ID),
            "text": text + "\n📌 Live Board • Auto-updated",
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        })

if __name__ == "__main__":
    if not BOT_TOKEN or not CHANNEL_ID:
        exit(1)

    usdt_rate = get_usdt_irt_rate()
    crypto_prices = get_all_crypto_prices()
    comm_prices = get_commodities()
    post_text = build_post_content(usdt_rate, crypto_prices, comm_prices)
    send_or_update_telegram(post_text)
