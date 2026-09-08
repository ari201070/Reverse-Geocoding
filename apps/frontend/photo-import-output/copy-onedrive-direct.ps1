# Copy unique OneDrive files to F: drive
# Reads CSV directly - no Hebrew corruption from Node.js
$ErrorActionPreference = 'Continue'
$csvPath = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/onedrive-files.csv'
$dbPath = 'C:/Users/flier/.gemini/antigravity/scratch/photo_catalog.db'

# Load CSV
$csv = Import-Csv $csvPath
Write-Host "Loaded $($csv.Count) files from CSV"

# Load existing files from DB
$db = New-Object System.Data.SQLite.SQLiteConnection("Data Source=$dbPath;Version=3;")
$db.Open()
$cmd = $db.CreateCommand()
$cmd.CommandText = 'SELECT filename, file_size FROM photos'
$reader = $cmd.ExecuteReader()
$existing = @{}
while ($reader.Read()) {
    $name = $reader['filename'].ToString().ToLower()
    $size = [long]$reader['file_size']
    if (-not $existing.ContainsKey($name)) { $existing[$name] = @() }
    $existing[$name] += $size
}
$reader.Close()
$db.Close()
Write-Host "Existing files in DB: $($existing.Count) unique names"

$copied = 0
$skipped = 0
$dupes = 0
$failed = 0

foreach ($file in $csv) {
    $name = $file.Name
    $size = [long]$file.Length
    $src = $file.FullName
    
    # Check extension
    $ext = [System.IO.Path]::GetExtension($name).ToLower()
    $validExts = @('.jpg','.jpeg','.png','.mp4','.gif','.mov','.avi','.heic','.webp')
    if ($ext -notin $validExts) { continue }
    
    # Check duplicate
    $nameLower = $name.ToLower()
    if ($existing.ContainsKey($nameLower)) {
        $sizes = $existing[$nameLower]
        $isDupe = $false
        foreach ($s in $sizes) { if ([Math]::Abs($s - $size) -lt 4096) { $isDupe = $true; break } }
        if ($isDupe) { $dupes++; continue }
    }
    
    # Extract date from filename
    $dateMatch = [regex]::Match($name, '(d{4})(d{2})(d{2})[_-]')
    if (-not $dateMatch.Success) {
        $dateMatch = [regex]::Match($name, '(d{4})-(d{2})-(d{2})')
    }
    
    $monthNames = @('','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre')
    
    if ($dateMatch.Success) {
        $year = $dateMatch.Groups[1].Value
        $monthNum = [int]$dateMatch.Groups[2].Value
        $destDir = "F:/$($year)/$($monthNames[$monthNum])"
    } else {
        $destDir = 'F:/SinFecha'
    }
    
    $dest = "$($destDir)/$($name)"
    
    try {
        if (-not (Test-Path $dest)) {
            if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
            Copy-Item -LiteralPath $src -Destination $dest -Force
            $copied++
        } else {
            $skipped++
        }
    } catch {
        Write-Host "ERROR: $($_.Exception.Message) - $name"
        $failed++
    }
}

Write-Host ''
Write-Host '========================================'
Write-Host '  RESULTADO DE COPIA'
Write-Host '========================================'
Write-Host "  Copiados:  $copied"
Write-Host "  Duplicados: $dupes"
Write-Host "  Ya existian: $skipped"
Write-Host "  Fallidos:  $failed"
Write-Host '========================================'
