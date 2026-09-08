$ErrorActionPreference = 'Continue'
$csvPath = 'C:/Users/flier/GitHub/Travel-Booking-Document-Hub/onedrive-files.csv'
$csv = Import-Csv $csvPath
Write-Host "Loaded $($csv.Count) files from CSV"

$monthNames = @('','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre')
$validExts = @('.jpg','.jpeg','.png','.mp4','.gif','.mov','.avi','.heic','.webp')
$copied = 0; $skipped = 0; $dupes = 0; $failed = 0

foreach ($file in $csv) {
    $name = $file.Name
    $size = [long]$file.Length
    $src = $file.FullName
    $ext = [System.IO.Path]::GetExtension($name).ToLower()
    if ($ext -notin $validExts) { continue }

    $dateMatch = [regex]::Match($name, '(\d{4})(\d{2})(\d{2})[_-]')
    if (-not $dateMatch.Success) { $dateMatch = [regex]::Match($name, '(\d{4})-(\d{2})-(\d{2})') }

    if ($dateMatch.Success) {
        $year = $dateMatch.Groups[1].Value
        $monthNum = [int]$dateMatch.Groups[2].Value
        if ($monthNum -ge 1 -and $monthNum -le 12) {
            $destDir = "F:/$year/$($monthNames[$monthNum])"
        } else {
            $destDir = 'F:/SinFecha'
        }
    } else {
        $destDir = 'F:/SinFecha'
    }

    $dest = "$destDir/$name"

    try {
        if (Test-Path $dest) { $skipped++; continue }
        if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
        Copy-Item -LiteralPath $src -Destination $dest -Force
        $copied++
        if ($copied % 100 -eq 0) { Write-Host "  [Progreso] Copiadas $copied fotos..." }
    } catch {
        $failed++
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "  RESULTADO DE COPIA"
Write-Host "========================================"
Write-Host "  Copiados:    $copied"
Write-Host "  Duplicados:  $dupes"
Write-Host "  Ya existian: $skipped"
Write-Host "  Fallidos:    $failed"
Write-Host "========================================"
