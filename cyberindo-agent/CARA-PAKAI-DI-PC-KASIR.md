# Panduan Menghubungkan Website Faukay E-Sport ke PC Kasir (CyberIndo Billing)

Saat Anda sudah berada di **PC Server Kasir** tempat aplikasi **CyberIndo Billing Server** berjalan, ikuti 3 langkah mudah berikut:

---

## Langkah 1: Deteksi Lokasi & Proses CyberIndo di PC Kasir
1. Copy folder `cyberindo-agent` ini ke PC Kasir (misal di `C:\cyberindo-agent`).
2. Buka **PowerShell** di PC Kasir, lalu jalankan:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\inspect-cyberindo.ps1
   ```
3. Script tersebut akan menampilkan:
   - Nama proses dan judul jendela aplikasi **CyberIndo Billing Server**.
   - Lokasi file database lokal CyberIndo (jika ada).

---

## Langkah 2: Jalankan Pembaca Otomatis CyberIndo (`cyberindo-ui-reader.py`)
Karena sebagian besar versi CyberIndo mengenkripsi file database-nya, cara paling stabil dan aman (tanpa menyentuh/merusak database kasir) adalah membaca langsung tabel daftar PC (`Nama PC`, `Status`, `Sisa Waktu`) dari jendela aplikasi **CyberIndo Billing Server**:

1. Pastikan Python 3 terinstal di PC Kasir, lalu jalankan sekali perintah ini di Command Prompt / PowerShell:
   ```powershell
   pip install pywinauto requests
   ```
2. Jalankan pembaca otomatis CyberIndo:
   ```powershell
   python .\cyberindo-ui-reader.py --url https://alamat-website-anda.vercel.app/api/pcs
   ```
   *(Jika website dijalankan di jaringan lokal yang sama, gunakan `http://localhost:3000/api/pcs`)*.

---

## Langkah 3: Sesuaikan Penamaan PC (Jika Perlu)
Secara otomatis script akan mengenali:
- **Zona VVIP (18 PC)**: `VVIP-01` s/d `VVIP-18`
- **Zona VIP (28 PC)**: `VIP-07` s/d `VIP-36` (Anda juga bisa memilih 2 nomor VIP mana yang dilewati langsung dari tombol **"Atur PC VIP"** di pojok kanan atas website).
