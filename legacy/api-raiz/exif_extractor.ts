// exif_extractor.ts - Soberanía del Tiempo Absoluto y Dirección
import exifr from 'exifr';

export async function extractSpatialMetadata(imageBuffer: Buffer) {
  const data = await exifr.parse(imageBuffer, {
    gps: true,
    pick: ['GPSLatitude', 'GPSLongitude', 'GPSImgDirection', 'GPSTimeStamp', 'GPSDateStamp']
  });

  let timestampUTC: Date;
  if (data?.GPSDateStamp && data?.GPSTimeStamp) {
    const [y, m, d] = data.GPSDateStamp.split(':').map(Number);
    const [hh, mm, ss] = data.GPSTimeStamp;
    timestampUTC = new Date(Date.UTC(y, m - 1, d, hh, mm, ss));
  } else {
    timestampUTC = data?.DateTimeOriginal || new Date();
  }

  return {
    lat: parseFloat(data?.latitude?.toFixed(4)), // Privacidad 11m [3]
    lng: parseFloat(data?.longitude?.toFixed(4)),
    camera_heading: data?.GPSImgDirection || null,
    utc_timestamp: timestampUTC.toISOString()
  };
}
