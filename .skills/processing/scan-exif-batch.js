import fs from 'fs';
import path from 'path';
import exifr from 'exifr';

const folders = [
  "F:\\2025\\09-Septiembre",
  "F:\\2025\\10-Octubre"
];

const outputJsonPath = "C:\\Users\\flier\\.gemini\\antigravity\\scratch\\sep_oct_exif_data.json";

async function scanFile(filePath) {
  try {
    const fileBuffer = await fs.promises.readFile(filePath);
    const exifData = await exifr.parse(fileBuffer, {
      gps: true,
      exif: true,
      xmp: true,
      iptc: true
    });
    
    if (!exifData) return { hasExif: false };
    
    const lat = exifData.latitude || exifData.GPSLatitude || null;
    const lng = exifData.longitude || exifData.GPSLongitude || null;
    const timestamp = exifData.DateTimeOriginal || exifData.CreateDate || exifData.DateTime || null;
    const gps_accuracy = exifData.GPSHPositioningError || null;
    const direction = exifData.GPSImgDirection || null;
    
    return {
      hasExif: true,
      lat: lat ? Number(lat) : null,
      lng: lng ? Number(lng) : null,
      timestamp: timestamp ? String(timestamp) : null,
      gps_accuracy: gps_accuracy ? String(gps_accuracy) : null,
      direction: direction ? Number(direction) : null
    };
  } catch (err) {
    return { hasExif: false, error: err.message };
  }
}

async function main() {
  console.error("=== BATCH EXIF SCANNING ===");
  const results = {};
  
  for (const folder of folders) {
    if (!fs.existsSync(folder)) {
      console.error(`Folder not found: ${folder}`);
      continue;
    }
    
    console.error(`Scanning folder: ${folder}`);
    const files = await fs.promises.readdir(folder);
    results[folder] = [];
    
    let count = 0;
    for (const file of files) {
      const filePath = path.join(folder, file);
      const stat = await fs.promises.stat(filePath);
      if (stat.isDirectory()) continue;
      
      const exif = await scanFile(filePath);
      
      results[folder].push({
        filename: file,
        sizeBytes: stat.size,
        mtime: stat.mtime,
        exif: exif
      });
      
      count++;
      if (count % 50 === 0) {
        console.error(`Processed ${count} files in ${path.basename(folder)}...`);
      }
    }
  }
  
  await fs.promises.writeFile(outputJsonPath, JSON.stringify(results, null, 2), 'utf8');
  console.error(`✅ Done! Saved results to ${outputJsonPath}`);
}

main().catch(err => console.error("Error in main:", err));
