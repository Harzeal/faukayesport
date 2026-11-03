# =============================================================================
# FAUKAY E-SPORT — CyberIndo Billing Server Inspector
# Jalankan script ini di PC Server Kasir untuk mendeteksi otomatis:
# 1. Proses aplikasi CyberIndo Billing yang sedang berjalan
# 2. Lokasi folder instalasi & file database (.db, .sqlite, .mdb, .fdb, .ini)
# 3. Port TCP lokal yang digunakan CyberIndo Server
# =============================================================================

Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host "   FAUKAY E-SPORT - CYBERINDO BILLING INSPECTOR (PC KASIR)  " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host ""

# 1. Cari proses CyberIndo / GCafePro / Billing yang sedang jalan
Write-Host "[1/3] Mencari Proses CyberIndo Billing yang sedang aktif..." -ForegroundColor Cyan
$procs = Get-Process | Where-Object {
    $_.ProcessName -match "cyber|billing|gcafe|gbilling|server|cafe" -or
    $_.MainWindowTitle -match "Cyberindo|Billing|GCafe"
}

if ($procs) {
    foreach ($p in $procs) {
        $path = try { $p.MainModule.FileName } catch { "Akses Path membutuhkan Run as Administrator" }
        Write-Host "  -> Ditemukan Proses : $($p.ProcessName) (PID: $($p.Id))" -ForegroundColor Green
        Write-Host "     Judul Jendela    : $($p.MainWindowTitle)"
        Write-Host "     Lokasi File EXE  : $path"
    }
} else {
    Write-Host "  -> Belum ditemukan proses dengan nama CyberIndo yang sedang jalan." -ForegroundColor Yellow
    Write-Host "     Pastikan aplikasi CyberIndo Billing Server sedang terbuka di PC Kasir."
}

Write-Host ""
Write-Host "[2/3] Mencari Folder Instalasi & File Database CyberIndo..." -ForegroundColor Cyan
$searchRoots = @(
    "C:\Program Files",
    "C:\Program Files (x86)",
    "C:\Cyberindo",
    "D:\Cyberindo",
    "D:\Billing",
    "E:\Cyberindo"
)

foreach ($root in $searchRoots) {
    if (Test-Path $root) {
        $foundFolders = Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -match "cyber|gcafe|billing"
        }
        foreach ($folder in $foundFolders) {
            Write-Host "  -> Folder Ditemukan: $($folder.FullName)" -ForegroundColor Green
            $dbFiles = Get-ChildItem -Path $folder.FullName -Recurse -Include *.db, *.sqlite, *.sqlite3, *.mdb, *.fdb, *.ini, *.xml -ErrorAction SilentlyContinue
            foreach ($f in $dbFiles) {
                Write-Host "     [FILE DATA] $($f.FullName) ($($f.Length) bytes)" -ForegroundColor Gray
            }
        }
    }
}

Write-Host ""
Write-Host "[3/3] Selesai! Foto atau copy hasil di atas untuk menyesuaikan reader bila diperlukan." -ForegroundColor Green
