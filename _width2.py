import sys
sys.stdout.reconfigure(encoding="utf-8")
exec(open(r"d:\MyLab\myBBS\_line_stats.py", encoding="utf-8").read())

# static/app.js 的 registerCharacterWidths 規則（逐條對應）
RANGES2 = [(0x1100, 0x115F), (0x2E80, 0xA4CF), (0xAC00, 0xD7A3),
           (0xF900, 0xFAFF), (0xFE30, 0xFE6F), (0xFF01, 0xFF60), (0xFFE0, 0xFFE6)]


def js_w(line):
    w, i = 0, 0
    while i < len(line):
        c = line[i]
        if c == "\x1b":
            j = i + 1
            while j < len(line) and not ("@" <= line[j] <= "~"):
                j += 1
            i = j + 1
            continue
        o = ord(c)
        if o == 0:
            n = 0
        elif o < 0x2E80:
            n = 1
        else:
            n = 2 if any(a <= o <= b for a, b in [(x[0], x[1]) for x in RANGES2]) else 1
        w += n
        i += 1
    return w


ws = [js_w(x) for x in lines]
print("app.js provider 規則 → 每行寬度:")
print(ws)
print("最大:", max(ws), "| ≤80 的行數:", sum(1 for v in ws if v <= 80), "/", len(ws))



def w1(line):
    w, i = 0, 0
    while i < len(line):
        c = line[i]
        if c == "\x1b":
            j = i + 1
            while j < len(line) and not ("@" <= line[j] <= "~"):
                j += 1
            i = j + 1
            continue
        o = ord(c)
        if 0x2500 <= o <= 0x259F:          # 方塊元素/製表符：PTT 以 1 欄計
            w += 1
        elif (0x1100 <= o <= 0x115F) or (0x3000 <= o <= 0x303E) or (0xFF01 <= o <= 0xFF60) or (0xFE30 <= o <= 0xFE6F):
            w += 2
        else:
            w += 1
        i += 1
    return w


print("變體（U+2500..259F 計 1 欄）:")
print([w1(x) for x in lines[:30]])
print("最大:", max(w1(x) for x in lines))
