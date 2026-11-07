"""Checks Reserved for sizes XS/S of the jacquard jacket and pings you on Telegram."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

URL = "https://www.reserved.com/es/es/chaqueta-jacquard-482lo-mlc"
PRODUCT = "482LO-MLC"
WANTED = ["XS", "S", "XXL"]  # sizes you want to be alerted about

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def get_page():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def send(text):
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    urllib.request.urlopen(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, timeout=30)


def parse_sizes(html):
    """Finds the per-size stock entries the page embeds, e.g.
    {"isInStock":false,...,"sizeName":"XS","sku":"482LO-MLC-XS","stock":false,"stockQuantity":0}"""
    sizes = {}
    pattern = r'\{[^{}]*"sku":"' + re.escape(PRODUCT) + r'-[A-Z]+"[^{}]*\}'
    for m in re.finditer(pattern, html):
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
        if "isInStock" in obj and "sizeName" in obj:
            sizes[obj["sizeName"]] = obj
    return sizes


def main():
    sizes = parse_sizes(get_page())
    if not sizes:
        sys.exit("No stock data found - the site may have changed or blocked the request.")

    summary = ", ".join(f'{n}: {s.get("stockQuantity", "?") if s["isInStock"] else "0"}'
                        for n, s in sizes.items())
    print("Stock:", summary)

    available = [n for n in WANTED if sizes.get(n, {}).get("isInStock")]
    if available:
        send(f"🧥 Back in stock: {', '.join(available)}!\n{URL}")
    elif os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        # Manual "Run workflow" click: send a status message so you can test the bot.
        send(f"✅ Bot is working. Current stock - {summary}")


if __name__ == "__main__":
    main()
