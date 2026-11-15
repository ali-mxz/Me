import os
import json
import urllib.request
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
PINNED_MSG_ID = os.environ.get("PINNED_MSG_ID", "").strip()

# چیدمان دقیق طبق ترتیب درخواستی شما + لینک چارت زنده TradingView
WATCHLIST = [
    {"symbol": "USDT", "type": "usdt", "tv": "CRYPTO:USDTUSD"},
    {"symbol": "BTC", "type": "crypto", "pair": "BTCUSDT", "tv": "BINANCE:BTCUSDT"},
    {"symbol": "ETH", "type": "crypto", "pair": "ETHUSDT", "tv": "BINANCE:ETHUSDT"},
    {"symbol": "XRP", "type": "crypto", "pair": "XRPUSDT", "tv": "BINANCE:XRPUSDT"},
    {"symbol": "SOL", "type": "crypto", "pair": "SOLUSDT", "tv": "BINANCE:SOLUSDT"},
    {"symbol": "PAXG", "type": "crypto", "pair": "PAXGUSDT", "tv": "BINANCE:PAXGUSDT"},
    {"symbol": "SLVON", "type": "commodity", "ticker": "SI=F", "tv": "TVC:SILVER"},
    {"symbol": "COPXON", "type": "commodity", "ticker": "HG=F", "tv": "COMEX:HG1!"},
    {"symbol": "USOON", "type": "commodity", "ticker": "CL=F", "tv": "TVC:USOIL"},
    {"symbol": "GRAM", "type": "crypto", "pair": "TONUSDT", "tv": "OKX:TONUSDT"},
    {"symbol": "DOGE", "type": "crypto", "pair": "DOGEUSDT", "tv": "BINANCE:DOGEUSDT"},
    {"symbol": "BNB", "type": "crypto", "pair": "BNBUSDT", "tv": "BINANCE:BNBUSDT"},
    {"symbol": "TRX", "type": "crypto", "pair": "TRXUSDT", "tv": "BINANCE:TRXUSDT"},
    {"symbol": "ADA", "type": "crypto", "pair": "ADAUSDT", "tv": "BINANCE:ADAUSDT"},
    {"symbol": "LINK", "type": "crypto", "pair": "LINKUSDT", "tv": "BINANCE:LINKUSDT"},
    {"symbol": "ZEC", "type": "crypto", "pair": "ZECUSDT", "tv": "BINANCE:ZECUSDT"},
    {"symbol": "XMR", "type": "crypto", "pair": "XMRUSDT", "tv": "KRAKEN:XMRUSD"},
    {"symbol": "SUI", "type": "crypto", "pair": "SUIUSDT", "tv": "BINANCE:SUIUSDT"},
    {"symbol": "LTC", "type": "crypto", "pair": "LTCUSDT", "tv": "BINANCE:LTCUSDT"},
    {"symbol": "NOT", "type": "crypto", "pair": "NOTUSDT", "tv": "BINANCE:NOTUSDT"},
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
        data = http_get_json("://er-api.com", "/v6/latest/USD")
        rate = float(data["rates"]["IRR"]) / 10.0
        if rate > 10000:
            return rate
    except Exception:
        pass

    return 0.0

def get_crypto_markets():
    market_dict = {}
    try:
        data = http_get_json("://mexc.com", "/api/v3/ticker/24hr")
        for item in data:
            sym = item.get("symbol", "")
            if sym.endswith("USDT"):
                price = float(item.get("lastPrice", 0))
                change = float(item.get("priceChangePercent", 0)) * 100.0
                market_dict[sym] = {"price": price, "change": change}
        if market_dict:
            return market_dict
    except Exception:
        pass

    try:
        data = http_get_json("://kucoin.com", "/api/v1/market/allTickers")
        for item in data.get("data", {}).get("ticker", []):
            sym = item.get("symbol", "").replace("-", "")
            if sym.endswith("USDT"):
                price = float(item.get("last", 0))
                change = float(item.get("changeRate", 0)) * 100.0
                market_dict[sym] = {"price": price, "change": change}
    except Exception:
        pass

    return market_dict

def get_commodity_price(ticker):
    try:
        path = "/v8/finance/chart/" + ticker + "?interval=1d&range=2d"
        data = http_get_json("://yahoo.com", path)
        results = data.get("chart", {}).get("result", [])
        if results:
            meta = results.get("meta", {})
            price = float(meta.get("regularMarketPrice", 0))
            prev_close = float(meta.get("chartPreviousClose", 0))
            change = ((price - prev_close) / prev_close * 100.0) if prev_close > 0 else 0.0
            return {"price": price, "change": change}
    except Exception as e:
        print(f"Commodity {ticker} error: {e}")
    return None

def build_post_content(usdt_irt, crypto_map):
    # زمان دقیق تهران (UTC+3:30)
    tehran_tz = timezone(timedelta(hours=3, minutes=30))
    now_tehran = datetime.now(tehran_tz)
    date_str = now_tehran.strftime("%Y-%m-%d")
    time_str = now_tehran.strftime("%H:%M")

    lines = [
        "🦎 <b>Watch Lizard</b>  •  <i>Market Pulse</i>",
        f"<code>{date_str}</code>  |  <code>{time_str} IRST</code>",
        "────────────────────"
    ]

    changes_tracker = []

    for item in WATCHLIST:
        sym = item["symbol"]
        item_type = item["type"]
        tv_link = "https://" + "://tradingview.com" + item["tv"]
        sym_label = f'<a href="{tv_link}">{sym}</a>'

        usd_price = 0.0
        change_24h = None

        if item_type == "usdt":
            irt_price = usdt_irt
            usd_price = 1.0
        elif item_type == "crypto":
            m_info = crypto_map.get(item["pair"])
            if m_info:
                usd_price = m_info["price"]
                change_24h = m_info["change"]
            irt_price = usd_price * usdt_irt if (usd_price > 0 and usdt_irt > 0) else 0
        elif item_type == "commodity":
            c_info = get_commodity_price(item["ticker"])
            if c_info:
                usd_price = c_info["price"]
                change_24h = c_info["change"]
            irt_price = usd_price * usdt_irt if (usd_price > 0 and usdt_irt > 0) else 0

        if change_24h is not None:
            dot = "🟢" if change_24h >= 0 else "🔴"
            sign = "+" if change_24h > 0 else ""
            change_str = f" {dot} <code>{sign}{change_24h:.1f}%</code>"
            changes_tracker.append({"sym": sym, "chg": float(change_24h)})
        else:
            change_str = ""

        irt_formatted = format_price(irt_price, is_irt=True)

        if item_type == "usdt":
            lines.append(f"▫️ {sym_label}: <code>{irt_formatted}</code> IRT")
        else:
            usd_formatted = format_price(usd_price, is_irt=False)
            lines.append(
                f"▫️ {sym_label}: <code>{irt_formatted}</code> IRT  |  <code>${usd_formatted}</code>{change_str}"
            )

    if len(changes_tracker) >= 2:
        top_gainer = max(changes_tracker, key=lambda x: x["chg"])
        top_loser = min(changes_tracker, key=lambda x: x["chg"])

        lines.append("\n<blockquote expandable>📊 <b>24h Watchlist Summary</b>")
        lines.append(f"▲ Top Gainer: <b>{top_gainer['sym']}</b> (<code>{top_gainer['chg']:+.2f}%</code>)")
        lines.append(f"▼ Top Loser: <b>{top_loser['sym']}</b> (<code>{top_loser['chg']:+.2f}%</code>)")
        lines.append("<i>Tap any ticker symbol to open its live chart.</i></blockquote>")

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
        print(f"SUCCESS: Message sent. ID: {msg_id}")

    if PINNED_MSG_ID and PINNED_MSG_ID.isdigit():
        tg_api_call("editMessageText", {
            "chat_id": CHANNEL_ID,
            "message_id": int(PINNED_MSG_ID),
            "text": text + "\n\n📌 <i>Live Board • Auto-updated every 30m</i>",
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        })

if __name__ == "__main__":
    if not BOT_TOKEN or not CHANNEL_ID:
        exit(1)

    usdt_rate = get_usdt_irt_rate()
    crypto_prices = get_crypto_markets()
    post_text = build_post_content(usdt_rate, crypto_prices)
    send_or_update_telegram(post_text)
