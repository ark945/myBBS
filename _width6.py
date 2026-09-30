"""與 static/app.js 修正後的 wcwidth 完全對照，確認每列 ≤ 80。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import re
from app import Big5UAOIncrementalDecoder

CSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[MP]|\x1b.")
raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
d = Big5UAOIncrementalDecoder()
text = d.decode(raw) + d.decode(bytes(d._pending))


def wcwidth(cp):                       # 1:1 對應 static/app.js
    if cp == 0 or cp < 0x20:
        return 0
    if cp < 0x7F:
        return 1
    if cp < 0xA0:
        return 0
    if ((0x0300 <= cp <= 0x036F) or (0x1AB0 <= cp <= 0x1AFF) or (0x1DC0 <= cp <= 0x1DFF)
            or (0x20D0 <= cp <= 0x20FF) or (0xFE00 <= cp <= 0xFE0F) or (0xFE20 <= cp <= 0xFE2F)
            or cp in (0x200B, 0x200C, 0x200D, 0xFEFF)):
        return 0
    if (0x2500 <= cp <= 0x25FF) or (0x2600 <= cp <= 0x26FF):
        return 1
    if ((0x1100 <= cp <= 0x115F) or (0x2E80 <= cp <= 0xA4CF and cp != 0x303F)
            or (0xAC00 <= cp <= 0xD7A3) or (0xF900 <= cp <= 0xFAFF)
            or (0xFE30 <= cp <= 0xFE6F) or (0xFF00 <= cp <= 0xFF60) or (0xFFE0 <= cp <= 0xFFE6)):
        return 2
    return 1                            # 對照 app.js：Latin-1 Supplement 單寬


rows = text.split("\r\n")
w = [sum(wcwidth(ord(c)) for c in CSI.sub("", r) if ord(c) >= 32) for r in rows]
print("列數", len(rows))
print("逐列寬度", w)
print("最大", max(w), "| 超過 80 的列", [i + 1 for i, v in enumerate(w) if v > 80])
