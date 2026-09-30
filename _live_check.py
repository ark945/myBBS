import sys
sys.stdout.reconfigure(encoding="utf-8")
import asyncio
import websockets
from websockets.sync.client import connect as sync_connect
from app import Big5UAOIncrementalDecoder

print("websockets:", getattr(websockets, "__version__", "?"))
URL = "wss://ws.ptt.cc/bbs"
d = Big5UAOIncrementalDecoder()


def try_variant(tag, **kw):
    try:
        with sync_connect(URL, **kw) as ws:
            ws.send("1\r")
            parts = []
            while True:
                try:
                    msg = ws.recv(timeout=3)
                except Exception:
                    break
                b = msg if isinstance(msg, bytes) else str(msg).encode()
                parts.append(d.decode(b))
                if d._pending:
                    parts.append(d.decode(bytes(d._pending)))
                    d._pending = bytearray()
            text = "".join(parts)
            print(f"[{tag}] 字元 {len(text)} | U+FFFD {text.count(chr(0xfffd))} | 0xFF {text.count(chr(0xff))}")
            for i, ln in enumerate(text.split("\r\n")[:6], 1):
                print(f"  {i}: {ln[:78]}")
    except Exception as e:
        print(f"[{tag}] 失敗: {type(e).__name__}: {e}")


try_variant("subprotocols=['1.1']", subprotocols=["1.1"])
try_variant("both", subprotocols=["1.1"], additional_headers={"Sec-WebSocket-Protocol": "1.1"})
try_variant("+Origin", subprotocols=["1.1"],
            additional_headers={"Origin": "https://term.ptt.cc"})
try_variant("Origin only", additional_headers={"Origin": "https://term.ptt.cc"})

