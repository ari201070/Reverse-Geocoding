-- setup_db.sql
-- Script to initialize the Reverse-Geocoding SpatialCache (Nivel 1)

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS postgis;
-- NOTE: h3 extension must be installed on the server
CREATE EXTENSION IF NOT EXISTS h3;

-- Tabla de Soberanía de Datos (Memoria Colectiva)
CREATE TABLE IF NOT EXISTS known_places (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,                -- Nombre oficial del local
    place_id TEXT UNIQUE,              -- ID de Google/OpenCage
    mid TEXT UNIQUE,                   -- Machine Identifier de Hitos
    
    -- Evidencia del Ancla (Soberanía de Datos)
    anchor_evidence JSONB,             -- { method: 'OCR', value: '...', confidence: 0.9 }
    anchor_method TEXT,                -- 'OCR' | 'LANDMARK' | 'FISONOMIA'
    
    -- Privacidad: Coordenadas anonimizadas a 4 decimales (~11m)
    anon_latitude NUMERIC(8, 4) NOT NULL, 
    anon_longitude NUMERIC(9, 4) NOT NULL,
    
    -- Índice H3 Resolución 9 (Precisión ~11m)
    h3_res9 h3index NOT NULL,
    
    -- Metadatos de Auditoría (Retención 90 días)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índice B-Tree ultra rápido para consultas espaciales
CREATE INDEX IF NOT EXISTS idx_known_places_h3 ON known_places USING btree (h3_res9);

-- Política de limpieza automática de auditoría
CREATE OR REPLACE FUNCTION purge_old_exif() RETURNS void AS $$
BEGIN
    -- Los nombres se mantienen, pero los datos de auditoría expiran
    DELETE FROM known_places WHERE created_at < NOW() - INTERVAL '90 days' AND name IS NULL;
END;
$$ LANGUAGE plpgsql;
