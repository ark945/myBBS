import sys, re
sys.stdout.reconfigure(encoding="utf-8")
exec(open(r"d:\MyLab\myBBS\_line_stats.py", encoding="utf-8").read())

pat = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
out = []
for k in (0, 12, 20, 29, 32, 33):
    s = lines[k]
    vis = pat.sub("", s)
    out.append("行%2d | raw=%3d | 可見字元=%3d | 顯示寬度=%3d" % (k + 1, len(s), len(vis), disp_w(vis)))
open(r"d:\MyLab\myBBS\_w3.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
