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

def to_arabic(s):
    return s.translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))

def to_persian(s):
    return s.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fetch_json(host, path):
    scheme = "https" + "://"
    req = urllib.request.Request(
        scheme + host + path,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def get_usdt_irt():
    # همان منبع سالم ساعت 05:31 صبح امروز (نوبیتکس)
    try:
        d = fetch_json("api.nobitex" + ".ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        p = float(d["stats"]["usdt-rls"]["latest"]) / 10.0
        if p > 10000:
            print(f"USDT loaded from Nobitex: {p}")
            return p
    except Exception as e:
        print(f"Nobitex err: {e}")

    # پشتیبان دوم: صرافی والکس (همان نسخه صبح)
    try:
        d = fetch_json("api.wallex" + ".ir", "/v1/markets")
        p = float(d["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if p > 10000:
            print(f"USDT loaded from Wallex: {p}")
            return p
    except Exception as e:
        print(f"Wallex err: {e}")

    return 0.0
def get_binance_data():
    """Return Binance 24h prices and changes for available USDT spot pairs."""
    prices = {}
    try:
        data = fetch_json("api.binance" + ".com", "/api/v3/ticker/24hr")
        for item in data:
            pair = item.get("symbol", "")
            if pair.endswith("USDT"):
                sym = pair[:-4]
                last = float(item.get("lastPrice", 0) or 0)
                chg = float(item.get("priceChangePercent", 0) or 0)
                if last > 0:
                    prices[sym] = {"price": last, "chg": chg}
    except Exception as e:
        print(f"Binance err: {e}")
    return prices


def get_usdt_usd(binance_data):
    """Estimate USDT/USD from Binance USDCUSDT (inverse quote)."""
    try:
        usdc_usdt = float(binance_data.get("USDC", {}).get("price", 0))
        if usdc_usdt > 0:
            rate = 1.0 / usdc_usdt
            if 0.90 < rate < 1.10:
                print(f"USDT/USD loaded from Binance: {rate}")
                return rate
    except Exception as e:
        print(f"USDT/USD err: {e}")
    return 1.0


def get_cryptos(binance_data=None):
    prices = dict(binance_data or {})
    # Kraken fallback only for assets not available as Binance USDT spot pairs.
    for sym, kpair in {"XMR": "XXMRZUSD", "TON": "TONUSD"}.items():
        if sym not in prices:
            try:
                d = fetch_json("api.kraken" + ".com", "/0/public/Ticker?pair=" + kpair)
                for _, info in d.get("result", {}).items():
                    last = float(info.get("c", [0])[0])
                    opening = float(info.get("o", 0))
                    if last > 0:
                        chg = ((last - opening) / opening * 100.0) if opening > 0 else 0.0
                        prices[sym] = {"price": last, "chg": chg, "quote": "USD"}
                    break
            except Exception as e:
                print(f"Kraken {sym} err: {e}")
    return prices


def get_commodities():
    comm = {}
    try:
        xag = fetch_json("api.gold-api" + ".com", "/price/XAG")
        if xag.get("price"):
            comm["SLVON"] = {"price": float(xag["price"]), "chg": 0.0}
    except Exception:
        pass

    for sym, tk in {"COPXON": "HG=F", "USOON": "CL=F"}.items():
        try:
            d = fetch_json("query2.finance.yahoo" + ".com", "/v8/finance/chart/" + tk + "?interval=1d&range=2d")
            for it in d.get("chart", {}).get("result", []):
                meta = it.get("meta", {})
                p = float(meta.get("regularMarketPrice", 0))
                prev = float(meta.get("chartPreviousClose", 0))
                if p > 0:
                    comm[sym] = {"price": p, "chg": ((p - prev) / prev * 100.0) if prev > 0 else 0.0}
                    break
        except Exception:
            pass
    return comm

def fmt_usd(v, sym=""):
    if v <= 0:
        return "—"
    if sym == "NOT":
        return f"{v:,.7f}"
    if v >= 1000:
        return f"{v:,.0f}"
    if v >= 10:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.3f}"
    return f"{v:,.5f}"


def subscript_pct(value):
    # Compact percentage without %; all digits use Unicode subscript forms.
    raw = f"{abs(value):.1f}"
    digits = str.maketrans("0123456789.-", "₀₁₂₃₄₅₆₇₈₉.₋")
    sign = "₊" if value >= 0 else "₋"
    return sign + raw.translate(digits)


def align_fa_amount(value):
    text = to_persian(f"{value:,.0f}" if value >= 10 else f"{value:,.2f}") if value > 0 else "—"
    # Figure spaces keep the final (ones) digit in a consistent right-hand column.
    visible_len = len(text)
    return (" " * max(0, 15 - visible_len)) + text


def build_post(usdt_irt, cryptos, comms, usdt_usd=1.0):
    now = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    j_str = to_arabic(jdatetime.datetime.fromgregorian(datetime=now).strftime("%Y/%m/%d"))
    header = f"{now.strftime('%a, %Y-%m-%d')}  🗓  {now.strftime('%H:%M')}  ⏰  {j_str}"
    # get_usdt_irt is the local USDT rate; derive the free USD/IRT rate from USDT/USD.
    usd_irt = (usdt_irt / usdt_usd) if (usdt_irt > 0 and usdt_usd > 0) else 0.0
    lines = [header, "┄" * 32]
    tracker = []
    for it in WATCHLIST:
        sym, tp = it["symbol"], it["type"]
        tv_url = "https" + "://www.tradingview" + ".com/chart/?symbol=" + it["tv"]
        link = f'<a href="{tv_url}">{sym}</a>'
        usd, chg = 0.0, None
        if tp == "usdt":
            usd = usdt_usd
            chg = None
        elif tp == "crypto" and it["lookup"] in cryptos:
            quote = cryptos[it["lookup"]].get("quote", "USDT")
            factor = 1.0 if quote == "USD" else usdt_usd
            usd, chg = cryptos[it["lookup"]]["price"] * factor, cryptos[it["lookup"]]["chg"]
        elif tp == "commodity" and sym in comms:
            usd, chg = comms[sym]["price"], comms[sym]["chg"]

        irt_val = usd * usd_irt if (usd > 0 and usd_irt > 0) else 0
        irt_fa = align_fa_amount(irt_val)
        usd_digits = fmt_usd(usd, sym)
        # Keep the dollar sign outside the monospace digits.
        usd_str = f"$<code>{usd_digits}</code>"

        if chg is not None:
            dot = "🟢" if chg >= 0 else "🔴"
            compact = subscript_pct(chg)
            tracker.append({"sym": sym, "chg": chg})
        else:
            dot, compact = "⚪️", "₀.₀"

        # Fixed symbol and price columns keep every status circle on the same vertical axis.
        symbol_pad = " " * max(1, 7 - len(sym))
        price_digits = f"{usd_digits:>10}"
        usd_str = "$" + f"<code>{price_digits}</code>"
        lines.append(f"▫️ {link}{symbol_pad}{usd_str} {dot}{compact} | تومن {irt_fa}")

    if len(tracker) >= 2:
        hi = max(tracker, key=lambda x: x["chg"])
        lo = min(tracker, key=lambda x: x["chg"])
        lines.append(f"📊 24h: 🚀 {hi['sym']} {hi['chg']:+.1f}% | 🔻 {lo['sym']} {lo['chg']:+.1f}%")
    return "\n".join(lines)


def tg_call(method, payload):
    url = "https" + "://api.telegram" + ".org/bot" + BOT_TOKEN + "/" + method
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

if __name__ == "__main__":
    if BOT_TOKEN and CHANNEL_ID:
        u = get_usdt_irt()
        binance_data = get_binance_data()
        usdt_usd = get_usdt_usd(binance_data)
        cryptos = get_cryptos(binance_data)
        text = build_post(u, cryptos, get_commodities(), usdt_usd)
        tg_call("sendMessage", {
            "chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True
        })
        if PINNED_MSG_ID and PINNED_MSG_ID.isdigit():
            tg_call("editMessageText", {
                "chat_id": CHANNEL_ID, "message_id": int(PINNED_MSG_ID),
                "text": text + "\n📌 Live Board • Auto-updated",
                "parse_mode": "HTML", "disable_web_page_preview": True
            })
