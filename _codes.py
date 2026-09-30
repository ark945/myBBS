"""抓取 WS 還原後的文字並寫入 UTF-8 檔，另列出每行碼點寬度加總。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import asyncio
import websockets


def wc(cp):
    if cp == 0 or cp < 0x20:
        return 0
    if cp < 0x7F:
        return 1
    if (0x2500 <= cp <= 0x25FF) or (0x2600 <= cp <= 0x26FF):
        return 1
    if ((0x1100 <= cp <= 0x115F) or (0x2E80 <= cp <= 0xA4CF and cp != 0x303F)
            or (0xAC00 <= cp <= 0xD7A3) or (0xF900 <= cp <= 0xFAFF)
            or (0xFE30 <= cp <= 0xFE6F) or (0xFF00 <= cp <= 0xFF60)
            or (0xFFE0 <= cp <= 0xFFE6)):
        return 2
    return 1


async def main():
    parts = []
    async with websockets.connect(
        "ws://127.0.0.1:8088/ws", subprotocols=["1.1"],
        additional_headers={"Origin": "https://term.ptt.cc"},
    ) as ws:
        try:
            while True:
                parts.append(await asyncio.wait_for(ws.recv(), 3))
        except Exception:
            pass
    txt = "".join(parts)
    open(r"d:\MyLab\myBBS\_ws_dump.txt", "w", encoding="utf-8").write(txt)
    widths = []
    import re
    csi = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[=>]")
    for ln in txt.split("\r\n"):
        widths.append(sum(wc(ord(c)) for c in csi.sub("", ln)))
    print("FRAME", len(parts), "CHAR", len(txt), "LINE", len(widths),
          "MAX", max(widths) if widths else 0, "OVER80", [i for i, w in enumerate(widths, 1) if w > 80])


asyncio.run(main())


