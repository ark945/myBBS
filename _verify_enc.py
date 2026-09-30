"""Verify the actual encoding/frame-type of wss://ws.ptt.cc/bbs stream.

Compares UTF-8 vs big5-uao decoding of the captured login screen so we can
decide how app.py should translate between PTT and the browser.
"""
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
    conn = await asyncio.wait_for(
        websockets.connect("wss://ws.ptt.cc/bbs", additional_headers=HEADERS), timeout=15
    )
    data = bytearray()
    frame_types = []
    async with conn as ws:
        try:
            while len(data) < 6000:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                if isinstance(msg, bytes):
                    frame_types.append("binary")
                    data.extend(msg)
                else:
                    frame_types.append("text(utf-8)")
                    data.extend(msg.encode("utf-8"))
        except Exception:
            pass
    return bytes(data), frame_types


raw, frame_types = asyncio.run(main())
print(f"=== RAW LENGTH: {len(raw)} ===")
print(f"=== FRAME TYPES (first 10): {frame_types[:10]} ... total={len(frame_types)} ===")
print("=== RAW HEX (first 200 bytes) ===")
print(raw[:200].hex())

ansi_re = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[\(\)][A-B0-2]")


def strip_ansi(s):
    return ansi_re.sub("", s)


print("\n=== DECODED AS UTF-8 (ANSI stripped, first 40 lines) ===")
try:
    utf8_text = raw.decode("utf-8", errors="replace")
    bad = utf8_text.count("\ufffd")
    print(f"(U+FFFD replacement count: {bad})")
    for i, line in enumerate(strip_ansi(utf8_text).splitlines()[:40]):
        print(f"{i:2d}|{line}")
except Exception as e:
    print("utf-8 decode failed:", e)

print("\n=== DECODED AS BIG5-UAO (ANSI stripped, first 15 lines) ===")
big5_text = raw.decode("big5-uao", errors="replace")
for i, line in enumerate(strip_ansi(big5_text).splitlines()[:15]):
    print(f"{i:2d}|{line}")
