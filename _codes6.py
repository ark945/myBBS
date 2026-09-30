"""逐行標出每個符號字元的位次、碼點與名稱（對應 Putty 畫面中的 ? 位置）。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"d:\MyLab\myBBS")
from app import Big5UAOIncrementalDecoder
from unicodedata import name as uname

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
d = Big5UAOIncrementalDecoder()
txt = d.decode(raw)
if d._pending:
    txt += d.decode(bytes(d._pending))

out = []
for i, line in enumerate(txt.split("\n")[:6], 1):
    out.append(f"[{i}] len={len(line)}")
    for j, c in enumerate(line):
        if ord(c) < 0x20 or c == " ":
            continue
        try:
            nm = uname(c)
        except Exception:
            nm = "(no name)"
        out.append(f"    {j:2d} {c} U+{ord(c):04X} big5={c.encode('big5-uao', errors='ignore').hex().upper() or '-'} {nm}")

import io
with io.open(r"d:\MyLab\myBBS\_codes6_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("written", len(out))
