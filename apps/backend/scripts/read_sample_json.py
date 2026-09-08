import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sample_path = r"F:\copia de los datos de Google\Takeout\Google Fotos\12 de julio de 2017\שוקוהיטה.jpg.supplemental-metadata.json"
try:
    with open(sample_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)
