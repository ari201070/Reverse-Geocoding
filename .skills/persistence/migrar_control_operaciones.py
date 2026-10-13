import sqlite3

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("Creando tabla 'control_operaciones' con integridad referencial...")
cursor.execute("""
CREATE TABLE IF NOT EXISTS control_operaciones (
    foto_id TEXT NOT NULL,
    operacion_id TEXT NOT NULL,
    huella_contenido TEXT NOT NULL CHECK (length(huella_contenido) = 64),
    version_reglas TEXT NOT NULL,
    resultado_json TEXT NOT NULL CHECK (json_valid(resultado_json)),
    registrada_utc TEXT NOT NULL,
    PRIMARY KEY (foto_id, operacion_id),
    FOREIGN KEY (foto_id) REFERENCES photos(id) ON DELETE RESTRICT
);
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_control_operaciones_fecha ON control_operaciones (registrada_utc);")
conn.commit()
conn.close()
print("Tabla e indice creados exitosamente en el catalogo fisico.")
