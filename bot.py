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
    {"symbol": "BTC", "type": "crypto", "tv": "BINANCE:BTCUSDT"},
    {"symbol": "ETH", "type": "crypto", "tv": "BINANCE:ETHUSDT"},
    {"symbol": "XRP", "type": "crypto", "tv": "BINANCE:XRPUSDT"},
    {"symbol": "SOL", "type": "crypto", "tv": "BINANCE:SOLUSDT"},
    {"symbol": "PAXG", "type": "crypto", "tv": "BINANCE:PAXGUSDT"},
    {"symbol": "SLVON", "type": "commodity", "tv": "TVC:SILVER"},
    {"symbol": "COPXON", "type": "commodity", "tv": "COMEX:HG1!"},
    {"symbol": "USOON", "type": "commodity", "tv": "TVC:USOIL"},
    {"symbol": "GRAM", "type": "crypto", "alias": "TON", "tv": "OKX:TONUSDT"},
    {"symbol": "DOGE", "type": "crypto", "tv": "BINANCE:DOGEUSDT"},
    {"symbol": "LINK", "type": "crypto", "tv": "BINANCE:LINKUSDT"},
    {"symbol": "XMR", "type": "crypto", "tv": "KRAKEN:XMRUSD"},
    {"symbol": "BNB", "type": "crypto", "tv": "BINANCE:BNBUSDT"},
    {"symbol": "TRX", "type": "crypto", "tv": "BINANCE:TRXUSDT"},
    {"symbol": "ADA", "type": "crypto", "tv": "BINANCE:ADAUSDT"},
    {"symbol": "ZEC", "type": "crypto", "tv": "BINANCE:ZECUSDT"},
    {"symbol": "SUI", "type": "crypto", "tv": "BINANCE:SUIUSDT"},
    {"symbol": "LTC", "type": "crypto", "tv": "BINANCE:LTCUSDT"},
    {"symbol": "NOT", "type": "crypto", "tv": "BINANCE:NOTUSDT"},
]

def to_arabic_digits(text):
    mapping = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
    return text.translate(mapping)

def http_get_json(host, path):
    url = "https://" + host + path
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    })
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
    try:
        data = http_get_json("api.nobitex.ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        rate = float(data["stats"]["usdt-rls"]["latest"]) / 10.0
        if rate > 10000:
            return rate
    except Exception:
        pass

    try:
        data = http_get_json("api.wallex.ir", "/v1/markets")
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
        data = http_get_json("api.gateio.ws", "/api/v4/spot/tickers")
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
        data = http_get_json("://kucoin.com", "/api/v1/market/allTickers")
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

    return prices

def get_commodities():
    comm = {}
    try:
        xag = http_get_json("://gold-api.com", "/price/XAG")
        if xag and xag.get("price"):
            comm["SLVON"] = {"price": float(xag["price"]), "change": None}
    except Exception:
        pass

    stooq_map = {"COPXON": "hg.f", "USOON": "cl.f"}
    for sym, code in stooq_map.items():
        try:
            data = http_get_json("stooq.com", "/q/l/?s=" + code + "&f=sd2t2ohlcv&h&e=json")
            for info in data.get("symbols", []):
                close_p = float(info.get("close", 0))
                open_p = float(info.get("open", 0))
                if close_p > 0:
                    chg = ((close_p - open_p) / open_p * 100.0) if open_p > 0 else None
                    comm[sym] = {"price": close_p, "change": chg}
                    break
        except Exception:
            pass

    return comm

def build_post_content(usdt_irt, crypto_map, comm_map):
    tehran_tz = timezone(timedelta(hours=3, minutes=30))
    now_tehran = datetime.now(tehran_tz)

    gregorian_str = now_tehran.strftime("%Y-%m-%d")
    time_str = now_tehran.strftime("%H:%M")
    jalali_now = jdatetime.datetime.fromgregorian(datetime=now_tehran)
    jalali_arabic = to_arabic_digits(jalali_now.strftime("%Y/%m/%d"))

    lines = [
        "🦎 <b>Watch Lizard</b>  •  Market Pulse",
        f"🗓 <code>{gregorian_str}</code>   |   ⏰ <code>{time_str}</code>   |   <code>{jalali_arabic}</code>",
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    ]

    changes_tracker = []

    for item in WATCHLIST:
        sym = item["symbol"]
        lookup_sym = item.get("alias", sym)
        item_type = item["type"]
        tv_link = "https://tradingview.com" + item["tv"]
        sym_label = f'<a href="{tv_link}">{sym}</a>'

        usd_price = 0.0
        change_24h = None

        if item_type == "usdt":
            irt_price = usdt_irt
            usd_price = 1.0
        elif item_type == "crypto":
            m_info = crypto_map.get(lookup_sym)
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
            right_side_status = f"  {dot} <code>{sign}{change_24h:.1f}%</code>"
            changes_tracker.append({"sym": sym, "chg": float(change_24h)})
        else:
            right_side_status = ""

        irt_formatted = format_price(irt_price, is_irt=True)

        if item_type == "usdt":
            lines.append(f"▫️ {sym_label}:  <code>{irt_formatted}</code> IRT")
        else:
            usd_formatted = format_price(usd_price, is_irt=False)
            lines.append(
                f"▫️ {sym_label}:  <code>${usd_formatted}</code>  |  <code>{irt_formatted}</code> IRT{right_side_status}"
            )

    if len(changes_tracker) >= 2:
        top_gainer = max(changes_tracker, key=lambda x: x["chg"])
        top_loser = min(changes_tracker, key=lambda x: x["chg"])

        lines.append("\n<blockquote expandable>📊 <b>24h Watchlist Summary</b>")
        lines.append(f"▲ Top Gainer: {top_gainer['sym']} (<code>{top_gainer['chg']:+.2f}%</code>)")
        lines.append(f"▼ Top Loser: {top_loser['sym']} (<code>{top_loser['chg']:+.2f}%</code>)")
        lines.append("Tap any ticker symbol to open its live chart.</blockquote>")

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
            "text": text + "\n\n📌 Live Board • Auto-updated every 5m",
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
