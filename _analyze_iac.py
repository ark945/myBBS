"""診斷：模擬「HTTP 標頭剝除 + Telnet IAC 狀態機 + Big5 解碼」三段式管線。"""
import sys, codecs
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

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()

# --- 現況：直接 big5-uao 解碼 (app.py 目前做法) ---
cur = raw.decode("big5-uao", errors="replace")
print("=== 現況解碼前 6 行 ===")
for ln in cur.splitlines()[:6]:
    print(repr(ln))

# --- 步驟 1：剝除 HTTP 標頭 ---
i = raw.find(b"\r\n\r\n")
body = raw[i + 4:]
print("\nHTTP 標頭長度:", i + 4, repr(raw[:i + 4]))

# --- 步驟 2：Telnet IAC 狀態機過濾 ---
NAMES = {240: "SE", 241: "NOP", 250: "SB", 251: "WILL", 252: "WONT",
         253: "DO", 254: "DONT", 255: "IAC"}
out = bytearray()
k = 0
n = len(body)
print("\n=== IAC 序列清單 ===")
while k < n:
    b = body[k]
    if b == 0xFF and k + 1 < n:
        c = body[k + 1]
        if c in (251, 252, 253, 254) and k + 2 < n:
            print(f"  @{k}: IAC {NAMES[c]} option={body[k+2]}")
            k += 3
        elif c == 250:  # SB
            end = body.find(b"\xff\xf0", k + 2)
            end = end if end != -1 else n
            print(f"  @{k}: IAC SB {bytes(body[k+2:end])} IAC SE")
            k = end + 2
        elif c == 255:  # IAC IAC -> 字面 0xFF
            out.append(0xFF)
            print(f"  @{k}: IAC IAC (字面 FF)")
            k += 2
        else:
            print(f"  @{k}: IAC {NAMES.get(c, c)}")
            k += 2
    else:
        out.append(b)
        k += 1

# --- 步驟 3：Big5-UAO 解碼 ---
text = bytes(out).decode("big5-uao", errors="replace")
print("\n=== 過濾後解碼前 20 行 ===")
for ln in text.splitlines()[:20]:
    print(ln.replace("\x1b", "«E»"))

print("\n字串總長:", len(text), " U+FFFD 數:", text.count("\ufffd"))
