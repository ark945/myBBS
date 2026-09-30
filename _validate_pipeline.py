"""驗證 Big5UAOIncrementalDecoder：整批 vs 分批、U+FFFD 計數、80 欄對齊。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from app import Big5UAOIncrementalDecoder

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()

# 基準：方案 C（剝標頭 + IAC 過濾 + big5-uao），由 _cmp_codecs.py 求得
BASE_LEN, BASE_FFFD = 3978, 0


def run_chunks(chunks):
    d = Big5UAOIncrementalDecoder()
    parts = [d.decode(c) for c in chunks]
    rest = d.decode(bytes(d._pending) + b"\x00"[:0]) if d._pending else ""
    return "".join(parts) + rest


batch = run_chunks([raw])
print(f"整批              : 長度 {len(batch):5d} | U+FFFD {batch.count(chr(0xfffd))}")
for size in (1, 3, 7, 19, 64, 512):
    out = run_chunks([raw[i:i + size] for i in range(0, len(raw), size)])
    print(f"每 {size:>3} bytes 一批 : 長度 {len(out):5d} | U+FFFD {out.count(chr(0xfffd)):2d} "
          f"| 與整批相同 {out == batch}")

print("\n--- 前 6 行 ---")
for k, ln in enumerate(batch.split("\r\n")[:6], 1):
    print(f"{k}: {ln}")

print("\n--- DoD 檢查 ---")
print("長度 == 3978 :", len(batch) == BASE_LEN, len(batch))
print("U+FFFD == 0  :", batch.count(chr(0xfffd)) == BASE_FFFD)
print("無 HTTP 標頭 :", "HTTP/1.1" not in batch)
print("無 ÿ 殘跡    :", "\u00ff" not in batch)
print("含 UAO 字形  :", all(c in batch for c in "╦╠╣"))
