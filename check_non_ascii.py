fn = "tests/test_main.py"
with open(fn, "rb") as f:
    for i, raw in enumerate(f.readlines(), start=1):
        if 1 <= i <= 9999:  # adjust range if needed
            s = raw.decode("utf-8", "backslashreplace")
            if r"\x" in s or any(ord(ch) > 127 for ch in s):
                import sys

                sys.stdout.buffer.write(f"{i} {s.rstrip()}\n".encode("utf-8"))
