import sys
sys.stdout.reconfigure(encoding="utf-8")
t = open(r"d:\MyLab\myBBS\_pttweb_bundle.js", encoding="utf-8", errors="replace").read()
for key in ["UAO init listener", "255:", "getRowText", "cols", "rows"]:
    i = t.find(key)
    print("==", repr(key), "@", i)
    if i != -1:
        print(t[max(0, i - 300):i + 200].replace("\n", " | "))
    print()
