"""檢查行尾形態（CR / CRLF）與幾個疑難字元的來源位元組。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from app import Big5UAOIncrementalDecoder

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
print("raw bytes:", len(raw))
print("CRLF 數量:", raw.count(b"\r\n"))
print("裸 CR 數量:", raw.count(b"\r") - raw.count(b"\r\n"))
print("連續 CRLFCRLF:", raw.count(b"\r\n\r\n"))
print("裸 LF 數量:", raw.count(b"\n") - raw.count(b"\r\n"))
print("前 60 字節:", raw[:60])
# 找 0xA2 / 0xEE 出現的原始位元組上下文
for target in (0xA2, 0xEE, 0xA1):
    idx = raw.find(bytes([target]))
    print(f"0x{target:02X} 首次索引 {idx} 上下文:", raw[max(0, idx-2):idx+4])

d = Big5UAOIncrementalDecoder()
txt = d.decode(raw)
if d._pending:
    txt += d.decode(bytes(d._pending))
print("解碼後字元數:", len(txt))
print("U+FFFD:", txt.count(chr(0xfffd)))
print("單字節 big5 測試:", bytes([0xA2]).decode("big5-uao"), bytes([0xEE]).decode("big5-uao"))
