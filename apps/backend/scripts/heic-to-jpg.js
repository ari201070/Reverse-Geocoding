import { readdir, readFile, stat, writeFile } from "node:fs/promises";
import { join, extname, parse } from "node:path";
import { Buffer } from "node:buffer";
import process from "node:process";
import heicConvert from "heic-convert";

const SEARCH_ROOT = "F:\\";
const QUALITY = 0.95; // Calidad 95%

// ─── Escaneo recursivo ───────────────────────────────────────────────────────
async function findHeicFiles(dir) {
  const results = [];
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return results; // Sin acceso → omitir
  }

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      const sub = await findHeicFiles(fullPath);
      results.push(...sub);
    } else if (entry.isFile() && extname(entry.name).toLowerCase() === ".heic") {
      results.push(fullPath);
    }
  }
  return results;
}

// ─── Conversión ──────────────────────────────────────────────────────────────
async function convertHeicToJpg(heicPath) {
  const base = parse(heicPath).name;
  const jpgPath = join(parse(heicPath).dir, `${base}.jpg`);

  // Verificar si ya existe el JPG correspondiente
  try {
    await stat(jpgPath);
    return { heicPath, jpgPath, status: "skipped" };
  } catch {
    // No existe → continuar
  }

  try {
    const heicBuffer = await readFile(heicPath);
    const jpgBuffer = await heicConvert({
      buffer: heicBuffer,
      format: "JPEG",
      quality: QUALITY,
    });
    await writeFile(jpgPath, Buffer.from(jpgBuffer));
    return { heicPath, jpgPath, status: "converted" };
  } catch (err) {
    return { heicPath, jpgPath, status: `error: ${err.message}` };
  }
}

// ─── Main ────────────────────────────────────────────────────────────────────
async function main() {
  console.log("🖼️  Buscando archivos HEIC en F:\\...");
  const heicFiles = await findHeicFiles(SEARCH_ROOT);
  console.log(`📂 Encontrados ${heicFiles.length} archivos HEIC`);

  let converted = 0;
  let skipped = 0;
  let errors = 0;

  for (const heicPath of heicFiles) {
    const result = await convertHeicToJpg(heicPath);
    if (result.status === "converted") {
      converted++;
      console.log(`  ✅ ${result.heicPath} → ${result.jpgPath}`);
    } else if (result.status === "skipped") {
      skipped++;
    } else {
      errors++;
      console.warn(`  ⚠️ ${result.heicPath}: ${result.status}`);
    }
  }

  console.log("\n════════════════════════════════════════════");
  console.log(`✅ Convertidos: ${converted}`);
  console.log(`⏭️  Omitidos (ya existían JPG): ${skipped}`);
  console.log(`❌ Errores: ${errors}`);
  console.log("════════════════════════════════════════════");
}

main().catch((err) => {
  console.error("❌ Error fatal:", err);
  process.exit(1);
});