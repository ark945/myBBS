import sys
sys.stdout.reconfigure(encoding="utf-8")
import uao
print("b2u('纂╦'):", repr(uao.b2u(b"\xa7\xf4\xf9\xde")))
print("u2b('纂'):", uao.u2b("\u7e82"))
print("b2u_table 筆數:", len(uao.b2u_table))
print("u2b_table 筆數:", len(uao.u2b_table))
print("含 f9de:", 0xF9DE in uao.b2u_table, "含 ffe2:", 0xFFE2 in uao.b2u_table)
# 尾 byte 小於 0x40 的情況（例：lead + ESC / lead + space）
print("a11b ->", repr(uao.b2u(b"\xa1\x1b")), "| a820 ->", repr(uao.b2u(b"\xa8 ")))
print("單 byte 0xc4 ->", repr(uao.b2u(b"\xc4")))
print("NUL ->", repr(uao.b2u(b"\x00")))
