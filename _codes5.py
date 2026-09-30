"""列出 PTT 首葉藝術字區所用到字元的碼點與 Big5 來源碼。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"d:\MyLab\myBBS")
from app import Big5UAOIncrementalDecoder
from unicodedata import name as uname

for ch in "¢«d▅▋╲¡¿c▄k＊ª¸£¨¹˙·；：–":
    b = ch.encode("big5-uao", errors="ignore").hex().upper()
    print(f"{ch} | U+{ord(ch):04X} | Big5={b} | {uname(ch)}")
