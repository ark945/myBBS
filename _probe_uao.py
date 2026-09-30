import uao, inspect

print("VER:", getattr(uao, "__version__", None))
names = [n for n in dir(uao) if not n.startswith("_")]
print("DIR:", names)
for n in ("BBS", "BBSThread", "BBSPost"):
    obj = getattr(uao, n, None)
    print(f"--- {n}: {obj}")
    if obj is not None and inspect.isclass(obj):
        try:
            sig = inspect.signature(obj.__init__)
            print("  __init__:", sig)
        except (ValueError, TypeError) as e:
            print("  __init__ err:", e)
        for m in dir(obj):
            if not m.startswith("_"):
                try:
                    ms = inspect.signature(getattr(obj, m))
                    print(f"  {m}{ms}")
                except (ValueError, TypeError):
                    pass
