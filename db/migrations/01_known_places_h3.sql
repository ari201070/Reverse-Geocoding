-- Implementación del Nivel 1 de la Lógica de Cascada (Caché Local)
-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS h3;
CREATE EXTENSION IF NOT EXISTS h3_postgis;

-- Tabla principal de ubicaciones conocidas (conocimiento en caché)
CREATE TABLE IF NOT EXISTS known_places (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_place_id TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    place_type TEXT,
    geom GEOMETRY(Point, 4326) NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    -- Columna generada automáticamente que convierte la geometría a un índice H3 (resolución 9)
    h3_index_res9 h3index GENERATED ALWAYS AS (h3_lat_lng_to_cell(geom::geometry, 9)) STORED
);

-- Índice diseñado para hacer match exacto (igualdad string/h3index) y no ST_DWithin
CREATE INDEX IF NOT EXISTS idx_known_places_h3_res9 ON known_places (h3_index_res9);

-- Comando PostGIS: Implementación del redondeo a 4 decimales
CREATE OR REPLACE FUNCTION round_geom_coordinates()
RETURNS TRIGGER AS $$
BEGIN
    -- Este redondeo debe ejecutarse antes de que el sistema genere la columna automática h3_index_res9
    NEW.geom := ST_SetSRID(ST_MakePoint(ROUND(ST_X(NEW.geom)::numeric, 4), ROUND(ST_Y(NEW.geom)::numeric, 4)), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_round_known_places_geom ON known_places;

CREATE TRIGGER trg_round_known_places_geom
BEFORE INSERT OR UPDATE ON known_places
FOR EACH ROW
EXECUTE FUNCTION round_geom_coordinates();
