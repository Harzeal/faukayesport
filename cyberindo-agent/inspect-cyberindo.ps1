# =============================================================================
# FAUKAY E-SPORT — Inspector Khusus D:\DataBaseBilling\GBillingServer
# =============================================================================

Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host "   FAUKAY E-SPORT - CEK D:\DataBaseBilling\GBillingServer   " -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor DarkYellow
Write-Host ""

$dataDir = "D:\DataBaseBilling\GBillingServer"

Write-Host "[1/3] Daftar Semua File di $dataDir :" -ForegroundColor Cyan
if (Test-Path $dataDir) {
    Get-ChildItem -Path $dataDir -Recurse -File | Sort-Object LastWriteTime -Descending | ForEach-Object {
        Write-Host ("  {0,-62} | {1,10} bytes | Update: {2}" -f $_.FullName, $_.Length, $_.LastWriteTime.ToString("HH:mm:ss dd/MM/yyyy")) -ForegroundColor Green
    }
} else {
    Write-Host "  Folder $dataDir tidak ditemukan!" -ForegroundColor Red
}

Write-Host ""
Write-Host "[2/3] Cek Header File Database (.db / .sqlite / .dat / .ini / .xml):" -ForegroundColor Cyan
if (Test-Path $dataDir) {
    Get-ChildItem -Path $dataDir -Recurse -File | ForEach-Object {
        try {
            $bytes = [System.IO.File]::ReadAllBytes($_.FullName) | Select-Object -First 16
            $ascii = -join ($bytes | ForEach-Object { if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' } })
            Write-Host ("  {0,-40} -> Header: [{1}]" -f $_.Name, $ascii) -ForegroundColor Gray
        } catch {
            Write-Host ("  {0,-40} -> (Sedang dipakai proses aktif, dicopy sementara...)" -f $_.Name) -ForegroundColor Yellow
            try {
                $tmp = "$env:TEMP\$($_.Name).tmp"
                Copy-Item $_.FullName $tmp -Force
                $bytes = [System.IO.File]::ReadAllBytes($tmp) | Select-Object -First 16
                $ascii = -join ($bytes | ForEach-Object { if ($_ -ge 32 -and $_ -le 126) { [char]$_ } else { '.' } })
                Write-Host ("  {0,-40} -> Header: [{1}]" -f $_.Name, $ascii) -ForegroundColor Green
                Remove-Item $tmp -Force -ErrorAction SilentlyContinue
            } catch {}
        }
    }
}

Write-Host ""
Write-Host "[3/3] Daftar IP PC Client yang Sedang Terhubung ke Billing (Port 6895):" -ForegroundColor Cyan
$conns = Get-NetTCPConnection -LocalPort 6895 -State Established -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty RemoteAddress -Unique |
    Sort-Object { [version]$_ }

Write-Host "  Total IP PC Client Aktif Terhubung: $($conns.Count) PC" -ForegroundColor Green
Write-Host "  Daftar IP: $($conns -join ', ')" -ForegroundColor Gray
