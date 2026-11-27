import os
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
MINI_APP_BASE = "https://t.me" + "/watchlizardbot/chart?startapp="

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

def to_subscript(s):
    return s.translate(str.maketrans("0123456789+-", "₀₁₂₃₄₅₆₇₈₉₊₋"))

def fetch_json(host, path):
    scheme = "https" + "://"
    req = urllib.request.Request(
        scheme + host + path,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def get_usdt_irt():
    try:
        d = fetch_json("api.nobitex" + ".ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        p = float(d["stats"]["usdt-rls"]["latest"]) / 10.0
        if p > 10000:
            return p
    except Exception:
        pass

    try:
        d = fetch_json("api.wallex" + ".ir", "/v1/markets")
        p = float(d["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if p > 10000:
            return p
    except Exception:
        pass

    return 0.0

def get_cryptos():
    prices = {}
    try:
        for item in fetch_json("api.gateio" + ".ws", "/api/v4/spot/tickers"):
            pair = item.get("currency_pair", "")
            if pair.endswith("_USDT"):
                last = float(item.get("last", 0))
                if last > 0:
                    prices[pair[:-5]] = {"price": last, "chg": float(item.get("change_percentage", 0))}
    except Exception:
        pass

    for sym, kpair in {"XMR": "XXMRZUSD", "TON": "TONUSD", "USDT": "USDTZUSD"}.items():
        if sym not in prices:
            try:
                d = fetch_json("api.kraken" + ".com", "/0/public/Ticker?pair=" + kpair)
                for _, info in d.get("result", {}).items():
                    c_list = info.get("c", [])
                    o_val = float(info.get("o", 0))
                    for c_str in c_list:
                        last = float(c_str)
                        if last > 0:
                            chg = ((last - o_val) / o_val * 100.0) if o_val > 0 else 0.0
                            prices[sym] = {"price": last, "chg": chg}
                        break
            except Exception:
                pass

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

def fmt_num(v, is_usdt=False):
    if v <= 0:
        return "—"
    if is_usdt:
        return f"{v:,.4f}"
    if v >= 1000:
        return f"{v:,.0f}"
    if v >= 10:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.3f}"
    if v >= 0.01:
        return f"{v:,.5f}"
    return f"{v:,.7f}"

def pad_compact(sym):
    w_s = sum(0.55 if c in "I1.,$:" else (1.25 if c in "WMG@" else 1.0) for c in sym)
    g1 = "\u2006" * max(1, round((5.0 - w_s) * 2))
    g2 = "\u2006"
    return g1, g2

عذرخواهی می‌کنم بابت این مشکل رندر شدن کد در رابط کاربری.
برای اینکه بدون هیچ‌گونه به‌هم‌ریختگی بتوانید کد را مونتاژ کنید، فایل bot.py را به دو تکه مجزا و تمیز تقسیم کردم. کافی است بخش اول و بلافاصله زیر آن بخش دوم را کپی کنید.

بسته ۱ از ۲ (از ابتدای فایل تا پایان تابع pad_compact)

python
import os
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
MINI_APP_BASE = "https://t.me" + "/watchlizardbot/chart?startapp="

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

def to_subscript(s):
    return s.translate(str.maketrans("0123456789+-", "₀₁₂₃₄₅₆₇₈₉₊₋"))

def fetch_json(host, path):
    scheme = "https" + "://"
    req = urllib.request.Request(
        scheme + host + path,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

def get_usdt_irt():
    try:
        d = fetch_json("api.nobitex" + ".ir", "/market/stats?srcCurrency=usdt&dstCurrency=rls")
        p = float(d["stats"]["usdt-rls"]["latest"]) / 10.0
        if p > 10000:
            return p
    except Exception:
        pass

    try:
        d = fetch_json("api.wallex" + ".ir", "/v1/markets")
        p = float(d["result"]["symbols"]["USDTTMN"]["stats"]["lastPrice"])
        if p > 10000:
            return p
    except Exception:
        pass

    return 0.0

def get_cryptos():
    prices = {}
    try:
        for item in fetch_json("api.gateio" + ".ws", "/api/v4/spot/tickers"):
            pair = item.get("currency_pair", "")
            if pair.endswith("_USDT"):
                last = float(item.get("last", 0))
                if last > 0:
                    prices[pair[:-5]] = {"price": last, "chg": float(item.get("change_percentage", 0))}
    except Exception:
        pass

    for sym, kpair in {"XMR": "XXMRZUSD", "TON": "TONUSD", "USDT": "USDTZUSD"}.items():
        if sym not in prices:
            try:
                d = fetch_json("api.kraken" + ".com", "/0/public/Ticker?pair=" + kpair)
                for _, info in d.get("result", {}).items():
                    c_list = info.get("c", [])
                    o_val = float(info.get("o", 0))
                    for c_str in c_list:
                        last = float(c_str)
                        if last > 0:
                            chg = ((last - o_val) / o_val * 100.0) if o_val > 0 else 0.0
                            prices[sym] = {"price": last, "chg": chg}
                        break
            except Exception:
                pass

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

def fmt_num(v, is_usdt=False):
    if v <= 0:
        return "—"
    if is_usdt:
        return f"{v:,.4f}"
    if v >= 1000:
        return f"{v:,.0f}"
    if v >= 10:
        return f"{v:,.2f}"
    if v >= 1:
        return f"{v:,.3f}"
    if v >= 0.01:
        return f"{v:,.5f}"
    return f"{v:,.7f}"

def pad_compact(sym):
    w_s = sum(0.55 if c in "I1.,$:" else (1.25 if c in "WMG@" else 1.0) for c in sym)
    g1 = "\u2006" * max(1, round((5.0 - w_s) * 2))
    g2 = "\u2006"
    return g1, g2
def build_post(usdt_irt, cryptos, comms, with_seconds=True):
    now = datetime.now(timezone(timedelta(hours=3, minutes=30)))
    j_str = to_arabic(jdatetime.datetime.fromgregorian(datetime=now).strftime("%Y/%m/%d"))
    time_fmt = "%H:%M:%S" if with_seconds else "%H:%M"
    lines = [
        f"{now.strftime('%a')}, {now.strftime('%Y-%m-%d')} 🗓 {now.strftime(time_fmt)} ⏰ {j_str}",
        "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"
    ]
    tracker = []
    for it in WATCHLIST:
        sym, tp = it["symbol"], it["type"]
        safe_tv = it["tv"].replace(":", "_").replace("!", "")
        app_url = f"{MINI_APP_BASE}{safe_tv}"
        link = f'<a href="{app_url}">{sym}</a>'

        usd, chg = 0.0, None
        if tp == "usdt":
            if "USDT" in cryptos:
                usd = cryptos["USDT"]["price"]
                chg = cryptos["USDT"]["chg"]
            else:
                usd = 1.0
        elif tp == "crypto" and it["lookup"] in cryptos:
            usd, chg = cryptos[it["lookup"]]["price"], cryptos[it["lookup"]]["chg"]
        elif tp == "commodity" and sym in comms:
            usd, chg = comms[sym]["price"], comms[sym]["chg"]

        irt_val = usd * usdt_irt if (usd > 0 and usdt_irt > 0) else 0
        if irt_val > 0:
            raw_irt = f"{irt_val:,.0f}" if irt_val >= 10 else f"{irt_val:,.2f}"
            if tp == "usdt":
                irt_display = f"<code>{raw_irt}</code>"
            else:
                irt_display = to_persian(raw_irt)
        else:
            irt_display = "—"

        num_str = fmt_num(usd, is_usdt=(tp == "usdt"))

        if chg is not None:
            dot = "🟢" if chg >= 0 else "🔴"
            pct = to_subscript(f"{'+' if chg > 0 else ''}{chg:.1f}")
            if tp != "usdt":
                tracker.append({"sym": sym, "chg": chg})
        else:
            dot, pct = "⚪️", to_subscript("0.0")

        g1, g2 = pad_compact(sym)
        usd_part = f"<code>{num_str}</code>$" if num_str != "—" else "—"

        irt_sep = "\u200a" if irt_val >= 100_000_000 else "\u2009"
        pre_toman = "" if irt_val >= 100_000_000 else "\u2006"

        lines.append(f"▫️{link}{g1}{usd_part}{g2}{pct}{dot}{pre_toman}\u200eتومن{irt_sep}\u200e{irt_display}")

    if len(tracker) >= 2:
        hi = max(tracker, key=lambda x: x["chg"])
        lo = min(tracker, key=lambda x: x["chg"])
        lines.append("")
        lines.append(f"<blockquote>📊 24h: 🚀 {hi['sym']} {hi['chg']:+.1f}% | 🔻 {lo['sym']} {lo['chg']:+.1f}%</blockquote>")
    return "\n".join(lines)

def tg_call(method, payload):
    url = "https" + "://api.telegram" + ".org/bot" + BOT_TOKEN + "/" + method
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"Telegram API Error ({e.code}): {err_body}")
        return None
    except Exception as e:
        print(f"Network/TG Error: {e}")
        return None

if __name__ == "__main__":
    if BOT_TOKEN and CHANNEL_ID:
        now_ir = datetime.now(timezone(timedelta(hours=3, minutes=30)))
        u = get_usdt_irt()
        c = get_cryptos()
        cm = get_commodities()

        chat_info = tg_call("getChat", {"chat_id": CHANNEL_ID})
        pinned_id = None
        if chat_info and chat_info.get("ok"):
            pinned_msg = chat_info.get("result", {}).get("pinned_message")
            if pinned_msg:
                pinned_id = pinned_msg.get("message_id")

        if now_ir.minute % 5 == 0 or not pinned_id:
            if pinned_id:
                archive_text = build_post(u, c, cm, with_seconds=False)
                tg_call("editMessageText", {
                    "chat_id": CHANNEL_ID,
                    "message_id": pinned_id,
                    "text": archive_text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                })
                tg_call("unpinChatMessage", {
                    "chat_id": CHANNEL_ID,
                    "message_id": pinned_id
                })

            live_text = build_post(u, c, cm, with_seconds=True)
            sent = tg_call("sendMessage", {
                "chat_id": CHANNEL_ID,
                "text": live_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            })
            if sent and sent.get("ok"):
                pinned_id = sent["result"]["message_id"]
                tg_call("pinChatMessage", {
                    "chat_id": CHANNEL_ID,
                    "message_id": pinned_id,
                    "disable_notification": True
                })

        if pinned_id:
            for _ in range(9):
                time.sleep(5 - (time.time() % 5))
                live_text = build_post(u, c, cm, with_seconds=True)
                tg_call("editMessageText", {
                    "chat_id": CHANNEL_ID,
                    "message_id": pinned_id,
                    "text": live_text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                })
Use code with caution.
(نکته: بین بسته ۱ و بسته ۲ فقط یک خط خالی بگذارید تا دقیقاً به هم متصل شوند).
