import sys
sys.stdout.reconfigure(encoding="utf-8")
import uao
import uao.b2u as m2u
import uao.u2b as m2b

print("b2u 模組成員:", [n for n in dir(m2u) if not n.startswith("_")][:10])
print("u2b 模組成員:", [n for n in dir(m2b) if not n.startswith("_")][:10])

f = getattr(m2u, "convert", None) or getattr(m2u, "decode", None) or getattr(m2u, "b2u", None)
g = getattr(m2b, "convert", None) or getattr(m2b, "decode", None) or getattr(m2b, "u2b", None)
print("b2u 函式:", f, "| u2b 函式:", g)
if f:
    print("a7f4 f9de ->", repr(f(b"\xa7\xf4\xf9\xde")))
    print("a11b ->", repr(f(b"\xa1\x1b")), "| a8 20 ->", repr(f(b"\xa8 ")))
    print("單 byte c4 ->", repr(f(b"\xc4")), "| NUL ->", repr(f(b"\x00")))
if g:
    print("u2b(纂) ->", repr(g(chr(0x7E82))))
