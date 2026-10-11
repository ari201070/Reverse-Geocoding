"""Orquestador de ingesta transaccional — pipeline Roma (solo se ejecuta bajo orden explicita)."""
import os
import re
import json
import sqlite3

DB_PATH = "F:/photo_catalog.db"
BASE_DIR = "F:/2023/10-Octubre/"
CONTEXTS = "data/fixtures/roma-2023/contexts.json"


def extraer_14_digitos(nombre_archivo):
    """Aisla YYYYMMDDHHMMSS sea extendido con puntos o compacto."""
    digitos = re.sub(r"\D", "", nombre_archivo)
    m = re.search(r"(19\d\d|20\d\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([01]\d|2[0-3])([0-5]\d)([0-5]\d)", digitos)
    return m.group(0) if m else None


def cargar_contextos():
    with open(CONTEXTS, encoding="utf-8") as fh:
        return json.load(fh)


def contexto_de(signatura, contextos):
    for ctx_id, ctx in contextos.items():
        if signatura is None:
            continue
        for v in ctx.get("ventanas", []):
            if v["desde"] <= signatura <= v["hasta"]:
                return ctx_id, ctx
    return None, None


def procesar(dry_run=True):
    contextos = cargar_contextos()
    con = sqlite3.connect(DB_PATH, timeout=30)
    cur = con.cursor()
    stats = {"trayecto_null": 0, "omitidas": 0}
    archivos = sorted(os.listdir(BASE_DIR))
    if not dry_run:
        con.execute("BEGIN TRANSACTION")
    for fn in archivos:
        sig = extraer_14_digitos(fn)
        ctx_id, _ctx = contexto_de(sig, contextos)
        if ctx_id == "terravision-fiumicino-termini-2023-10-02":
            # Invariante: captura NULL, monumento solo en escena.place_id.
            if not dry_run:
                cur.execute(
                    "UPDATE photos SET latitude=NULL, longitude=NULL, lat=NULL,"
                    " lng=NULL, h3_index=NULL WHERE filename=?",
                    (fn,),
                )
            stats["trayecto_null"] += 1
        else:
            stats["omitidas"] += 1
    if not dry_run:
        con.commit()
    con.close()
    return stats


if __name__ == "__main__":
    import sys
    print(procesar(dry_run="--execute" not in sys.argv))
