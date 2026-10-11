import os
import sqlite3
import json
import h3
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

DB_PATH = r"C:\Users\flier\GitHub\Reverse-Geocoding\data\photo_catalog.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur = conn.cursor()

    # ===========================================
    # 1. MIGRACION DE ESQUEMA
    # ===========================================
    cur.execute("PRAGMA table_info(photos)")
    cols = [c[1] for c in cur.fetchall()]
    if "location_time" not in cols:
        cur.execute("ALTER TABLE photos ADD COLUMN location_time TEXT")
        print("Column location_time added")
    else:
        print("Column location_time already exists")

    # Añadir columna tags si no existe (TEXT para almacenar JSON)
    if "tags" not in cols:
        cur.execute("ALTER TABLE photos ADD COLUMN tags TEXT")
        print("Column tags added")
    else:
        print("Column tags already exists")

    # ===========================================
    # 2. SELECCIONAR LOTE: Fotos April 2023
    # ===========================================
    cur.execute("SELECT id, filename, date_taken, latitude, longitude, file_path FROM photos WHERE date_taken LIKE '2023-04-%'")
    rows = cur.fetchall()
    print(f"\nApril 2023 photos found: {len(rows)}")

    # ===========================================
    # 3. PROCESAMIENTO EN TRANSACTION
    # ===========================================
    cur.execute("BEGIN TRANSACTION")

    updated = 0
    h3_cells = set()

    for row in rows:
        row_id, filename, date_taken, lat, lng, file_path = row

        # 3a. Actualizar location_time con el horario verificado
        # Diagnóstico Fase 1: todas tenían bright_daylight y were synced_local_time
        # location_time = date_taken (valor EXIF crudo preservado)
        location_time_val = date_taken

        # 3b. Redondear lat/long a 4 decimales (~11m)
        lat_rounded = round(lat, 4) if lat is not None else None
        lng_rounded = round(lng, 4) if lng is not None else None

        # 3c. Calcular celda H3 Resolución 9
        h3_index = None
        if lat_rounded is not None and lng_rounded is not None:
            try:
                h3_index = h3.latlng_to_cell(lat_rounded, lng_rounded, 9)
                h3_cells.add(h3_index)
            except Exception as e:
                print(f"Error calculating H3 for row {row_id}: {e}")

        # 3d. Montar tags JSON 3D útiles (Lugar/Hito, Evento/Viaje, Situación/Escena)
        place_tag = "roma_italia"
        event_tag = "viaje_italia_2023"
        scene_tag = "caminata_centro"
        if date_taken:
            try:
                dt = datetime.strptime(date_taken, "%Y-%m-%d %H:%M:%S")
                hour = dt.hour
                if 11 <= hour <= 15:
                    scene_tag = "almuerzo_mediodia"
            except ValueError:
                scene_tag = "caminata_centro"

        tags_json = json.dumps({
            "place": place_tag,
            "event": event_tag,
            "scene": scene_tag
        }, ensure_ascii=False)

        # 3e. Actualizar la fila
        cur.execute(
            "UPDATE photos SET location_time = ?, lat = ?, lng = ?, h3_index = ?, tags = ? WHERE id = ?",
            (location_time_val, lat_rounded, lng_rounded, h3_index, tags_json, row_id)
        )
        updated += 1

    # ===========================================
    # 4. COMMIT TRANSACCIÓN
    # ===========================================
    cur.execute("COMMIT")
    conn.close()

    # ===========================================
    # 5. GENERAR INFORME DE EJECUCIÓN
    # ===========================================
    report_lines = []
    report_lines.append("# Execution Report: Phase 2 - 04-Abril 2023")
    report_lines.append("")
    report_lines.append("## Summary of updates")
    report_lines.append(f"- Total records updated: {updated}")
    report_lines.append(f"- H3 Resolution 9 cells assigned: {len(h3_cells)} unique")
    report_lines.append(f"- Sample H3 indexes: {sorted(list(h3_cells))[:5]}")
    report_lines.append("- Coordinates rounded to 4 decimals (~11m precision)")
    report_lines.append("- 3D informative tags (Place/Hito, Evento/Viaje, Situación/Escena)")
    report_lines.append("- Zero-loss protocol: native EXIF_GPS coordinates not modified")
    report_lines.append("- Explicit SQLite transaction (BEGIN TRANSACTION / COMMIT)")
    report_lines.append("")
    report_lines.append("## Processed photos (sample)")
    # Volver a consultar las fotos actualizadas para el reporte
    conn2 = sqlite3.connect(DB_PATH)
    cursor = conn2.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spatial_cac9185';")
    if not cursor.fetchone():
        print("❌ ALERTA CRITICA: base obsoleta o de scratch. Ejecucion abortada.")
        import sys
        sys.exit(1)
    cur2 = conn2.cursor()
    cur2.execute("SELECT id, filename, location_time, h3_index, tags FROM photos WHERE date_taken LIKE '2023-04-%' LIMIT 10")
    sample_rows = cur2.fetchall()
    for srow in sample_rows:
        report_lines.append(f"- ID {srow[0]}: {srow[1]} | location_time={srow[2]} | h3={srow[3]} | tags={srow[4]}")
    conn2.close()
    report_lines.append("")
    report_lines.append("## Considerations")
    report_lines.append("- No native hardware EXIF_GPS coordinates were modified")
    report_lines.append("- System noisy tags (reclassified_trip, april_2023_audit) excluded")
    report_lines.append("- Tags based on 3 dimensions: Place/Hito, Evento/Viaje, Situación/Escena")

    report_md = "\n".join(report_lines)
    report_path = "data/execution_2023_04_abril_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\nExecution report written to {report_path}")

    # Mostrar resumen en consola
    print("\n" + "="*60)
    print("PHASE 2 PERSISTENCE SUMMARY - 04-ABRil")
    print("="*60)
    print(f"Records updated: {updated}")
    print(f"Unique H3 cells: {len(h3_cells)}")
    print(f"Report: {report_path}")

if __name__ == "__main__":
    main()
