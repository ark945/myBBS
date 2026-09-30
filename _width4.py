"""最終校驗：(A) 逐行顯示寬度（正確 CSI 正則）；(B) 兩連線模式下 frame 型別與標頭位置。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import re
from app import Big5UAOIncrementalDecoder

out = []
raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
d = Big5UAOIncrementalDecoder()
text = d.decode(raw) + d.decode(bytes(d._pending))
out.append(f"總字元 {len(text)} | U+FFFD {text.count(chr(0xfffd))} | 0xFF {text.count(chr(0xff))}")

CSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[MP]|\x1b.")


def w_provider(ch):
    """對照 static/app.js registerCharacterWidths 的雙寬範圍。"""
    o = ord(ch)
    dbl = ((0x1101 <= o <= 0x115F) or (0x2E80 <= o <= 0xA4CF and o != 0x303F)
           or (0xAC00 <= o <= 0xD7A3) or (0xF900 <= o <= 0xFAFF)
           or (0xFE30 <= o <= 0xFE6F) or (0xFF00 <= o <= 0xFF60) or (0xFFE0 <= o <= 0xFFE6))
    return 2 if dbl else 1


rows = text.split("\r\n")
widths = []
for r in rows:
    vis = CSI.sub("", r)
    widths.append(sum(w_provider(c) for c in vis if ord(c) >= 32))
out.append(f"行數 {len(rows)} | 寬度序列 {widths}")
out.append(f"最大值 {max(widths)} | 非零最小 {min([x for x in widths if x])} | 零寬行 "
           f"{sum(1 for x in widths if x == 0)}")
out.append("逐行: " + " | ".join(f"{i+1}={widths[i]}" for i in range(len(widths))))

open(r"d:\MyLab\myBBS\_w4.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")

# (B) frame 型別
import asyncio
import websockets

HDR = {"Origin": "https://term.ptt.cc"}


async def probe(tag, **kw):
    async with websockets.connect("wss://ws.ptt.cc/bbs", **kw) as ws:
        await ws.send("1\r")
        kinds = []
        try:
            while len(kinds) < 3:
                m = await asyncio.wait_for(ws.recv(), timeout=3)
                b = m if isinstance(m, bytes) else str(m).encode("latin-1", "replace")
                kinds.append((type(m).__name__, len(b), b[:22]))
        except asyncio.TimeoutError:
            pass
        print(tag, kinds)


asyncio.run(probe("with subprotocol 1.1:", subprotocols=["1.1"], additional_headers=HDR))
asyncio.run(probe("without subprotocol  :", additional_headers=HDR))
