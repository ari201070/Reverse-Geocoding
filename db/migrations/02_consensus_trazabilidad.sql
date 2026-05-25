-- db/migrations/02_consensus_trazabilidad.sql
-- Migración para el motor de consenso, trazabilidad en PostGIS y protocolo de fotos ancla (Antigravity 2.0)

-- 1. Actualización de la tabla known_places con columnas críticas para el Pilar 5 (Consenso) y el Pilar 7 (Herencia)
ALTER TABLE known_places 
ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(4, 2),
ADD COLUMN IF NOT EXISTS metadata_evidence JSONB,
ADD COLUMN IF NOT EXISTS review_status VARCHAR(20) DEFAULT 'RECONSTRUCTED';

-- 2. Creación del índice parcial idx_pending_reviews para optimizar búsquedas de la cola de operador (HITL)
CREATE INDEX IF NOT EXISTS idx_pending_reviews 
ON known_places (id) 
WHERE review_status = 'PENDING_REVIEW';

-- 3. Protocolo de Fotos Ancla (Pilar 7)
CREATE TABLE IF NOT EXISTS anchor_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lat DECIMAL(8,4) NOT NULL, -- Redondeo forzado a 4 decimales
    lng DECIMAL(9,4) NOT NULL,
    h3_res9 TEXT NOT NULL,     -- Celda H3 Resolución 9
    timestamp_utc TIMESTAMP NOT NULL, -- Normalizado para Sincronización Solar
    visual_signature JSONB     -- Características de micro-fisonomía via Ollama
);

-- Índice para búsquedas ultra rápidas de fotos ancla por celda H3
CREATE INDEX IF NOT EXISTS idx_anchor_photos_h3 ON anchor_photos (h3_res9);
