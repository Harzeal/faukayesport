# Faukay E-Sport — Real-Time CyberIndo Billing Monitor Specification

## 1. Overview & Goals
Website pemantauan status PC dan sisa waktu *real-time* untuk warnet **Faukay E-Sport** yang menggunakan sistem billing **CyberIndo**.
Pengunjung (pelanggan warnet dari HP/rumah maupun layar monitor di warnet) dapat melihat:
- PC mana saja yang **Kosong (Available)** dan siap dipakai.
- PC mana saja yang **Sedang Digunakan (In Use)** beserta **Sisa Waktu Real-Time (`HH:MM:SS`)** yang berjalan mundur setiap detik.
- PC mana yang waktunya **Segera Habis (< 15 menit)** sehingga pelanggan tahu kursi mana yang sebentar lagi kosong.
- Pembagian ruangan/kategori: **Zona VVIP (18 PC: VVIP 01–18)** dan **Zona VIP (28 PC: VIP 07–36 dengan 2 nomor dilewati yang dapat dikonfigurasi)**.

---

## 2. Frontend Visual Design System (Faukay E-Sport Brand Identity)

Berdasarkan logo resmi **FAUKAY E-SPORT (`FK`)**:

### Color Palette (Named Hex Tokens)
- `Obsidian Void` (`#070709`): Background utama halaman (sesuai latar belakang hitam pekat pada logo).
- `Carbon Surface` (`#111216`): Permukaan kartu PC dan panel kontrol.
- `Faukay Amber Orange` (`#EA8215`): Warna aksen utama darilambang perisai `FK` dan teks `FAUKAY`. Digunakan untuk highlight aktif, border geometris, dan identitas utama.
- `Esport Crimson Red` (`#E50914`): Warna aksen sekunder dari pita `E-SPORT`. Digunakan untuk badge VVIP, peringatan waktu hampir habis, dan aksen kontras.
- `Emerald Ready` (`#10B981`): Indikator tegas untuk **PC KOSONG / READY**.
- `Crisp White` (`#F8FAFC`) & `Steel Muted` (`#8E95A5`): Tipografi utama dan sekunder.

### Typography
- **Display / Heading (`Chakra Petch` / `Rajdhani`)**: Mengikuti karakter huruf miring-geometris tegas pada tulisan `FAUKAY E-SPORT`. Digunakan pada nama PC (`VVIP-01`, `VIP-07`), header ruangan, dan angka ringkasan.
- **Monospace Timer (`JetBrains Mono`)**: Khusus untuk hitung mundur sisa waktu `HH:MM:SS` agar lebar karakter angka tidak bergeser setiap detik (`tabular-nums`).
- **Body (`Plus Jakarta Sans` / `Inter`)**: Teks informasi pendukung, filter, dan panduan.

### Layout & Aesthetic Principles
- **Tactical Arena Telemetry (Non-Generic Layout)**: Alih-alih kartu bulat standar, setiap kursi PC dirancang seperti **modul HUD/Telemetry Esport** dengan sudut terpotong (*chamfered/clipped corners* `clip-path`) terinspirasi dari bingkai siku putih `[ FAUKAY ]` pada logo.
- **Spend Boldness on the Live Telemetry Grid**: Fokus utama layar langsung pada bar ringkasan ketersediaan real-time dan denah kursi **VVIP** & **VIP** dengan *countdown timer* yang menyala.

```
+-------------------------------------------------------------------------+
| [LOGO FK] FAUKAY E-SPORT             [LIVE SYNC: ONLINE] [SIMULATOR ON] |
+-------------------------------------------------------------------------+
| [ TOTAL: 46 PC ]  [ KOSONG: 14 PC ]  [ MAIN: 32 PC ]  [ <15 MNT: 5 PC ] |
+-------------------------------------------------------------------------+
| FILTER ZONA: [ SEMUA (46) ] [ ZONA VVIP (18) ] [ ZONA VIP (28) ]        |
| STATUS:      [ SEMUA ] [ HANYA KOSONG ] [ SEGERA HABIS ]   [Cari PC...] |
+-------------------------------------------------------------------------+
| === ZONA VVIP (PC 01 - 18) ============================================ |
| +--------------+ +--------------+ +--------------+ +--------------+     |
| | VVIP-01 [ON] | | VVIP-02 [OK] | | VVIP-03 [!!] | | VVIP-04 [ON] | ... |
| | 01:42:18     | | KOSONG       | | 00:08:45     | | 02:15:00     |     |
| | [======----] | | SIAP PAKAI   | | SEGERA HABIS | | [========--] |     |
| +--------------+ +--------------+ +--------------+ +--------------+     |
|                                                                         |
| === ZONA VIP (PC 07 - 36 | 28 UNIT) =================================== |
| +--------------+ +--------------+ +--------------+ +--------------+     |
| | VIP-07  [OK] | | VIP-08  [ON] | | VIP-09  [ON] | | VIP-10  [OK] | ... |
+-------------------------------------------------------------------------+
```

---

## 3. System Architecture & Data Flow

### Komponen Sistem
1. **Next.js Web App (`src/`)**:
   - `GET /api/pcs`: Mengembalikan daftar status seluruh PC beserta `remainingSeconds` yang dihitung secara presisi berdasarkan waktu sinkronisasi terakhir (`lastUpdatedAt`).
   - `POST /api/pcs/sync`: Endpoint berkeamanan API Key (`FAUKAY_SYNC_SECRET`) untuk menerima push data dari **CyberIndo Agent** di PC Kasir.
   - `POST /api/pcs/simulate`: Mengaktifkan/mengacak ulang simulasi real-time untuk pengujian lokal sebelum disambungkan ke PC Kasir.
   - **Client-Side 1-Second Ticker**: Mengurangi `remainingSeconds` setiap 1 detik di browser pengunjung dan melakukan *re-fetch* otomatis setiap 5 detik.

2. **CyberIndo Local Agent (`cyberindo-agent/`)**:
   Program jembatan yang nanti dicopy ke **PC Server Kasir CyberIndo**, dilengkapi dengan:
   - `inspect-cyberindo.ps1` / `inspect-cyberindo.js`: Script pendeteksi otomatis folder instalasi CyberIndo Billing Server, file database lokal, dan jendela aplikasi kasir.
   - `agent.js` / `ui-reader.py`: Script sinkronisasi yang membaca daftar PC + sisa waktu dari CyberIndo Server (mendukung mode **UI Automation pembaca tabel CyberIndo Server**, **Database Reader**, dan **Simulation Mode**) lalu mengirimkannya ke website Faukay E-Sport setiap 3–5 detik.
