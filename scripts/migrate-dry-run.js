import fs from 'fs';
import path from 'path';
import { z } from 'zod';
import { parseExif, calculateHaversineDistance } from '../lib/geo.js';
import legacyDb from '../lib/legacy_db_mock.js';

// 1. FIX LÍNEA 9: Regex Zod SIN contrabarra antes del $ (fin de línea exacto)
const photoAuditSchema = z.object({
  photo_name: z.string().min(1),
  date_taken: z.string().regex(/^\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}$/, "Formato EXIF inválido"),
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  camera_heading: z.number().min(0).max(360).nullable().optional()
});

async function runMigrationDryRun() {
  console.log("🔍 [DRY-RUN] Iniciando auditoría diagnóstica de migración hacia PostGIS...\n");
  const legacyPhotos = legacyDb.getAllPhotos();
  const passed = [];
  const rejected = [];
  legacyPhotos.sort((a, b) => parseExif(a.date_taken) - parseExif(b.date_taken));
  for (let i = 0; i < legacyPhotos.length; i++) {
    const current = legacyPhotos[i];
    const prevAnchor = legacyPhotos.slice(0, i).reverse().find(p => p.latitude && p.longitude);
    const nextAnchor = legacyPhotos.slice(i + 1).find(p => p.latitude && p.longitude);
    const schemaValidation = photoAuditSchema.safeParse(current);
    if (!schemaValidation.success) {
      rejected.push({
        photo_name: path.basename(current.photo_name),
        reason: `Fallo Zod: ${schemaValidation.error.errors[0].message}`,
        data: current
      });
      continue;
    }
    let velocityVetoTriggered = false;
    let vetoReason = "";
    const t_curr = parseExif(current.date_taken);
    if (prevAnchor && t_curr) {
      const t_prev = parseExif(prevAnchor.date_taken);
      const hours = Math.abs(t_curr - t_prev) / (1000 * 60 * 60);
      if (hours > 0) {
        const dist = calculateHaversineDistance(prevAnchor.latitude, prevAnchor.longitude, current.latitude, current.longitude);
        const speed = dist / hours;
        if (speed > 120.0) {
          velocityVetoTriggered = true;
          vetoReason = `Velocidad imposible Tramo Origen: ${speed.toFixed(2)} km/h`;
        }
      }
    }
    if (nextAnchor && t_curr && !velocityVetoTriggered) {
      const t_next = parseExif(nextAnchor.date_taken);
      const hours = Math.abs(t_next - t_curr) / (1000 * 60 * 60);
      if (hours > 0) {
        const dist = calculateHaversineDistance(current.latitude, current.longitude, nextAnchor.latitude, nextAnchor.longitude);
        const speed = dist / hours;
        if (speed > 120.0) {
          velocityVetoTriggered = true;
          vetoReason = `Velocidad imposible Tramo Destino: ${speed.toFixed(2)} km/h`;
        }
      }
    }
    if (velocityVetoTriggered) {
      rejected.push({
        photo_name: path.basename(current.photo_name),
        reason: `Veto Cinemático: ${vetoReason}`,
        data: current
      });
      continue;
    }
    passed.push(current);
  }
  generateAuditReport(passed, rejected);
}

function generateAuditReport(passed, rejected) {
  const reportPath = path.resolve(process.cwd(), 'data/migration_dry_run_report.md');
  let md = `# 📊 Reporte de Simulación de Migración (Dry-Run)\n`;
  md += `*Fecha de ejecución: ${new Date().toISOString().split('T')[0]}*\n\n`;
  md += `### 📈 Resumen Ejecutivo\n`;
  md += `- **Total de fotos analizadas:** ${passed.length + rejected.length}\n`;
  md += `- **✅ Listas para PostGIS (Aprobadas):** ${passed.length}\n`;
  md += `- **❌ Retenidas por Inconsistencias (Rechazadas):** ${rejected.length}\n\n`;
  if (rejected.length > 0) {
    md += `### 🚨 Alertas y Fotos Retenidas\n`;
    md += `| Archivo | Coordenadas Evaluadas | Motivo del Rechazo |\n`;
    md += `|---|---|---|\n`;
    for (const item of rejected) {
      // 2. FIX LÍNEA 78: Template literal limpio sin contrabarras
      md += `| \`${item.photo_name}\` | \`${item.data.latitude}, ${item.data.longitude}\` | **${item.reason}** |\n`;
    }
    md += `\n*Nota: Estas fotos requieren revisión manual en tu DB legacy antes de forzar la migración real.*\n`;
  } else {
    md += `### ✨ ¡Limpieza Absoluta!\n`;
    md += `Todas las fotos analizadas pasaron los guardrails de velocidad y formato. El estado inicial está 100% limpio.\n`;
  }
  fs.writeFileSync(reportPath, md);
  console.log(`[💾 REPORTE GUARDADO] Se ha generado el informe detallado en: ${reportPath}`);
}

runMigrationDryRun();
