"""
FAUKAY E-SPORT — CyberIndo Billing UI Table Reader (Windows UI Automation)
==========================================================================
Script ini berjalan di PC Server Kasir (Windows) tempat CyberIndo Billing Server aktif.
Membaca tabel daftar PC (Nama PC, Status, Sisa Waktu) langsung dari tampilan aplikasi
CyberIndo Billing Server dan mengirimkannya secara real-time ke Website Faukay E-Sport.

Cara Install di PC Kasir:
    pip install pywinauto requests

Cara Jalankan:
    python cyberindo-ui-reader.py --url http://localhost:3000/api/pcs
"""

import argparse
import re
import time
import requests

try:
    from pywinauto import Desktop
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False


def parse_hms_to_seconds(time_str: str) -> int:
    """Ubah format waktu '01:45:20' atau '01:45' menjadi detik."""
    if not time_str:
        return 0
    clean = time_str.strip()
    match_hms = re.search(r"(\d{1,2}):(\d{2}):(\d{2})", clean)
    if match_hms:
        h, m, s = map(int, match_hms.groups())
        return h * 3600 + m * 60 + s

    match_hm = re.search(r"(\d{1,2}):(\d{2})", clean)
    if match_hm:
        h, m = map(int, match_hm.groups())
        return h * 3600 + m * 60

    return 0


def map_pc_name_to_id(raw_name: str):
    """Cocokkan nama workstation CyberIndo ke format ID Faukay E-Sport (VVIP-01..18, VIP-07..36)."""
    upper = raw_name.upper().strip()
    num_match = re.search(r"(\d+)", upper)
    if not num_match:
        return None
    num = int(num_match.group(1))
    if "VVIP" in upper:
        return f"VVIP-{num:02d}"
    return f"VIP-{num:02d}"


def read_cyberindo_window(window_regex: str):
    """Membaca baris list PC dari jendela aplikasi CyberIndo Billing Server."""
    if not HAS_PYWINAUTO:
        raise RuntimeError("Modul pywinauto belum terinstall. Jalankan: pip install pywinauto requests")

    windows = Desktop(backend="uia").windows(title_re=window_regex)
    if not windows:
        windows = Desktop(backend="win32").windows(title_re=window_regex)

    if not windows:
        print(f"[WARN] Jendela aplikasi dengan judul '{window_regex}' belum ditemukan.")
        return []

    win = windows[0]
    pcs_payload = []

    # Cari semua elemen ListItem / DataItem pada tabel daftar workstation CyberIndo
    items = win.descendants(control_type="DataItem") or win.descendants(control_type="ListItem")
    for item in items:
        texts = [t.strip() for t in item.texts() if t and t.strip()]
        joined = " | ".join(texts)
        pc_id = map_pc_name_to_id(joined)
        if not pc_id:
            continue

        remaining_sec = parse_hms_to_seconds(joined)
        is_online = remaining_sec > 0 or any(
            k in joined.upper() for k in ["ONLINE", "PAKAI", "MEMBER", "PAKET", "MAIN", "AKTIF"]
        )

        pcs_payload.append({
            "id": pc_id,
            "status": "IN_USE" if is_online else "AVAILABLE",
            "remainingSeconds": remaining_sec if is_online else 0,
            "totalSeconds": max(remaining_sec, 7200) if is_online else 0,
            "packageType": "Billing CyberIndo" if is_online else "Siap Pakai",
        })

    return pcs_payload


def main():
    parser = argparse.ArgumentParser(description="Faukay E-Sport CyberIndo Live Reader")
    parser.add_argument("--url", default="http://localhost:3000/api/pcs", help="URL API Website Faukay E-Sport")
    parser.add_argument("--secret", default="", help="Secret key FAUKAY_SYNC_SECRET (opsional)")
    parser.add_argument("--window", default=".*(Cyberindo|Billing|GCafe).*", help="Regex judul jendela CyberIndo")
    parser.add_argument("--interval", type=int, default=3, help="Interval update dalam detik (default: 3)")
    args = parser.parse_args()

    print("============================================================")
    print(" FAUKAY E-SPORT — CYBERINDO LIVE READER AGENT")
    print(f" Target API : {args.url}")
    print(f" Interval   : {args.interval} detik")
    print("============================================================")

    while True:
        try:
            pcs_data = read_cyberindo_window(args.window)
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
                print(f"[SYNC OK] Mengirim {len(pcs_data)} status PC -> HTTP {res.status_code}")
            else:
                print("[INFO] Menunggu data tabel PC dari jendela CyberIndo...")
        except Exception as err:
            print(f"[ERROR] {err}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
