"""
FAUKAY E-SPORT — CyberIndo Billing (gcbServer.exe) Live Reader
==============================================================
Disesuaikan khusus untuk proses:
  C:\\Program Files (x86)\\GBillingServer\\gcbServer.exe
  (Judul jendela mengikuti shift kasir, misal: 'MALAM (Staff)' atau 'PAGI (Staff)')

Cara Jalankan di PC Kasir:
  Klik 2x file 2-JALANKAN-SYNC.bat
"""

import argparse
import os
import re
import subprocess
import time
import requests

try:
    from pywinauto import Application, Desktop
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False


def get_gcbserver_pid():
    """Cari PID dari proses gcbServer.exe yang sedang berjalan di Windows."""
    try:
        out = subprocess.check_output(
            ['tasklist', '/FI', 'IMAGENAME eq gcbServer.exe', '/FO', 'CSV', '/NH'],
            text=True,
             stderr=subprocess.DEVNULL,
        ).strip()
        # Format CSV: "gcbServer.exe","5108","Console","1","45,120 K"
        match = re.search(r'"gcbServer\.exe","(\d+)"', out, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None


def inspect_server_ini():
    """Baca konfigurasi C:\\Program Files (x86)\\GBillingServer\\server.ini jika ada."""
    ini_path = r"C:\Program Files (x86)\GBillingServer\server.ini"
    if os.path.exists(ini_path):
        try:
            with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
                print(f"[INFO] Isi server.ini:\n{content}\n")
        except Exception as e:
            print(f"[WARN] Gagal membaca server.ini: {e}")


def parse_hms_to_seconds(text: str) -> int:
    """Cari pola waktu HH:MM:SS atau HH:MM dari teks baris tabel CyberIndo."""
    if not text:
        return 0
    # Cari semua pola waktu di dalam baris
    hms_matches = re.findall(r"\b(\d{1,2}):(\d{2}):(\d{2})\b", text)
    if hms_matches:
        # Biasanya kolom Sisa Waktu berada di bagian tengah/akhir
        h, m, s = map(int, hms_matches[-1])
        return h * 3600 + m * 60 + s

    hm_matches = re.findall(r"\b(\d{1,2}):(\d{2})\b", text)
    if hm_matches:
        h, m = map(int, hm_matches[-1])
        return h * 3600 + m * 60

    return 0


def map_pc_name_to_id(raw_text: str):
    """
    Cocokkan nama workstation CyberIndo ke ID Faukay E-Sport:
    - VVIP-01 s/d VVIP-18
    - VIP-07 s/d VIP-36 (atau PC-07 s/d PC-36)
    """
    upper = raw_text.upper()

    # Cek apakah ada kata VVIP diikuti angka
    vvip_match = re.search(r"\bVVIP[\s\-_]*0*(\d{1,2})\b", upper)
    if vvip_match:
        num = int(vvip_match.group(1))
        if 1 <= num <= 18:
            return f"VVIP-{num:02d}"

    # Cek apakah ada kata VIP atau PC atau klien diikuti angka
    vip_match = re.search(r"\b(?:VIP|PC|CLIENT|NO)?[\s\-_]*0*(\d{1,2})\b", upper)
    if vip_match:
        num = int(vip_match.group(1))
        if 1 <= num <= 18 and "VIP" not in upper:
            # Jika penomoran 1-18 adalah VVIP
            return f"VVIP-{num:02d}"
        if 7 <= num <= 36:
            return f"VIP-{num:02d}"

    return None


def read_gcbserver_ui(first_run: bool = False):
    """Hubungkan langsung ke proses gcbServer.exe (PID) dan baca tabel PC."""
    if not HAS_PYWINAUTO:
        raise RuntimeError("Modul pywinauto belum terinstall. Jalankan: pip install pywinauto requests")

    pid = get_gcbserver_pid()
    if not pid:
        print("[WARN] Proses gcbServer.exe tidak ditemukan! Pastikan aplikasi CyberIndo Billing terbuka.")
        return []

    pcs_map = {}

    for backend in ("uia", "win32"):
        try:
            app = Application(backend=backend).connect(process=pid)
            windows = app.windows()
            if not windows:
                continue

            main_win = windows[0]
            if first_run:
                print(f"[INFO] Terhubung ke gcbServer.exe (PID: {pid}, Backend: {backend}, Judul: '{main_win.window_text()}')")

            # Ambil semua elemen di dalam jendela gcbServer
            descendants = main_win.descendants()
            if first_run:
                print(f"[DEBUG] Ditemukan {len(descendants)} elemen UI di dalam jendela gcbServer.")
                sample_texts = []
                for d in descendants:
                    try:
                        t_list = [t.strip() for t in d.texts() if t and t.strip()]
                        cname = d.friendly_class_name()
                        if t_list:
                            sample_texts.append(f"{cname}: {' | '.join(t_list[:6])}")
                    except Exception:
                        pass
                print("[DEBUG] Contoh 20 teks elemen pertama yang terbaca dari gcbServer:")
                for st in sample_texts[:20]:
                    print("   ->", st)

            for elem in descendants:
                try:
                    texts = [str(t).strip() for t in elem.texts() if t and str(t).strip()]
                    if not texts:
                        continue
                    joined = " | ".join(texts)
                    pc_id = map_pc_name_to_id(joined)
                    if not pc_id:
                        continue

                    rem_sec = parse_hms_to_seconds(joined)
                    upper_joined = joined.upper()
                    is_maint = any(k in upper_joined for k in ["RUSAK", "MAINT", "OFFLINE"])
                    is_active = rem_sec > 0 or any(
                        k in upper_joined
                        for k in ["ONLINE", "MEMBER", "PAKET", "PERSONAL", "BERMAIN", "DIGUNAKAN", "IN USE"]
                    )

                    if is_maint and not is_active:
                        status = "MAINTENANCE"
                    elif is_active:
                        status = "IN_USE"
                    else:
                        status = "AVAILABLE"

                    # Simpan data terlengkap untuk tiap pc_id
                    prev = pcs_map.get(pc_id)
                    if not prev or rem_sec > prev["remainingSeconds"]:
                        pcs_map[pc_id] = {
                            "id": pc_id,
                            "status": status,
                            "remainingSeconds": rem_sec if status == "IN_USE" else 0,
                            "totalSeconds": max(rem_sec, 7200) if status == "IN_USE" else 0,
                            "packageType": "Billing CyberIndo" if status == "IN_USE" else "Siap Pakai",
                        }
                except Exception:
                    continue

            if pcs_map:
                break
        except Exception as e:
            if first_run:
                print(f"[DEBUG] Backend {backend} info: {e}")

    return list(pcs_map.values())


def main():
    parser = argparse.ArgumentParser(description="Faukay E-Sport gcbServer.exe Live Reader")
    parser.add_argument("--url", default="http://localhost:3000/api/pcs", help="URL API Website Faukay E-Sport")
    parser.add_argument("--secret", default="", help="Secret key FAUKAY_SYNC_SECRET (opsional)")
    parser.add_argument("--interval", type=int, default=3, help="Interval update dalam detik (default: 3)")
    args = parser.parse_args()

    print("============================================================")
    print(" FAUKAY E-SPORT — GCBSERVER (CYBERINDO) LIVE READER")
    print(f" Target API : {args.url}")
    print(f" Interval   : {args.interval} detik")
    print("============================================================")

    inspect_server_ini()
    first_run = True

    while True:
        try:
            pcs_data = read_gcbserver_ui(first_run=first_run)
            first_run = False

            if pcs_data:
                res = requests.post(
                    args.url,
                    json={
                        "secret": args.secret,
                        "source": "CYBERINDO_AGENT",
                        "pcs": pcs_data,
                    },
                    timeout=5,
                )
                active_cnt = sum(1 for p in pcs_data if p["status"] == "IN_USE")
                print(
                    f"[{time.strftime('%H:%M:%S')}] SYNC OK -> Terbaca {len(pcs_data)} PC ({active_cnt} Aktif) -> HTTP {res.status_code}"
                )
            else:
                print(
                    f"[{time.strftime('%H:%M:%S')}] [INFO] gcbServer terdeteksi, namun baris tabel PC belum terbaca. Pastikan jendela utama Billing tidak di-minimize ke tray."
                )
        except Exception as err:
            print(f"[{time.strftime('%H:%M:%S')}] [ERROR] {err}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
