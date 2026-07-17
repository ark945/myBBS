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

class Big5UAOIncrementalDecoder:
    """
    A custom incremental decoder wrapper for big5-uao.
    Since the uao package does not implement the incrementaldecoder interface,
    this class buffers split double-byte characters manually.
    """
    def __init__(self):
        self.buffer = bytearray()

    def decode(self, new_bytes: bytes) -> str:
        self.buffer.extend(new_bytes)
        n = len(self.buffer)
        if n == 0:
            return ""
            
        i = 0
        while i < n:
            b = self.buffer[i]
            if 0x81 <= b <= 0xfe:
                i += 2
            else:
                i += 1
                
        if i == n:
            valid_bytes = self.buffer
            self.buffer = bytearray()
        else:
            valid_bytes = self.buffer[:-1]
            self.buffer = bytearray([self.buffer[-1]])
            
        return valid_bytes.decode('big5-uao', errors='replace')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myBBS-Proxy")

app = FastAPI(title="myBBS Proxy")

# Config: passcode required to use the proxy (prevents abuse)
PROXY_PASSCODE = os.getenv("PROXY_PASSCODE", "")

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

    ptt_url = "wss://ws.ptt.cc/bbs"
    headers = {
        "Origin": "https://term.ptt.cc",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Connect to PTT WebSocket server (support both older and v14.0+ websockets versions)
        try:
            ptt_conn = websockets.connect(ptt_url, additional_headers=headers)
        except TypeError:
            ptt_conn = websockets.connect(ptt_url, extra_headers=headers)

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
