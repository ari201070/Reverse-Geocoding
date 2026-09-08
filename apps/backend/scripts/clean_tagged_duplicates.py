import os
import sys
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

F_DRIVE_TARGETS = [
    {"folder": r"F:\2011\11-Noviembre", "tag": "_Argentina_2011"},
    {"folder": r"F:\2005\11-Noviembre", "tag": "_Argentina_2011"},
    {"folder": r"F:\2023\05-Mayo", "tag": "_Bosnia_2023"},
    {"folder": r"F:\2023\05-Mayo", "tag": "_Israel_2023"},
    {"folder": r"F:\2010\08-Agosto", "tag": "_Croacia_Montenegro_2010"},
    {"folder": r"F:\2013\08-Agosto", "tag": "_Creta_2013"},
    {"folder": r"F:\2023\04-Abril", "tag": "_Italia_2023"},
    {"folder": r"F:\2015\07-Julio", "tag": "_Eslovenia_2015"},
    {"folder": r"F:\2024\09-Septiembre", "tag": "_Dinamarca_2024"}
]

IMG_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif')

def clean_base_name(filename, tag):
    name, ext = os.path.splitext(filename)
    for t in ["_Argentina_2011", "_Bosnia_2023", "_Croacia_Montenegro_2010", "_Creta_2013", "_Italia_2023", "_Eslovenia_2015", "_Israel_2023", "_Dinamarca_2024"]:
        name = name.replace(t, "").replace(t.upper(), "")
    name = re.sub(r'(_\d+)$', '', name)
    name = re.sub(r'(_dup|_copy|\s\(\d+\))$', '', name, flags=re.IGNORECASE)
    return name.strip()

print("--- INICIANDO SANEAMIENTO RÁPIDO Y SEGURO ---")

for target in F_DRIVE_TARGETS:
    folder = target["folder"]
    tag = target["tag"]
    if not os.path.exists(folder):
        continue
        
    print(f"\nProcesando: {folder} | Tag: {tag}")
    files = [f for f in os.listdir(folder) if f.lower().endswith(IMG_EXTENSIONS)]
    
    groups = {}
    for f in files:
        base = clean_base_name(f, tag)
        if base not in groups:
            groups[base] = []
        groups[base].append(os.path.join(folder, f))
        
    deleted = 0
    kept = 0
    
    for base, paths in groups.items():
        ext = os.path.splitext(paths[0])[1]
        correct_name = f"{base}{tag}{ext}"
        correct_path = os.path.join(folder, correct_name)
        
        # Sort paths: prefer one that already has the tag or shortest path
        paths.sort(key=lambda x: (0 if tag in x else 1, len(x)))
        keeper = paths[0]
        duplicates = paths[1:]
        
        if keeper != correct_path:
            if os.path.exists(correct_path):
                try:
                    os.remove(correct_path)
                except Exception:
                    pass
            try:
                os.rename(keeper, correct_path)
                keeper = correct_path
            except Exception:
                pass
                
        for dup in duplicates:
            try:
                os.remove(dup)
                deleted += 1
            except Exception:
                pass
                
        kept += 1
        
    print(f"Resultado en {folder}: Conservados {kept} | Borrados {deleted}")

print("\n¡Saneamiento completado con éxito!")
