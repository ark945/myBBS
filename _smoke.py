"""端到端煙霧測試：透過本地 uvicorn 代理取得 PTT 畫面並驗證解碼結果。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import asyncio
import websockets


async def main():
    parts = []
    async with websockets.connect(
        "ws://127.0.0.1:8088/ws",
        subprotocols=["1.1"],
        additional_headers={"Origin": "https://term.ptt.cc"},
    ) as ws:
        try:
            while True:
                parts.append(await asyncio.wait_for(ws.recv(), 3))
        except Exception:
            pass
    txt = "".join(parts)
    print("FRAMES", len(parts), "| CHARS", len(txt), "| U+FFFD", txt.count(chr(0xfffd)),
          "| 0xFF", txt.count("\u00ff"), "| HTTP residue:", "HTTP/1.1" in txt)
    for i, line in enumerate(txt.split("\r\n")[:8], 1):
        print(i, line)


asyncio.run(main())
