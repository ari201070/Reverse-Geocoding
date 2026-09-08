import os
import sys
import io
import hashlib
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

TRAVEL_MATRIX = [
    {"name": "Argentina_2011", "path": r"F:\2005\11-Noviembre", "tag": "_Argentina_2011"},
    {"name": "Bosnia_2023", "path": r"F:\2023\05-Mayo", "tag": "_Bosnia_2023"},
    {"name": "Croacia_Montenegro_2010", "path": r"F:\2010\08-Agosto", "tag": "_Croacia_Montenegro_2010"},
    {"name": "Creta_2013", "path": r"F:\2013\08-Agosto", "tag": "_Creta_2013"},
    {"name": "Italia_2023", "path": r"F:\2023\04-Abril", "tag": "_Italia_2023"},
    {"name": "Eslovenia_2015", "path": r"F:\2015\07-Julio", "tag": "_Eslovenia_2015"},
    {"name": "Israel_2023", "path": r"F:\2023\05-Mayo", "tag": "_Israel_2023"},
    {"name": "Dinamarca_2024", "path": r"F:\2024\09-Septiembre", "tag": "_Dinamarca_2024"},
]

def clean_base_name(filename, tag):
    ext = os.path.splitext(filename)[1]
    name = os.path.splitext(filename)[0]
    
    all_tags = [t["tag"] for t in TRAVEL_MATRIX]
    for t in all_tags:
        name = name.replace(t, "")
        
    name = re.sub(r'(_dup)+$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'(_copy)+$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'(_\d+)+$', '', name)
    
    return f"{name.strip()}{tag}{ext}"

print("--- DEDUPLICACIÓN RÁPIDA POR TAMAÑO Y NOMBRE CON TAGGING LIMPIO ---")
summary_report = []

for trip in TRAVEL_MATRIX:
    folder = trip["path"]
    tag = trip["tag"]
    name = trip["name"]
    
    if not os.path.exists(folder):
        continue
        
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.webp', '.dng'))]
    total_analyzed = len(files)
    
    size_groups = {}
    for f in files:
        fp = os.path.join(folder, f)
        try:
            sz = os.path.getsize(fp)
        except Exception:
            sz = 0
        if sz not in size_groups:
            size_groups[sz] = []
        size_groups[sz].append(fp)
            
    deleted_count = 0
    survivors_count = 0
    
    for sz, group in size_groups.items():
        group.sort(key=lambda x: (0 if tag in x else 1, len(os.path.basename(x))))
        keeper = group[0]
        duplicates = group[1:]
        
        dirname, fname = os.path.dirname(keeper), os.path.basename(keeper)
        desired_name = clean_base_name(fname, tag)
        desired_path = os.path.join(dirname, desired_name)
        
        if os.path.abspath(keeper) != os.path.abspath(desired_path):
            if not os.path.exists(desired_path):
                os.rename(keeper, desired_path)
                keeper = desired_path
            else:
                try:
                    os.remove(keeper)
                    deleted_count += 1
                    survivors_count += 1
                    continue
                except Exception:
                    pass
                    
        for dup in duplicates:
            try:
                os.remove(dup)
                deleted_count += 1
            except Exception:
                pass
                
        survivors_count += 1

    summary_report.append({
        "name": name,
        "path": folder,
        "total": total_analyzed,
        "deleted": deleted_count,
        "survivors": survivors_count
    })
    print(f"Viaje: {name:<25} | Analizados: {total_analyzed:<5} | Eliminados: {deleted_count:<5} | Sobrevivientes: {survivors_count:<5}")

print("\n" + "=" * 80)
print(f"{'Viaje':<25} | {'Carpeta Procesada':<25} | {'Analizados':<10} | {'Eliminados':<10} | {'Sobrevivientes':<12}")
print("-" * 90)
for r in summary_report:
    print(f"{r['name']:<25} | {r['path']:<25} | {r['total']:<10} | {r['deleted']:<10} | {r['survivors']:<12}")
print("=" * 80)
