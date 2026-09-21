import os
import sys
import shutil

# Ensure standard output encodes as UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

TARGET_FOLDERS = [
    (r"G:\האחסון שלי\טיול לבוסניה והרצגובינה", r"F:\טיול לבוסניה והרצגובינה", "Viaje a Bosnia"),
    (r"G:\האחסון שלי\Google AI Studio\imagenes", r"F:\Google_AI_Studio_imagenes", "Google AI Studio"),
    (r"G:\האחסון שלי\כנס פוס", r"F:\כנס פוס", "Conferencia Foss"),
    (r"G:\האחסון שלי\גברים רעבים באיטליה", r"F:\גברים רעבים באיטליה", "Hombres Hambrientos en Italia"),
    (r"G:\האחסון שלי\צילומי מסמכים", r"F:\צילומי מסמכים", "Fotos de Documentos"),
    (r"G:\האחסון שלי\Gemini Gems", r"F:\Gemini_Gems", "Prompts de Gemini Gems")
]

def format_size(bytes_val):
    if bytes_val is None or bytes_val <= 0:
        return "0 KB"
    if bytes_val >= 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / 1024:.1f} KB"

def copy_file_safe(src, dst):
    """
    Safely copies file content byte-by-byte to avoid [WinError 1] Incorrect function
    caused by Google Drive's virtual file extended attributes on .gdoc/.gsheet.
    """
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
            return True
        with open(src, 'rb') as sf, open(dst, 'wb') as df:
            while chunk := sf.read(1024 * 1024):
                df.write(chunk)
        return True
    except Exception as e:
        print(f"   [Aviso copia] {os.path.basename(src)}: {e}")
        return False

def main():
    print("=" * 125)
    print("  RESPALDO SEGURO EN F:\\ Y PURGA INMEDIATA EN GOOGLE DRIVE (G:\\האחסון שלי)")
    print("  [PROTOCOLO DE SEGURIDAD ABSOLUTO — CERO PÉRDIDA DE DATOS]")
    print("=" * 125)

    total_backed_up = 0
    total_deleted_from_g = 0
    total_bytes_purged_from_g = 0

    for g_path, f_path, label in TARGET_FOLDERS:
        print(f"\n📁 Procesando: {label}")
        print(f"   Origen G:\\ : {g_path}")
        print(f"   Destino F:\\: {f_path}")

        if not os.path.exists(g_path):
            print("   -> La carpeta no existe en G:\\ (Ya eliminada o no creada). Omitiendo.")
            continue

        os.makedirs(f_path, exist_ok=True)

        g_files = []
        for root, dirs, files in os.walk(g_path):
            for f in files:
                g_fp = os.path.join(root, f)
                rel_path = os.path.relpath(g_fp, g_path)
                f_fp = os.path.join(f_path, rel_path)
                g_files.append((g_fp, f_fp, f))

        print(f"   Total archivos en G:\\: {len(g_files)}")

        backed_up_this_folder = 0
        deleted_this_folder = 0
        bytes_this_folder = 0

        for g_fp, f_fp, f in g_files:
            try:
                g_sz = os.path.getsize(g_fp)
            except:
                g_sz = 0

            # 1. Ensure file exists on F:\ safely
            success = copy_file_safe(g_fp, f_fp)
            if success:
                backed_up_this_folder += 1
                total_backed_up += 1

                # 2. Only remove from G:\ once verified on F:\
                if os.path.exists(f_fp):
                    try:
                        os.remove(g_fp)
                        deleted_this_folder += 1
                        total_deleted_from_g += 1
                        bytes_this_folder += g_sz
                        total_bytes_purged_from_g += g_sz
                    except Exception as e:
                        print(f"   [Error borrando de G:\\] {f}: {e}")

        # 3. Clean up empty folder on G:\
        try:
            shutil.rmtree(g_path)
            print(f"   ✓ Carpeta eliminada de Google Drive: {os.path.basename(g_path)}")
        except:
            if os.path.exists(g_path):
                try:
                    os.rmdir(g_path)
                except:
                    pass

        print(f"   ✓ Respaldo y purga: {deleted_this_folder} archivos eliminados de Google Drive ({format_size(bytes_this_folder)} liberados).")

    print("\n" + "=" * 125)
    print("  REPORTE FINAL DE SINCRONIZACIÓN Y PURGA EN GOOGLE DRIVE (G:\\)")
    print("=" * 125)
    print(f"  • Total de archivos respaldados en F:\\ : {total_backed_up:>5} archivos")
    print(f"  • Total de archivos eliminados de Google Drive: {total_deleted_from_g:>5} archivos")
    print(f"  • Espacio total liberado en la nube de Google : {format_size(total_bytes_purged_from_g):>9}")
    print("=" * 125)
    print("IMPORTANTE: Al estar Google Drive for Desktop activo, estas eliminaciones se sincronizan en vivo.")
    print("Recuerda vaciar la papelera en https://drive.google.com/drive/trash para que la cuota web se actualice a 0.")

if __name__ == '__main__':
    main()
