import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import ollama, base64, json, os, time

VOUCHER_DIR = "data/vouchers/2026-09"
FILES = [
    "20261009_142606.jpg", "20261009_142650.jpg", "20261009_142726.jpg",
    "20261009_142802.jpg", "20261009_142908.jpg", "20261009_142942.jpg",
    "20261009_143022.jpg", "20261009_143330.jpg"
]

PROMPT = """Lee el texto de este ticket. Devuelve solo JSON sin explicaciones:
{"supplier":"empresa","route":"origen -> destino","date":"DD/MM/AAAA","time":"HH:MM","train_number":"tren","price":"tarifa EUR","confirmation_code":"codigo","ticket_type":"tipo"}"""

results = {}
for fn in FILES:
    img_path = os.path.join(VOUCHER_DIR, fn)
    if not os.path.exists(img_path):
        print(f"SKIP {fn}: no existe", flush=True)
        continue
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    print(f"Procesando {fn}...", flush=True)
    t0 = time.time()
    try:
        r = ollama.generate(model="moondream:latest", prompt=PROMPT, images=[img_b64], options={"num_predict": 200, "temperature": 0})
        elapsed = time.time() - t0
        print(f"  {fn}: {elapsed:.1f}s -> {r['response'][:200]}", flush=True)
        results[fn] = {"raw": r["response"], "elapsed": elapsed}
    except Exception as e:
        print(f"  {fn}: ERROR {str(e)[:200]}", flush=True)
        results[fn] = {"raw": None, "error": str(e)}

with open("ocr_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nTotal: {len(results)} procesados. Guardado en ocr_results.json", flush=True)
