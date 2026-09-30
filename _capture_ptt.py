"""One-off debug: connect straight to PTT websocket, dump raw login-screen bytes."""
import asyncio
import re
from collections import Counter

import websockets
import uao

uao.register_uao()

URI = "wss://ws.ptt.cc/bbs"
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
    'Origin': 'https://term.ptt.cc',
    'Referer': 'https://term.ptt.cc/',
}


async def main():
    chunks = []
    async with websockets.connect(URI, additional_headers=HEADERS) as ws:
        try:
            while True:
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, bytes):
                    chunks.append(msg)
                else:
                    print("TEXT FRAME:", repr(msg[:300]))
        except asyncio.TimeoutError:
            pass

    raw = b"".join(chunks)
    with open(r"d:\MyLab\myBBS\_debug_raw.bin", "wb") as f:
        f.write(raw)
    text = raw.decode("big5-uao", errors="replace")
    with open(r"d:\MyLab\myBBS\_debug_decoded.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print(f"RAW BYTES: {len(raw)}  DECODED CHARS: {len(text)}")

    # Non-ASCII character census (excluding escape-sequence bytes already stripped below)
    printable = re.sub(r"\x1b[\[\(][^\x07\x1b]{0,32}", "", text)
    non_ascii = Counter(ch for ch in printable if ord(ch) > 0x7F or ch == "\ufffd")
    print("\nNON-ASCII CHARS (top 40):")
    for ch, n in non_ascii.most_common(40):
        print(f"  U+{ord(ch):04X} {ch!r}: {n}")

    escs = Counter(re.findall(r"\x1b[\[\(][^\x07\x1b]{0,32}", text))
    print("\nESCAPE SEQUENCES (top 40):")
    for s, n in escs.most_common(40):
        print(f"  {s!r}: {n}")

    # Show the first screenful of decoded content with escapes visualized
    vis = text[:1500].replace("\x1b", "«ESC»").replace("\r\n", "\n")
    print("\n--- DECODED HEAD (first 1500 chars, ESC visualized) ---")
    print(vis)


asyncio.run(main())
