"""以 static/app.js 實際的 wcwidth 規則 vs 精簡規則，逐列比較顯示寬度。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import re
from app import Big5UAOIncrementalDecoder

CSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[MP]|\x1b.")
raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
d = Big5UAOIncrementalDecoder()
text = d.decode(raw) + d.decode(bytes(d._pending))


def w_js(cp):
    """完全比照 static/app.js 的 provider。"""
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
    return 2


def w_ref(cp):
    """精簡：方塊/區塊字元（U+2000-206F, U+2500-257F 等）計 1，其餘漢字全形計 2。"""
    if w_js(cp) == 0:
        return 0
    if (0x1100 <= cp <= 0x115F) or (0x2E80 <= cp <= 0x33FF and cp != 0x303F) \
       or (0x4E00 <= cp <= 0x9FFF) or (0xAC00 <= cp <= 0xD7A3) \
       or (0xF900 <= cp <= 0xFAFF) or (0xFE30 <= cp <= 0xFE6F) \
       or (0xFF00 <= cp <= 0xFF60) or (0xFFE0 <= cp <= 0xFFE6):
        return 2
    return 1


rows = text.split("\r\n")
a = [sum(w_js(ord(c)) for c in CSI.sub("", r) if ord(c) >= 32) for r in rows]
b = [sum(w_ref(ord(c)) for c in CSI.sub("", r) if ord(c) >= 32) for r in rows]
print(f"列數 {len(rows)}")
print("app.js 規則 :", a)
print("最大", max(a), "| >80 的列", [i + 1 for i, v in enumerate(a) if v > 80])
print("精簡規則    :", b)
print("最大", max(b), "| >80 的列", [i + 1 for i, v in enumerate(b) if v > 80])
