"""比較四種解碼方案在真實 PTT 抓包上的表現。"""
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


def strip_iac(buf: bytes) -> bytes:
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


def report(tag, text):
    n = len(text)
    fffd = text.count("\ufffd")
    print(f"{tag:>34} | 字串長度 {n:5d} | U+FFFD {fffd:3d} | 首行: {text.splitlines()[0][:52] if text else ''}")


# 方案 A：現況 —— 未剋除標頭、未過濾 IAC，直接 big5uao
report("A 現況(無剝除/無過濾)+big5uao", raw.decode("big5-uao", errors="replace"))
# 方案 B：只剝除標頭
report("B 僅剝除 HTTP 標頭+big5uao", body.decode("big5-uao", errors="replace"))
# 方案 C：剝除標頭 + IAC 過濾 + big5uao
filt = strip_iac(body)
report("C 剝除+IAC過濾+big5uao", filt.decode("big5-uao", errors="replace"))
# 方案 D：剝除標頭 + IAC 過濾 + 內建 big5
try:
    report("D 剝除+IAC過濾+內建 big5", filt.decode("big5", errors="replace"))
except Exception as e:
    print("D 失敗:", e)
# 方案 E：剝除標頭 + IAC 過濾 + cp950
try:
    report("E 剝除+IAC過濾+cp950", filt.decode("cp950", errors="replace"))
except Exception as e:
    print("E 失敗:", e)

# 三個 UAO 專屬字形在各 codec 下的結果
print("\n--- 各 codec 對 UAO 字形的支援 ---")
for pair in (b"\xf9\xde", b"\xf9\xe0", b"\xf9\xe2", b"\xff\xf0"):
    for enc in ("big5", "cp950", "big5-uao"):
        try:
            r = pair.decode(enc, errors="replace")
        except Exception as ex:
            r = f"<{ex}>"
        print(f"  {pair.hex()} @{enc:<9} -> {r!r}")

# 內建 incremental decoder 是否可用
print("\n--- 內建 incremental decoder ---")
for enc in ("big5", "cp950", "big5-uao"):
    try:
        d = codecs.getincrementaldecoder(enc)("replace")
        s = d.decode(b"\xc4\xa1\x1b[6n", False) + d.decode(b"\xa2\x7e", True)
        print(f"  {enc:<10} 可用 -> {s!r}")
    except Exception as ex:
        print(f"  {enc:<10} 不可用 -> {ex}")
