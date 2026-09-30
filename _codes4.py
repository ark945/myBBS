"""列出符號字元的 Big5 雙字節碼，並展示一條藝術字行的原始位元組與解碼對照。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"d:\MyLab\myBBS")
from app import Big5UAOIncrementalDecoder

for ch in "¢ª¡î¶¿·˙◢◣◤◥▃█–《》":
    try:
        print(f"{ch}  U+{ord(ch):04X}  Big5={ch.encode('big5-uao').hex().upper()}")
    except Exception as e:
        print(ch, "ERR", e)

print("\n-- 雙字節對照 --")
for pair in (b"\xa1\x50", b"\xa2\xa9", b"\xa1\x46", b"\xa1\x47"):
    print(pair.hex().upper(), "→", pair.decode("big5-uao", errors="replace"))

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
seg = raw[61:100]
print("\n原始 61..99:", " ".join(f"{b:02X}" for b in seg))
d = Big5UAOIncrementalDecoder()
print("解碼:", repr(d.decode(seg)))
