import mcp
import os
for root, dirs, files in os.walk(os.path.dirname(mcp.__file__)):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, encoding="utf-8", errors="ignore") as fp:
                data = fp.read()
            if "class Tool" in data:
                print("Found in:", path)