"""找出讓 34 列全部 ≤80 的最小寬度規則。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import re
from app import Big5UAOIncrementalDecoder

CSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[MP]|\x1b.")
raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
d = Big5UAOIncrementalDecoder()
text = d.decode(raw) + d.decode(bytes(d._pending))
rows = [CSI.sub("", r) for r in text.split("\r\n")]

DOUBLE = [(0x1100, 0x115F), (0x2E80, 0xA4CF), (0xAC00, 0xD7A3), (0xF900, 0xFAFF),
          (0xFE30, 0xFE6F), (0xFF00, 0xFF60), (0xFFE0, 0xFFE6)]


def wcwidth(cp):
    if cp == 0 or cp < 0x20:
        return 0
    if cp < 0x7F:
        return 1
    if cp < 0xA0:
        return 1                       # 0x7F..0x9F：控制字元，不佔格
    if (0x2500 <= cp <= 0x25FF) or (0x2600 <= cp <= 0x26FF):
        return 1                       # 方塊/區塊/幾何
    if cp == 0x3000:
        return 2
    for lo, hi in DOUBLE:
        if lo <= cp <= hi and cp != 0x303F:
            return 2
    return 1                           # 其餘（含 U+02B0..0x02FF 等修飾符號）


widths = [sum(wcwidth(ord(c)) for c in r) for r in rows]
print("逐列", widths)
print("最大", max(widths), "| 超過 80:", [i + 1 for i, v in enumerate(widths) if v > 80])

# 逐字元貢獻：找出 16/19 列中造成超寬的字元
for idx in (15, 18, 20, 26):
    r = rows[idx]
    print(f"列{idx+1} 寬 {widths[idx]} | 字元數 {len(r)}")
    print("   ", [(hex(ord(c)), wcwidth(ord(c)), c) for c in r if ord(c) >= 0xA0][:30])
