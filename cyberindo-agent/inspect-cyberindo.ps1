# =============================================================================
# FAUKAY E-SPORT — CyberIndo (gcbServer.exe) Deep Inspector
# Membaca isi C:\Program Files (x86)\GBillingServer\server.ini, semua file di
# folder GBillingServer, ProgramData, dan koneksi port lokal gcbServer.exe
# =============================================================================

Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host "   FAUKAY E-SPORT - GCBSERVER DEEP INSPECTOR (PC KASIR)     " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host ""

$gcbDir = "C:\Program Files (x86)\GBillingServer"
$iniPath = "$gcbDir\server.ini"

Write-Host "[1/4] Isi File server.ini:" -ForegroundColor Cyan
if (Test-Path $iniPath) {
    Get-Content $iniPath | ForEach-Object { Write-Host "  $_" -ForegroundColor Green }
} else {
    Write-Host "  File server.ini tidak ditemukan di $iniPath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/4] Semua File di dalam $gcbDir :" -ForegroundColor Cyan
if (Test-Path $gcbDir) {
    Get-ChildItem -Path $gcbDir -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  $($_.FullName) ($($_.Length) bytes)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[3/4] Mencari Database GBilling di C:\ProgramData & AppData:" -ForegroundColor Cyan
$extraPaths = @(
    "C:\ProgramData",
    "$env:LOCALAPPDATA",
    "$env:APPDATA"
)
foreach ($ep in $extraPaths) {
    Get-ChildItem -Path $ep -Directory -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -match "gbilling|cyber|gcb|gcafe|billing"
    } | ForEach-Object {
        Write-Host "  -> Folder Data: $($_.FullName)" -ForegroundColor Green
        Get-ChildItem -Path $_.FullName -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "     $($_.FullName) ($($_.Length) bytes)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "[4/4] Port Jaringan yang dipakai gcbServer.exe:" -ForegroundColor Cyan
$gcbProc = Get-Process -Name "gcbServer" -ErrorAction SilentlyContinue
if ($gcbProc) {
    $pidVal = $gcbProc.Id
    Write-Host "  gcbServer aktif dengan PID: $pidVal (Judul: $($gcbProc.MainWindowTitle))" -ForegroundColor Green
    Get-NetTCPConnection -OwningProcess $pidVal -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State | Format-Table -AutoSize
} else {
    Write-Host "  gcbServer sedang tidak berjalan." -ForegroundColor Red
}
