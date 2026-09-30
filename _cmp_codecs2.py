"""補充測試：uao 直解是否支援分批/尾字元、以及各 codec 失敗字元清單。"""
import sys, codecs
sys.stdout.reconfigure(encoding="utf-8")
import uao
uao.register_uao()
try:
    codecs.lookup("big5-uao")
except LookupError:
    codecs.register(lambda e: codecs.lookup("big5uao") if e in ("big5_uao", "big5-uao") else None)

raw = open(r"d:\MyLab\myBBS\_ptt_capture.bin", "rb").read()
i = raw.find(b"\r\n\r\n")
body = raw[i + 4:]


def strip_iac(buf):
    out = bytearray()
    k, n = 0, len(buf)
    while k < n:
        b = buf[k]
        if b == 0xFF and k + 1 < n:
            c = buf[k + 1]
            if c in (251, 252, 253, 254):
                k += 3 if k + 2 < n else 2
            elif c == 250:
                end = buf.find(b"\xff\xf0", k + 2)
                k = (end if end != -1 else n) + 2
            elif c == 255:
                out.append(0xFF)
                k += 2
            else:
                k += 2
        else:
            out.append(b)
            k += 1
    return bytes(out)


filt = strip_iac(body)

print("=== 1. uao 直解：分批是否一致 ===")
whole = filt.decode("big5-uao", errors="replace")
print("整批 decode 長度:", len(whole), "FFFD:", whole.count("\ufffd"))
# 模擬逐 frame 送（每 7 bytes 一切），观察 FFFD 數量是否變化
acc, pos = [], 0
while pos < len(filt):
    acc.append(filt[pos:pos + 7].decode("big5-uao", errors="replace"))
    pos += 7
chunked = "".join(acc)
print("每 7 bytes 切批 decode 長度:", len(chunked), "FFFD:", chunked.count("\ufffd"))
print("兩種切法是否相同:", whole == chunked)
# 半個雙字元（尾 byte 為 lead byte）
print("單 bytes 切法 FFFD 統計（每 1 byte）:",
      "".join(filt[j:j+1].decode("big5-uao", errors="replace") for j in range(0, len(filt), 1)).count("\ufffd"))

print("\n=== 2. uao decode 是否接受第二參數(final) ===")
try:
    print("uao.decode(b'\\xc4', False) ->", repr(uao.decode(b"\xc4", False)))
except Exception as e:
    print("uao.decode 第二參數異常:", type(e).__name__, e)

print("\n=== 3. 各 codec 失敗的雙字元組合（前 15 個） ===")
for enc in ("big5", "cp950", "big5-uao"):
    bad = []
    k = 0
    while k < len(filt):
        b = filt[k]
        if 0x81 <= b <= 0xFE and k + 1 < len(filt):
            pair = filt[k:k+2]
            t = pair.decode(enc, errors="replace")
            if "\ufffd" in t:
                bad.append(pair.hex())
            k += 2
        else:
            k += 1
    uniq = sorted(set(bad))
    print(f"  {enc:<10} 失敗對數 {len(bad):4d} 去重後 {len(uniq):3d} -> {uniq[:15]}")
