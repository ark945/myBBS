import asyncio, re, sys, unicodedata, codecs
sys.stdout.reconfigure(encoding="utf-8")
import websockets
import uao
uao.register_uao()
try:
    codecs.lookup("big5-uao")
except LookupError:
    def _search(enc):
        if enc in ("big5_uao", "big5-uao"):
            return codecs.lookup("big5uao")
        raise LookupError(enc)
    codecs.register(_search)

async def capture():
    headers = {"User-Agent": "Mozilla/5.0", "Origin": "https://term.ptt.cc"}
    ws = None
    for kw in ("additional_headers", "extra_headers"):
        try:
            ws = await websockets.connect("wss://ws.ptt.cc/bbs", open_timeout=15, **{kw: headers})
            break
        except TypeError:
            continue
    data = bytearray()
    async with ws:
        try:
            while len(data) < 6000:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                if isinstance(msg, bytes):
                    data.extend(msg)
                else:
                    data.extend(msg.encode("utf-8", "replace"))
        except Exception:
            pass
    return bytes(data)

raw = asyncio.run(capture())
open(r"d:\MyLab\myBBS\_ptt_capture.bin", "wb").write(raw)
print("captured", len(raw), "bytes")
m = re.match(rb"HTTP/\S+ \d{3}[^\r\n]*\r\n(?:[^\r\n]*\r\n)*\r\n", raw)
body = raw[m.end():] if m else raw
print("header stripped:", bool(m), "body len:", len(body))
clean = re.sub(rb"\x1b\[[0-9;?]*[A-Za-z]", b"", body)
text = clean.decode("big5", errors="replace")
open(r"d:\MyLab\myBBS\_banner_big5.txt", "w", encoding="utf-8").write(text)
pairs = {}
i = 0
while i < len(clean):
    if clean[i] >= 0x80 and i + 1 < len(clean) and clean[i+1] >= 0x80:
        p = clean[i:i+2]
        try:
            ch5, s5 = p.decode("big5"), "ok"
        except Exception:
            ch5, s5 = "?", "fail"
        try:
            chu, su = p.decode("big5-uao"), "ok"
        except Exception:
            chu, su = "?", "fail"
        pairs[p.hex()] = (ch5, s5, chu, su)
        i += 2
    else:
        i += 1
lines = []
for h in sorted(pairs):
    ch5, s5, chu, su = pairs[h]
    n5 = unicodedata.name(ch5, "") if ch5 != "?" else ""
    nu = unicodedata.name(chu, "") if chu != "?" else ""
    lines.append("%s  big5=U+%04X %r %-26s [%s]   uao=U+%04X %r [%s]" % (
        h, ord(ch5) if ch5 != "?" else 0, ch5, n5[:26], s5,
        ord(chu) if chu != "?" else 0, chu, su))
open(r"d:\MyLab\myBBS\_glyph_report.txt", "w", encoding="utf-8").write("\n".join(lines))
print("pairs:", len(pairs), "-> _glyph_report.txt")
