"""比較：雙字節配對 vs 逐字節 Latin-1 回退，並列出畫素字元清單。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from unicodedata import name as uname
sys.path.insert(0, r"d:\MyLab\myBBS")
from app import Big5UAOIncrementalDecoder          # 匯入即註冊 big5-uao 對照表

tests = [b"\xa2\x62", b"\xa2", b"\x62", b"\xa2\xa9", b"\xa1\x50", b"\xc4\xa1",
         b"\xa9\x76", b"\xa9\x65", b"\xa9\x64", b"\xb5\x79", b"\xa1\x47"]
for t in tests:
    whole = t.decode("big5-uao", errors="replace")
    parts = [bytes([x]).decode("big5-uao", errors="replace") for x in t]
    print(t.hex(), "→ 整段:", repr(whole), "| 逐字節:", parts)

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
sys.path.insert(0, r"d:\MyLab\myBBS")
from app import Big5UAOIncrementalDecoder
d = Big5UAOIncrementalDecoder()
txt = d.decode(raw)
if d._pending:
    txt += d.decode(bytes(d._pending))
used = sorted({ord(c) for c in txt if c not in "\r\n"})
print("\n使用中的非 ASCII 碼點數:", len(used))
for cp in used:
    if cp < 0x20:
        continue
    try:
        nm = uname(chr(cp))
    except Exception:
        nm = "?"
    print(f"U+{cp:04X} {chr(cp)} x{txt.count(chr(cp)):3d} {nm}")
