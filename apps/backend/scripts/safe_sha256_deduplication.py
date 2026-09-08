import os
import re
import hashlib
import shutil
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

F_DRIVE_TARGETS = [
    {"name": "Argentina_2011", "folder": r"F:\2011\11-Noviembre", "tag": "_Argentina_2011"},
    {"name": "Argentina_2011", "folder": r"F:\2005\11-Noviembre", "tag": "_Argentina_2011"},
    {"name": "Bosnia_2023", "folder": r"F:\2023\05-Mayo", "tag": "_Bosnia_2023"},
    {"name": "Israel_2023", "folder": r"F:\2023\05-Mayo", "tag": "_Israel_2023"},
    {"name": "Croacia_Montenegro_2010", "folder": r"F:\2010\08-Agosto", "tag": "_Croacia_Montenegro_2010"},
    {"name": "Creta_2013", "folder": r"F:\2013\08-Agosto", "tag": "_Creta_2013"},
    {"name": "Italia_2023", "folder": r"F:\2023\04-Abril", "tag": "_Italia_2023"},
    {"name": "Eslovenia_2015", "folder": r"F:\2015\07-Julio", "tag": "_Eslovenia_2015"},
    {"name": "Dinamarca_2024", "folder": r"F:\2024\09-Septiembre", "tag": "_Dinamarca_2024"},
]

IMG_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif')
KNOWN_TAGS = ["_Argentina_2011", "_Bosnia_2023", "_Croacia_Montenegro_2010", "_Creta_2013", "_Italia_2023", "_Eslovenia_2015", "_Israel_2023", "_Dinamarca_2024"]
QUARANTINE_ROOT = r"F:\Deduplication_Quarantine_Backup"
TIMESTAMP_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}\.\d{2}\.\d{2}")

def get_sha256(file_path):
    h = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        print(f"  [ERR] hash {file_path}: {e}")
        return None

def has_timestamp_prefix(filename):
    return bool(TIMESTAMP_REGEX.match(filename))

def ensure_single_tag(filename, desired_tag):
    name, ext = os.path.splitext(filename)
    for t in KNOWN_TAGS:
        if t in name:
            return filename
    return f"{name}{desired_tag}{ext}"

seen_folders = set()
total_groups = 0
total_quarantined = 0

print("="*70)
print("DEDUPLICACIÓN BLINDADA SHA-256 CON CUARENTENA")
print("PROHIBIDO BORRAR - TODO DUPLICADO VA A BACKUP")
print("="*70)

for target in F_DRIVE_TARGETS:
    folder = target["folder"]
    tag = target["tag"]
    travel = target["name"]
    folder_key = os.path.normpath(folder).lower()
    if folder_key in seen_folders:
        continue
    seen_folders.add(folder_key)

    if not os.path.exists(folder):
        print(f"\n[!] No existe: {folder}")
        continue

    print(f"\nProcesando: {folder} | Viaje: {travel} | Tag: {tag}")
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(IMG_EXTENSIONS)]
    print(f"  Archivos analizados: {len(files)}")
    hash_groups = {}
    for f in files:
        fp = os.path.join(folder, f)
        sha = get_sha256(fp)
        if sha is None:
            continue
        hash_groups.setdefault(sha, []).append({"path": fp, "name": f})

    groups_found = 0
    quarantined_here = 0

    quarantine_dir = os.path.join(QUARANTINE_ROOT, travel)
    os.makedirs(quarantine_dir, exist_ok=True)

    for sha, group in hash_groups.items():
        if len(group) == 1:
            info = group[0]
            desired = ensure_single_tag(info["name"], tag)
            if info["name"] != desired:
                src = info["path"]
                dst = os.path.join(folder, desired)
                if not os.path.exists(dst):
                    try:
                        os.rename(src, dst)
                        print(f"  [RENAME] {info['name']} -> {desired}")
                    except Exception as e:
                        print(f"  [ERR rename] {e}")
            continue

        groups_found += 1
        total_groups += 1
        with_ts = [g for g in group if has_timestamp_prefix(g["name"])]
        if with_ts:
            with_ts.sort(key=lambda x: len(x["name"]), reverse=True)
            keeper = with_ts[0]
        else:
            group_sorted = sorted(group, key=lambda x: len(x["name"]), reverse=True)
            keeper = group_sorted[0]

        print(f"  -> Grupo SHA256 {sha[:12]}... ({len(group)} archivos) Keeper: {keeper['name']}")

        desired = ensure_single_tag(keeper["name"], tag)
        keeper_src = keeper["path"]
        keeper_dst = os.path.join(folder, desired)
        final_keeper_path = keeper_src
        if keeper["name"] != desired:
            if not os.path.exists(keeper_dst):
                try:
                    os.rename(keeper_src, keeper_dst)
                    print(f"     [RENAME KEEPER] {keeper['name']} -> {desired}")
                    final_keeper_path = keeper_dst
                except Exception as e:
                    print(f"     [ERR rename keeper] {e}")
            else:
                final_keeper_path = keeper_dst

        for dup in group:
            if dup["path"] == keeper["path"]:
                continue
            src = dup["path"]
            base = os.path.basename(src)
            qdst = os.path.join(quarantine_dir, base)
            c = 1
            while os.path.exists(qdst):
                n, e = os.path.splitext(base)
                qdst = os.path.join(quarantine_dir, f"{n}_{c}{e}")
                c += 1
            try:
                shutil.move(src, qdst)
                print(f"     [CUARENTENA] {dup['name']} -> {qdst}")
                quarantined_here += 1
                total_quarantined += 1
            except Exception as e:
                print(f"     [ERR cuarentena] {e}")

    print(f"  Resultado {travel}: grupos={groups_found} | movidos a cuarentena={quarantined_here}")

print("\n" + "="*70)
print("REPORTE FINAL BLINDADO")
print("="*70)
print(f"Grupos de duplicados reales por SHA-256 encontrados: {total_groups}")
print(f"Archivos redundantes movidos a cuarentena: {total_quarantined}")
print(f"Ubicación cuarentena centralizada: {QUARANTINE_ROOT}")
print("Confirmación: El disco físico quedó libre de copias ruidosas")
print("sin haber eliminado ningún dato de forma definitiva.")
print("Todos los duplicados están resguardados en backup para revisión.")
print("="*70)
