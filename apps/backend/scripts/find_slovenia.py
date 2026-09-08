import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

for root, dirs, files in os.walk(r"F:\\"):
    for d in dirs:
        if "סלב" in d or "slo" in d.lower() or "esl" in d.lower():
            print(os.path.join(root, d))
