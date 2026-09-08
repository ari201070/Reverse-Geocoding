import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

org_dir = r"F:\Fotos_Organizadas"

print(f"--- CONTENIDO DE {org_dir} ---")
if os.path.exists(org_dir):
    for item in os.listdir(org_dir):
        p = os.path.join(org_dir, item)
        if os.path.isdir(p):
            sub_items = os.listdir(p)
            print(f"[DIR] {item}/ ({len(sub_items)} elementos)")
            for si in sub_items[:10]:
                print(f"    - {si}")
            if len(sub_items) > 10:
                print("    - ...")
        else:
            print(f"[FILE] {item}")
else:
    print("F:\\Fotos_Organizadas no existe.")
