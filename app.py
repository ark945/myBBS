import os
import asyncio
import logging
import codecs
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import websockets
import uao

# Register big5-uao codec mapping
uao.register_uao()

# Fix for big5-uao name normalization in Python 3.9+
try:
    codecs.lookup('big5-uao')
except LookupError:
    def big5_uao_codec_search(encoding):
        if encoding in ('big5_uao', 'big5-uao'):
            try:
                return codecs.lookup('big5uao')
            except LookupError:
                pass
        return None
    codecs.register(big5_uao_codec_search)

def strip_http_header(buf: bytes):
    """剝除串流最開頭的 HTTP 狀態行（只在第一個 frame 出現一次）。

    PTT 閘道第一個 payload 形如 `HTTP/1.1 200 OK` + 空行 + 畫面資料；
    空行可能是 `\\r\\n\\r\\n`（有协商 1.1 子協定）或 `\\n\\n`。
    回傳 (剝除後的 bytes, 是否已完成)。
    """
    for sep in (b"\r\n\r\n", b"\n\n"):
        idx = buf.find(sep)
        if idx != -1:
            return buf[idx + len(sep):], True
    return buf, False


def strip_iac(buf: bytes):
    """位元組層 Telnet IAC 過濾（增量安全）。

    回傳 (過濾後的 bytes, 已消耗的索引)：
      - `FF FB/FC/FD/FE` + 1 option  → 吞 3 bytes
      - `FF FA` … `FF F0`            → 吞至 SE
      - `FF FF`                      → 輸出字面 0xFF
      - 其餘                          → 原樣輸出
    尾端不完整的序列不消耗，留給下一次 decode()。
    """
    out = bytearray()
    i, n = 0, len(buf)
    while i < n:
        b = buf[i]
        if b == 0xFF:
            if i + 1 >= n:
                break                                   # Incomplete: keep tail
            c = buf[i + 1]
            if c in (0xFB, 0xFC, 0xFD, 0xFE):            # WILL/WONT/DO/DONT
                if i + 2 >= n:
                    break
                i += 3
                continue
            if c == 0xFA:                                # SB … SE
                end = buf.find(b"\xff\xf0", i + 2)
                if end == -1:
                    break
                i = end + 2
                continue
            if c == 0xFF:                                # escaped literal 0xFF
                out.append(0xFF)
                i += 2
                continue
            i += 2
            continue
        out.append(b)
        i += 1
    return bytes(out), i


def _complete_pair_len(data: bytes) -> int:
    """回傳「雙字節成對完整」的消耗長度；尾端孤 lead byte 不计入（留待下次）。"""
    i, n = 0, len(data)
    while i < n:
        b = data[i]
        if 0x81 <= b <= 0xFE:
            if i + 1 < n:
                i += 2
            else:
                break                                   # 孤 lead byte，待下一次
        else:
            i += 1
    return i


class Big5UAOIncrementalDecoder:
    """big5-uao 增量解碼器：HTTP 標頭剝除 → IAC 過濾 → 雙字節對齊解碼。

    `uao` 未提供 IncrementalDecoder，因此以單一 `_pending` 保留兩段待補字節：
      1. 不完整的 IAC 序列（`strip_iac` 未消耗的尾端）。
      2. 不完整的雙字節 lead byte（0x81–0xFE）。
    `_header_done` 確保 `HTTP/1.1 200 OK` 狀態行只在第一個 frame 剝除一次。
    """

    def __init__(self):
        self._pending = bytearray()
        self._header_done = False

    def decode(self, new_bytes: bytes) -> str:
        buf = bytes(self._pending) + bytes(new_bytes)
        self._pending = bytearray()

        # 1) HTTP 狀態行只可能出现一次（串流最開頭）
        if not self._header_done:
            buf, self._header_done = strip_http_header(buf)
            if not self._header_done:
                self._pending = bytearray(buf)           # 標頭尚未收全
                return ""

        # 2) 位元組層過濾 IAC，未收完的尾端留待下次
        filt, used = strip_iac(buf)
        tail = bytearray(buf[used:])

        # 3) 雙字節對齊：孤 lead byte 留待下次
        data = filt
        consumed = _complete_pair_len(data)
        self._pending = tail + bytearray(data[consumed:])

        ready = data[:consumed]
        if not ready:
            return ""
        return ready.decode("big5-uao", errors="replace")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myBBS-Proxy")

app = FastAPI(title="myBBS Proxy")

# Config: passcode required to use the proxy (prevents abuse)
PROXY_PASSCODE = os.getenv("PROXY_PASSCODE", "")

# Target BBS instance: "ptt" (official ptt.cc, default) or "ptt2" (批踢踢兔, independent community - NOT a mirror of ptt.cc data)
PTT_TARGETS = {
    "ptt": ("wss://ws.ptt.cc/bbs", "https://term.ptt.cc"),
    "ptt2": ("wss://ws.ptt2.cc/bbs", "https://term.ptt2.cc"),
}
PTT_TARGET = os.getenv("PTT_TARGET", "ptt").lower()
if PTT_TARGET not in PTT_TARGETS:
    logger.warning(f"Unknown PTT_TARGET '{PTT_TARGET}', falling back to 'ptt'.")
    PTT_TARGET = "ptt"

# Verify passcode helper
def verify_passcode(passcode: str) -> bool:
    if not PROXY_PASSCODE:
        return True
    return passcode == PROXY_PASSCODE

@app.get("/api/config")
def get_config():
    """Returns configuration details to the frontend (e.g. whether passcode is enabled)."""
    return {
        "passcode_required": bool(PROXY_PASSCODE)
    }

# WebSocket route for proxying
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, passcode: str = ""):
    # Accept the initial browser connection
    await websocket.accept()

    # Authenticate if passcode is set
    if not verify_passcode(passcode):
        logger.warning(f"Unauthorized access attempt with passcode: {passcode}")
        await websocket.send_text("\r\n\x1b[1;31m[ERROR] 密碼錯誤或未輸入密碼。請在控制台輸入正確密碼！\x1b[0m\r\n")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    logger.info("Client connected and authorized. Connecting to PTT...")
    await websocket.send_text("\x1b[1;36m[System] 正在透過跳板建立與 PTT 的連線...\x1b[0m\r\n")

    ptt_url, ptt_origin = PTT_TARGETS[PTT_TARGET]
    headers = {
        "Origin": ptt_origin,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Connect to PTT WebSocket server (support both older and v14.0+ websockets versions)
        # 必要：Origin 標頭 + 1.1 子協定（缺 Origin 會被閘道回 403）
        try:
            ptt_conn = websockets.connect(ptt_url, subprotocols=["1.1"], additional_headers=headers)
        except TypeError:
            ptt_conn = websockets.connect(ptt_url, subprotocols=["1.1"], extra_headers=headers)

        async with ptt_conn as ptt_ws:
            logger.info("Successfully connected to PTT.")
            await websocket.send_text("\x1b[1;32m[System] 連線成功！正在進入 BBS...\x1b[0m\r\n\r\n")

            # Decoders/Encoders for incremental translation of Big5 (big5-uao) stream
            # Since big5-uao has no built-in codecs incrementaldecoder, we use our custom implementation
            decoder = Big5UAOIncrementalDecoder()

            # Task for forwarding messages from PTT to Client
            async def ptt_to_client():
                try:
                    async for message in ptt_ws:
                        # PTT sends binary packets (Big5 encoded)
                        if isinstance(message, bytes):
                            # Decode binary packet to unicode text incrementally
                            unicode_text = decoder.decode(message)
                            if unicode_text:
                                await websocket.send_text(unicode_text)
                        else:
                            # If for some reason it's already text
                            await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error in ptt_to_client: {e}")
                finally:
                    logger.info("PTT connection closed.")

            # Task for forwarding messages from Client to PTT
            async def client_to_ptt():
                try:
                    while True:
                        # Client browser sends UTF-8 text strings
                        client_msg = await websocket.receive_text()
                        # Encode unicode text back to Big5 bytes
                        big5_bytes = client_msg.encode('big5-uao', errors='ignore')
                        await ptt_ws.send(big5_bytes)
                except WebSocketDisconnect:
                    logger.info("Client browser disconnected.")
                except Exception as e:
                    logger.error(f"Error in client_to_ptt: {e}")

            # Run both tasks concurrently
            await asyncio.gather(
                ptt_to_client(),
                client_to_ptt()
            )

    except websockets.exceptions.ConnectionClosed as ecc:
        logger.warning(f"PTT connection closed unexpectedly: {ecc}")
        await websocket.send_text("\r\n\x1b[1;31m[System] PTT 連線已中斷。\x1b[0m\r\n")
    except Exception as e:
        logger.error(f"Proxy websocket handler error: {e}")
        try:
            await websocket.send_text(f"\r\n\x1b[1;31m[System] 連線錯誤: {str(e)}\x1b[0m\r\n")
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass

# Serve static files for the SPA frontend
# We mount this at "/" and serve files from "/app/static" (in Docker) or "./static" (locally)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Route to serve the main HTML file
@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

# Mount the rest of static files (css, js, etc.)
app.mount("/", StaticFiles(directory=static_dir), name="static")
