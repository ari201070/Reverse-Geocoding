import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import exifr from 'exifr';
import initSqlJs from 'sql.js';

const DB_PATH = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db';
const MEDIA_EXTS = new Set(['.jpg','.jpeg','.heic','.png','.mp4','.mov','.gif','.webp','.tiff','.bmp','.avif']);
const BATCH_SIZE = 100;

const YEAR_DIRS = [];
for (let y = 2002; y <= 2026; y++) YEAR_DIRS.push(`F:\\${y}`);
const EXTRA_DIRS = ['F:\\.Papelera_Deduplicacion', 'G:\\האחסון שלי'];

let db = null;
let stats = { scanned: 0, skipped_same_size: 0, inserted: 0, duplicates_found: 0, updated_winner: 0, updated_path: 0, errors: 0 };

function sha256File(fp) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    const s = fs.createReadStream(fp);
    s.on('data', d => h.update(d));
    s.on('end', () => resolve(h.digest('hex')));
    s.on('error', reject);
  });
}

function calcTier(lat, lng, dateTaken) {
  const hasGPS = (lat != null && lng != null && Math.abs(lat) > 0.001 && Math.abs(lng) > 0.001);
  const hasDate = (dateTaken != null && dateTaken.length > 0);
  if (hasGPS && hasDate) return 4;
  if (hasDate) return 3;
  if (hasGPS) return 2;
  return 1;
}

function fmtDate(d) {
  if (!d) return null;
  if (typeof d === 'string') return d.slice(0, 19).replace('T', ' ');
  if (d instanceof Date && !isNaN(d)) return d.toISOString().replace('T', ' ').slice(0, 19);
  return null;
}

function isMedia(name) {
  return MEDIA_EXTS.has(path.extname(name).toLowerCase());
}

function folderSource(fp) {
  if (fp.includes('.Papelera_Deduplicacion')) return 'papelera';
  if (fp.startsWith('G:\\')) return 'G_Drive';
  return 'F_Organized';
}

async function* walkDir(dir) {
  try {
    const entries = await fs.promises.readdir(dir, { withFileTypes: true });
    for (const e of entries) {
      const fp = path.join(dir, e.name);
      if (e.isDirectory()) yield* walkDir(fp);
      else if (e.isFile() && isMedia(e.name)) yield fp;
    }
  } catch (err) {
    console.error(`  ⚠ ${dir}: ${err.message}`);
  }
}

async function initDB() {
  const SQL = await initSqlJs();
  const buf = fs.readFileSync(DB_PATH);
  db = new SQL.Database(buf);
  return db;
}

function saveDB() {
  fs.writeFileSync(DB_PATH, Buffer.from(db.export()));
}

function fetchOne(sql, params) {
  const stmt = db.prepare(sql);
  stmt.bind(params);
  if (stmt.step()) {
    const row = stmt.getAsObject();
    stmt.free();
    return row;
  }
  stmt.free();
  return null;
}

async function processFile(fp) {
  stats.scanned++;
  try {
    const stat = await fs.promises.stat(fp);
    const fname = path.basename(fp);
    const ext = path.extname(fname).toLowerCase();
    const src = folderSource(fp);

    // 1. OPTIMIZATION: Check path first. If path exists and size is identical, skip fully!
    const existingByPath = fetchOne('SELECT id, file_size, sha256, latitude, longitude, date_taken, folder_source FROM photos WHERE file_path = ?', [fp]);
    if (existingByPath) {
      if (stat.size === existingByPath.file_size) {
        stats.skipped_same_size++;
        return;
      }
      
      // If size changed, recalculate hash & EXIF
      const hash = await sha256File(fp);
      let exif = null;
      try {
        const buf = fs.readFileSync(fp);
        exif = await exifr.parse(buf, { gps: true, exif: true, xmp: true, iptc: true });
      } catch {}

      const lat = (exif?.latitude != null && Math.abs(exif.latitude) > 0.001) ? exif.latitude : null;
      const lng = (exif?.longitude != null && Math.abs(exif.longitude) > 0.001) ? exif.longitude : null;
      const dateRaw = exif?.DateTimeOriginal ?? exif?.CreateDate ?? exif?.ModifyDate ?? stat.mtime;
      const dateTaken = fmtDate(dateRaw);
      const dateSource = exif ? 'exif' : 'filesystem_mtime';

      db.run(
        `UPDATE photos SET sha256 = ?, file_size = ?, file_ext = ?, date_taken = ?, date_source = ?,
         latitude = ?, longitude = ?, folder_source = ? WHERE id = ?`,
        [hash, stat.size, ext, dateTaken, dateSource, lat, lng, src, existingByPath.id]
      );
      stats.updated_path++;
      return;
    }

    // 2. If path doesn't exist, calculate hash & EXIF
    const hash = await sha256File(fp);
    let exif = null;
    try {
      const buf = fs.readFileSync(fp);
      exif = await exifr.parse(buf, { gps: true, exif: true, xmp: true, iptc: true });
    } catch {}

    const lat = (exif?.latitude != null && Math.abs(exif.latitude) > 0.001) ? exif.latitude : null;
    const lng = (exif?.longitude != null && Math.abs(exif.longitude) > 0.001) ? exif.longitude : null;
    const dateRaw = exif?.DateTimeOriginal ?? exif?.CreateDate ?? exif?.ModifyDate ?? stat.mtime;
    const dateTaken = fmtDate(dateRaw);
    const dateSource = exif ? 'exif' : 'filesystem_mtime';

    // 3. Check if hash exists (duplicate detection)
    const existingByHash = fetchOne('SELECT id, file_path, file_size, latitude, longitude, date_taken, folder_source FROM photos WHERE sha256 = ?', [hash]);
    if (existingByHash) {
      stats.duplicates_found++;
      const newTier = calcTier(lat, lng, dateTaken);
      const oldTier = calcTier(existingByHash.latitude, existingByHash.longitude, existingByHash.date_taken);
      
      if (newTier > oldTier || (newTier === oldTier && stat.size > existingByHash.file_size)) {
        // Mark previous as duplicate and promote this one
        db.run('UPDATE photos SET is_duplicate = 1, duplicate_of = ? WHERE id = ?', [fp, existingByHash.id]);
        db.run(
          `UPDATE photos SET file_path = ?, folder_source = ?, file_size = ?, latitude = ?, longitude = ?,
           date_taken = ?, date_source = ?, is_duplicate = 0, duplicate_of = NULL WHERE id = ?`,
          [fp, src, stat.size, lat, lng, dateTaken, dateSource, existingByHash.id]
        );
        stats.updated_winner++;
      } else {
        // Keep this as duplicate
        db.run(
          `INSERT INTO photos (file_path, folder_source, filename, file_size, file_ext, sha256, date_taken, date_source,
            latitude, longitude, location_name, location_address, country, city, album_name, is_duplicate, duplicate_of)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, 1, ?)`,
          [fp, src, fname, stat.size, ext, hash, dateTaken, dateSource, lat, lng, existingByHash.file_path]
        );
      }
      return;
    }

    // 4. Truly new file, insert
    db.run(
      `INSERT INTO photos (file_path, folder_source, filename, file_size, file_ext, sha256, date_taken, date_source,
        latitude, longitude, location_name, location_address, country, city, album_name, is_duplicate, duplicate_of)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, 0, NULL)`,
      [fp, src, fname, stat.size, ext, hash, dateTaken, dateSource, lat, lng]
    );
    stats.inserted++;
  } catch (err) {
    stats.errors++;
    if (stats.errors <= 20) console.error(`  ❌ ${path.basename(fp)}: ${err.message.slice(0, 80)}`);
  }
}

async function scanDir(dir) {
  if (!fs.existsSync(dir)) { console.log(`  SKIP (not found): ${dir}`); return; }
  console.log(`\n📂 ${dir}`);
  let count = 0, batch = 0;
  db.run('BEGIN TRANSACTION');
  for await (const fp of walkDir(dir)) {
    await processFile(fp);
    count++;
    if (count % 200 === 0) {
      process.stdout.write(`  ${count} files... skp=${stats.skipped_same_size} dup=${stats.duplicates_found} upd=${stats.updated_winner} ins=${stats.inserted} err=${stats.errors}\r`);
    }
    if (++batch >= BATCH_SIZE) {
      db.run('COMMIT');
      db.run('BEGIN TRANSACTION');
      batch = 0;
    }
  }
  db.run('COMMIT');
  console.log(`  ✅ ${count} files`);
}

async function main() {
  console.log('='.repeat(60));
  console.log('  F: DRIVE SCAN (ULTRA-OPTIMIZED) — EXIF + SHA256 + DEDUP + DB INSERT');
  console.log(`  DB: ${DB_PATH}`);
  console.log('='.repeat(60));

  await initDB();
  const allDirs = [...YEAR_DIRS, ...EXTRA_DIRS];
  const start = Date.now();

  for (const dir of allDirs) {
    await scanDir(dir);
    saveDB();
    const e = ((Date.now() - start) / 1000 / 60).toFixed(1);
    console.log(`  💾 ${e} min | scn=${stats.scanned} skp=${stats.skipped_same_size} ins=${stats.inserted} dup=${stats.duplicates_found} upd=${stats.updated_winner} ptUpd=${stats.updated_path} err=${stats.errors}`);
  }

  db.close();
  const e = ((Date.now() - start) / 1000 / 60).toFixed(1);
  console.log('\n' + '='.repeat(60));
  console.log('  ✅ SCAN COMPLETE');
  console.log('='.repeat(60));
  for (const [k, v] of Object.entries(stats)) console.log(`  ${k.padEnd(20)} ${v}`);
  console.log(`  time (min)          ${e}`);
}

main().catch(err => { console.error('FATAL:', err); process.exit(1); });
