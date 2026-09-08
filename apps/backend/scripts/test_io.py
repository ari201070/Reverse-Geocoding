import os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

base_dir = r"F:\2025\Octubre\Viaje Familiar de 30 dias por Argentina"
day_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d != '_thumbs'])

d10 = day_dirs[1] # Día 10
files = os.listdir(os.path.join(base_dir, d10))
sample_file = os.path.join(base_dir, d10, files[180])

t0 = time.time()
with open(sample_file, 'rb') as f:
    data = f.read()
dt = time.time() - t0
print(f"Archivo: {files[180]} ({len(data)/1024:.1f} KB) leído en {dt:.3f}s")
