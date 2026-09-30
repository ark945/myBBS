import re
raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
m = re.match(rb"HTTP/\S+ \d{3}[^\r\n]*\r\n(?:[^\r\n]*\r\n)*\r\n", raw)
body = raw[m.end():]
def dump(lo, hi, tag):
    print("=== %s  [%d..%d] ===" % (tag, lo, hi))
    for off in range(lo, min(hi, len(body)), 16):
        chunk = body[off:off+16]
        hexs = " ".join("%02x" % b for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print("%04x  %-48s  %s" % (off, hexs, asc))
pos = body.find(b"hacoolman")
print("hacoolman at", pos)
dump(max(0, pos-96), pos+32, "around hacoolman")
i = body.find(b"\x18")
print("first 0x18 at", i)
dump(max(0, i-48), i+48, "around 0x18 control bytes")
