import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

viajes_dir = r"F:\Fotos_Organizadas\Viajes"

print("--- LISTANDO VIAJES EN F:\\Fotos_Organizadas\\Viajes ---")
if os.path.exists(viajes_dir):
    for v in os.listdir(viajes_dir):
        vp = os.path.join(viajes_dir, v)
        if os.path.isdir(vp):
            sub = os.listdir(vp)
            print(f"Viaje: {v} ({len(sub)} elementos)")
            for s in sub:
                sp = os.path.join(vp, s)
                if os.path.isdir(sp):
                    print(f"   - {s}/ ({len(os.listdir(sp))} archivos)")
                else:
                    print(f"   - {s}")
