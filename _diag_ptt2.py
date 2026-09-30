import asyncio
import codecs
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

import uao

uao.register_uao()
try:
    codecs.lookup("big5-uao")
except LookupError:
    def _search(enc):
        if enc in ("big5_uao", "big5-uao"):
            try:
                return codecs.lookup("big5uao")
            except LookupError:
                pass
        return None

    codecs.register(_search)

import websockets

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://term.ptt.cc",
}


async def main():
    print("connecting...", flush=True)
    try:
        conn = await asyncio.wait_for(
            websockets.connect("wss://ws.ptt.cc/bbs", additional_headers=HEADERS), timeout=15
        )
    except TypeError:
        conn = await asyncio.wait_for(
            websockets.connect("wss://ws.ptt.cc/bbs", extra_headers=HEADERS), timeout=15
        )
    print("connected, reading...", flush=True)
    data = bytearray()
    async with conn as ws:
        try:
            while len(data) < 6000:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data.extend(msg if isinstance(msg, bytes) else msg.encode("utf-8"))
        except Exception:
            pass
    return bytes(data)


raw = asyncio.run(main())
print(f"=== RAW LENGTH: {len(raw)} ===")

text = raw.decode("big5-uao", errors="replace")
clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
print("=== FULL LOGIN SCREEN (ANSI stripped), line-numbered ===")
for i, line in enumerate(clean.splitlines()):
    print(f"{i:2d}|{line}")
