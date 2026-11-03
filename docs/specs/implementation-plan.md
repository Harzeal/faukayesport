# Faukay E-Sport — Implementation Plan

## File Structure
- `package.json`, `tsconfig.json`, `next.config.mjs`: Konfigurasi Next.js (App Router + TypeScript).
- `public/logo.png`: Logo resmi Faukay E-Sport yang diunggah pengguna.
- `src/types/pc.ts`: Definisi tipe data PC (`PCUnit`, `PCZone`, `PCStatus`, `BillingSyncPayload`, `ArenaSummary`).
- `src/lib/pc-config.ts`: Konfigurasi default 18 PC VVIP (`VVIP-01` s/d `VVIP-18`) dan 28 PC VIP (`VIP-07` s/d `VIP-36` dengan 2 nomor dilewati yang dapat diatur), serta helper kalkulasi sisa waktu real-time.
- `src/lib/pc-store.ts`: Penyimpanan state status PC (mendukung penyimpanan lokal & siap dihubungkan ke cloud/API) beserta generator simulasi realistis dan fungsi sinkronisasi dari CyberIndo Agent.
- `src/app/api/pcs/route.ts`: Endpoint `GET /api/pcs` (ambil status live semua PC) & `POST /api/pcs` (update status/sync dari CyberIndo Agent atau kontrol kasir).
- `src/app/globals.css`: Sistem desain CSS bertema **Faukay E-Sport** (`#070709` Obsidian, `#EA8215` Cyber Orange, `#E50914` Crimson Red, sudut *chamfered*, font *Chakra Petch* & *JetBrains Mono*).
- `src/app/layout.tsx` & `src/app/page.tsx`: Halaman utama monitor real-time Faukay E-Sport dengan Live Countdown per detik, Filter Zona (VVIP / VIP / Kosong / Segera Habis), Pencarian PC, Modal Detail/Kontrol Kasir & Konfigurasi Nomor VIP yang Dilewati, serta Panduan Koneksi CyberIndo.
- `cyberindo-agent/`:
  - `inspect-cyberindo.ps1`: Script PowerShell sekali klik untuk dijalankan di PC Kasir guna mendeteksi lokasi instalasi CyberIndo, proses aktif, port lokal, dan file database.
  - `agent.js`: Script Node.js pengirim data real-time dari PC Kasir ke website Faukay E-Sport.
  - `cyberindo-ui-reader.py`: Script Python pembaca tabel aplikasi CyberIndo Billing Server secara otomatis (Windows UI Automation).
  - `CARA-PAKAI-DI-PC-KASIR.md`: Panduan langkah demi langkah berbahasa Indonesia untuk memasang agent di PC Kasir.

## Verification Steps
1. Unit test logika daftar PC (18 VVIP + 28 VIP = 46 PC) dan kalkulasi sisa waktu real-time.
2. Jalankan Next.js server dan verifikasi endpoint `GET /api/pcs` & `POST /api/pcs`.
3. Verifikasi tampilan UI dan fitur hitung mundur *real-time*.
