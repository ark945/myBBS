import asyncio
import codecs
from collections import Counter

import uao
uao.register_uao()
try:
    codecs.lookup('big5-uao')
except LookupError:
    def _search(enc):
        if enc in ('big5_uao', 'big5-uao'):
            try:
                return codecs.lookup('big5uao')
            except LookupError:
                pass
        return None
    codecs.register(_search)

import websockets

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Origin": "https://term.ptt.cc",
}


def east_asian_width(cp):
    # Rough East Asian Width classification for reporting only
    if (0x1100 <= cp <= 0x115F) or (0x2E80 <= cp <= 0xA4CF) or \
       (0xAC00 <= cp <= 0xD7A3) or (0xF900 <= cp <= 0xFAFF) or \
       (0xFE30 <= cp <= 0xFE4F) or (0xFF00 <= cp <= 0xFF60) or \
       (0xFFE0 <= cp <= 0xFFE6) or (0x20000 <= cp <= 0x3FFFD):
        return "WIDE(2)"
    if (0x2500 <= cp <= 0x259F) or (0x25A0 <= cp <= 0x25FF):
        return "box/block(1)"
    if cp < 0x7F:
        return "ascii(1)"
    return f"other({cp:#x})"


async def main():
    url = "wss://ws.ptt.cc/bbs"
    try:
        conn = await websockets.connect(url, additional_headers=HEADERS)
    except TypeError:
        conn = await websockets.connect(url, extra_headers=HEADERS)

    data = bytearray()
    async with conn as ws:
        try:
            while len(data) < 4096:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                if isinstance(msg, bytes):
                    data.extend(msg)
                else:
                    data.extend(msg.encode('utf-8'))
        except asyncio.TimeoutError:
            pass

    raw = bytes(data)
    print("=== RAW LENGTH:", len(raw), "===")
    print("=== RAW HEX (first 160 bytes) ===")
    print(raw[:160].hex())
    print()

    text = raw.decode('big5-uao', errors='replace')
    print("=== DECODED AS BIG5-UAO (visible, first 700 chars) ===")
    print(text[:700])
    print()
    print("=== UNIQUE NON-ASCII CODE POINTS: char | U+hex | EAW class | count ===")
    c = Counter(ch for ch in text if ord(ch) >= 0x7F)
    for ch, cnt in sorted(c.items(), key=lambda x: -x[1]):
        print(f"{ch!r:8} U+{ord(ch):04X}   {east_asian_width(ord(ch)):16} x{cnt}")


asyncio.run(main())
