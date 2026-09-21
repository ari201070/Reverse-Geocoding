import os
import sys
import io
import piexif

# Configure standard outputs for UTF-8 to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

F_DRIVE_ROOT = r"F:\\"
TARGET_YEARS = ['2024', '2025', '2026']

# Bounding box of Rome
ROME_MIN_LAT = 41.8
ROME_MAX_LAT = 42.0
ROME_MIN_LNG = 12.4
ROME_MAX_LNG = 12.6

def parse_rational(rat):
    if not rat or len(rat) != 2:
        return 0.0
    return float(rat[0]) / float(rat[1]) if rat[1] != 0 else 0.0

def exif_gps_to_decimal(gps_lat, lat_ref, gps_lng, lng_ref):
    try:
        lat = parse_rational(gps_lat[0]) + parse_rational(gps_lat[1])/60.0 + parse_rational(gps_lat[2])/3600.0
        lng = parse_rational(gps_lng[0]) + parse_rational(gps_lng[1])/60.0 + parse_rational(gps_lng[2])/3600.0
        
        if isinstance(lat_ref, bytes):
            lat_ref = lat_ref.decode(errors='ignore')
        if isinstance(lng_ref, bytes):
            lng_ref = lng_ref.decode(errors='ignore')
            
        if lat_ref == 'S':
            lat = -lat
        if lng_ref == 'W':
            lng = -lng
        return lat, lng
    except Exception:
        return None, None

def decode_xp_keywords(val):
    if not val:
        return ""
    if isinstance(val, (bytes, bytearray)):
        return val.decode('utf-16', errors='ignore').strip()
    elif isinstance(val, tuple):
        try:
            return bytes(val).decode('utf-16', errors='ignore').strip()
        except:
            return ""
    return ""

def main():
    print("=" * 80)
    print("  INICIANDO SANEAMIENTO EXIF FINAL Y DETALLADO (2024, 2025, 2026)")
    print("=" * 80)
    
    healed_count = 0
    scanned_count = 0
    
    for year in TARGET_YEARS:
        year_path = os.path.join(F_DRIVE_ROOT, year)
        if not os.path.exists(year_path):
            continue
            
        print(f"\nEscaneando de forma exhaustiva el año: {year} ...")
        
        for root, dirs, files in os.walk(year_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ('.jpg', '.jpeg'):
                    fp = os.path.join(root, f)
                    scanned_count += 1
                    
                    try:
                        exif_dict = piexif.load(fp)
                        zeroth = exif_dict.get('0th', {})
                        gps = exif_dict.get('GPS', {})
                        
                        is_corrupted = False
                        reason = ""
                        
                        # Check GPS
                        if gps:
                            lat_val = gps.get(piexif.GPSIFD.GPSLatitude)
                            lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
                            lng_val = gps.get(piexif.GPSIFD.GPSLongitude)
                            lng_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
                            
                            if lat_val and lat_ref and lng_val and lng_ref:
                                d_lat, d_lng = exif_gps_to_decimal(lat_val, lat_ref, lng_val, lng_ref)
                                if d_lat and d_lng:
                                    if ROME_MIN_LAT <= d_lat <= ROME_MAX_LAT and ROME_MIN_LNG <= d_lng <= ROME_MAX_LNG:
                                        is_corrupted = True
                                        reason = f"Coordenadas de Roma: ({d_lat:.4f}, {d_lng:.4f})"
                                        
                        # Check Keywords
                        keywords_tag = zeroth.get(40094)
                        if keywords_tag:
                            keywords_str = decode_xp_keywords(keywords_tag)
                            if 'Portuno' in keywords_str or 'Roma' in keywords_str or 'Italia' in keywords_str:
                                is_corrupted = True
                                reason = f"Keywords de Roma: '{keywords_str}'"
                                
                        if is_corrupted:
                            # Clean the file!
                            exif_dict.pop('GPS', None)
                            zeroth.pop(40094, None) # XPKeywords
                            zeroth.pop(40093, None) # XPSubject
                            zeroth.pop(40095, None) # XPComment
                            
                            # Write cleaned EXIF back
                            exif_bytes = piexif.dump(exif_dict)
                            piexif.insert(exif_bytes, fp)
                            print(f"  [SANEADO] {os.path.relpath(fp, F_DRIVE_ROOT)}")
                            print(f"            Causa: {reason}")
                            healed_count += 1
                            
                    except Exception as e:
                        pass
                        
    print("\n" + "="*50)
    print("  PROCESO DE SANEAMIENTO EXIF FINALIZADO")
    print("=" * 50)
    print(f"  - Total JPEGs escaneados:   {scanned_count}")
    print(f"  - Total archivos saneados:  {healed_count}")
    print("=" * 50)

if __name__ == '__main__':
    main()
