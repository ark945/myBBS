import sys
sys.stdout.reconfigure(encoding="utf-8")
import uao
from uao.b2u import b2u_table
from uao.u2b import u2b_table
ks = list(b2u_table.items())[:5]
print("b2u_table 型別:", type(b2u_table), "筆數:", len(b2u_table))
print("b2u_table 前 5 筆:", ks)
print("0xF9DE ->", b2u_table.get(0xF9DE), "| 0xA1BF ->", b2u_table.get(0xA1BF))
print("u2b_table 前 3 筆:", list(u2b_table.items())[:3])
print("u2b_table 筆數:", len(u2b_table))
# 單字元(<0x100)是否也在表內
print("0x41 in b2u_table:", 0x41 in b2u_table, "0x00 in b2u_table:", 0x00 in b2u_table)
print("0xFF in b2u_table:", 0xFF in b2u_table)
