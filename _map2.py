import re, unicodedata, codecs
import uao
uao.register_uao()
try:
    codecs.lookup("big5-uao")
except LookupError:
    def _search(enc):
        if enc in ("big5_uao", "big5-uao"):
            return codecs.lookup("big5uao")
        raise LookupError(enc)
    codecs.register(_search)

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
m = re.match(rb"HTTP/\S+ \d{3}[^\r\n]*\r\n(?:[^\r\n]*\r\n)*\r\n", raw)
body = raw[m.end():] if m else raw
clean = re.sub(rb"\x1b\[[0-9;?]*[A-Za-z]", b"", body)

def info(c):
    if c == "?" or len(c) != 1:
        return (0, "")
    return (ord(c), unicodedata.name(c, ""))

pairs = {}
i = 0
while i < len(clean):
    if clean[i] >= 0x80 and i + 1 < len(clean) and clean[i+1] >= 0x80:
        p = clean[i:i+2]
        try:
            ch5, s5 = p.decode("big5"), "ok"
        except Exception:
            ch5, s5 = "?", "fail"
        try:
            chu, su = p.decode("big5-uao"), "ok"
        except Exception:
            chu, su = "?", "fail"
        pairs[p.hex()] = (ch5, s5, chu, su)
        i += 2
    else:
        i += 1

lines = []
for h in sorted(pairs):
    ch5, s5, chu, su = pairs[h]
    o5, n5 = info(ch5)
    ou, nu = info(chu)
    lines.append("%s big5=U+%04X %r %-24s [%s] uao=U+%04X %r [%s]" % (h, o5, ch5, n5[:24], s5, ou, chu, su))
open(r"d:\MyLab\myBBS\_glyph_report.txt", "w", encoding="utf-8").write("\n".join(lines))
print("pairs:", len(pairs))
