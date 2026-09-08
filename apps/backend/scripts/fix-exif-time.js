import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readdir } from "node:fs/promises";
import { join, extname } from "node:path";
import process from "node:process";

const execFileAsync = promisify(execFile);
const EXIFTOOL = "C:\\Users\\flier\\AppData\\Local\\Programs\\ExifTool\\ExifTool.exe";
const SEARCH_ROOT = "F:\\2025";
const TARGET_MODEL = "COOLPIX P900";

// ─── Escaneo recursivo de JPG ────────────────────────────────────────────────
async function findJpgFiles(dir) {
  const results = [];
  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return results;
  }
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      const sub = await findJpgFiles(fullPath);
      results.push(...sub);
    } else if (entry.isFile() && [".jpg", ".jpeg"].includes(extname(entry.name).toLowerCase())) {
      results.push(fullPath);
    }
  }
  return results;
}

// ─── Obtener modelo de cámara ────────────────────────────────────────────────
async function getModel(filePath) {
  try {
    const { stdout } = await execFileAsync(EXIFTOOL, ["-Model", "-s3", filePath]);
    return stdout.trim();
  } catch {
    return "";
  }
}

// ─── Aplicar shift de -6 horas ───────────────────────────────────────────────
async function shiftTime(filePath) {
  try {
    const { stdout } = await execFileAsync(EXIFTOOL, [
      "-DateTimeOriginal-=6:00:00",
      "-CreateDate-=6:00:00",
      "-overwrite_original",
      filePath,
    ]);
    return stdout.trim();
  } catch (err) {
    return `ERROR: ${err.message}`;
  }
}

// ─── Main ────────────────────────────────────────────────────────────────────
async function main() {
  console.log(`🔍 Buscando JPG en ${SEARCH_ROOT}...`);
  const jpgFiles = await findJpgFiles(SEARCH_ROOT);
  console.log(`📂 Encontrados ${jpgFiles.length} JPG`);

  let target = 0;
  let shifted = 0;
  let errors = 0;

  for (const filePath of jpgFiles) {
    const model = await getModel(filePath);
    if (model === TARGET_MODEL) {
      target++;
      const result = await shiftTime(filePath);
      if (result.startsWith("ERROR")) {
        errors++;
        console.warn(`  ⚠️ ${filePath}: ${result}`);
      } else {
        shifted++;
        if (shifted % 50 === 0) console.log(`  ✅ ${shifted} fotos corregidas...`);
      }
    }
  }

  console.log("\n════════════════════════════════════════════");
  console.log(`🎯 Fotos COOLPIX P900: ${target}`);
  console.log(`✅ Corregidas (-6h): ${shifted}`);
  console.log(`❌ Errores: ${errors}`);
  console.log("════════════════════════════════════════════");
}

main().catch((err) => {
  console.error("❌ Error fatal:", err);
  process.exit(1);
});