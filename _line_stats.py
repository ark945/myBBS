import sys
sys.stdout.reconfigure(encoding="utf-8")
import codecs
import uao, uao.b2u
uao.register_uao()
try:
    codecs.lookup("big5-uao")
except LookupError:
    codecs.register(lambda e: codecs.lookup("big5uao") if e in ("big5_uao", "big5-uao") else None)

raw = open("_ptt_capture.bin", "rb").read()


def strip_http(b):
    i = b.find(b"\r\n\r\n")
    return b[i + 4:] if i != -1 else b


def strip_iac(b):
    out = bytearray()
    i = 0
    n = len(b)
    while i < n:
        v = b[i]
        if v == 0xFF:
            out.append(v)
            i += 1
            continue
        if v == 0xFB or v == 0xFC or v == 0xFD or v == 0xFE:
            i += 3
            continue
        if v == 0xFA:
            j = i + 1
            while j + 1 < n and not (b[j] == 0xFF and b[j + 1] == 0xF0):
                j += 1
            i = j + 2
            continue
        out.append(v)
        i += 1
    return bytes(out)


s = strip_iac(strip_http(raw)).decode("big5-uao", "replace")
lines = s.split("\r\n")
print("總行數:", len(lines))
for k in range(6):
    print("第%d行 長度=%2d | %r" % (k + 1, len(lines[k]), lines[k]))
print("\n--- 顯示寬度（跳過 ESC 序列，雙寬字形計 2）---")


def disp_w(line):
    w, i = 0, 0
    while i < len(line):
        ch = line[i]
        if ch == "\x1b":
            j = i + 1
            while j < len(line) and not ("@" <= line[j] <= "~"):
                j += 1
            i = j + 1
            continue
        o = ord(ch)
        w += 2 if (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xFE30 <= o <= 0xFE6F
                   or 0xFF01 <= o <= 0xFF60 or 0xFFE0 <= o <= 0xFFE6) else 1
        i += 1
    return w


for k in range(6):
    print("第%d行 顯示寬度=%3d" % (k + 1, disp_w(lines[k])))
ws = [(disp_w(x), k + 1) for k, x in enumerate(lines)]
print("寬度分布(前8):", sorted(ws, reverse=True)[:8])

from collections import Counter
print("行長度統計:", Counter(len(x) for x in lines).most_common(6))
