"""
FAUKAY E-SPORT — CyberIndo Pro Server v1.8.5 (gcbServer.exe) Live Reader
========================================================================
Mendukung:
1. Pembacaan Folder Database (D:/DataBaseBilling/GBillingServer)
2. Pembacaan 702 Elemen UI & Legacy Accessible Properties (gcbServer.exe)
3. Pembacaan Memori Proses (RAM QString UTF-16LE / UTF-8) gcbServer.exe
4. Format waktu CyberIndo Indonesia: "6j 59m", "1j 8m", "30m", "6m"
"""

import argparse
import ctypes
from ctypes import wintypes
import os
import re
import sqlite3
import subprocess
import time
import warnings
import requests

warnings.filterwarnings("ignore")

try:
    from pywinauto import Application
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False


def normalize_api_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if not url:
        url = "https://faukayesport-fky.vercel.app"
    if not url.startswith("http://") and not url.startswith("https://"):
        if "localhost" in url or "127.0.0.1" in url or url.startswith("192.168."):
            url = "http://" + url
        else:
            url = "https://" + url
    if not url.endswith("/api/pcs"):
        url = url.rstrip("/") + "/api/pcs"
    return url


def get_gcbserver_pid():
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq gcbServer.exe", "/FO", "CSV", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        match = re.search(r'"gcbServer\.exe","(\d+)"', out, re.IGNORECASE)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None


def parse_cyberindo_time_to_seconds(text: str) -> int:
    """
    Format CyberIndo Pro Indonesia (Nation=ID):
    - '6j 59m' -> 6 jam 59 menit
    - '2j 0m'  -> 2 jam 0 menit
    - '30m'    -> 30 menit
    - '6m'     -> 6 menit
    - '01:45:20' -> 1 jam 45 menit 20 detik
    """
    if not text:
        return 0

    # 1. Cek pola "6j 59m" atau "1j 8m"
    jm = re.search(r"\b(\d{1,2})\s*j\s*(\d{1,2})\s*m\b", text, re.IGNORECASE)
    if jm:
        h, m = int(jm.group(1)), int(jm.group(2))
        return h * 3600 + m * 60

    # 2. Cek pola hanya menit "30m" atau "6m"
    m_only = re.search(r"\b(\d{1,3})\s*m\b", text, re.IGNORECASE)
    if m_only:
        return int(m_only.group(1)) * 60

    # 3. Cek pola HH:MM:SS
    hms = re.search(r"\b(\d{1,2}):(\d{2}):(\d{2})\b", text)
    if hms:
        h, m, s = map(int, hms.groups())
        return h * 3600 + m * 60 + s

    return 0


def inspect_database_folder():
    """Periksa semua file di D:/DataBaseBilling/GBillingServer dari server.ini."""
    data_folder = r"D:\DataBaseBilling\GBillingServer"
    ini_path = r"C:\Program Files (x86)\GBillingServer\server.ini"

    if os.path.exists(ini_path):
        try:
            with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().lower().startswith("datafolder="):
                        data_folder = line.split("=", 1)[1].strip().replace("/", "\\")
        except Exception:
            pass

    print(f"\n[1/3] Memeriksa Folder Database: {data_folder}")
    if not os.path.exists(data_folder):
        print(f"  -> Folder {data_folder} tidak ditemukan.")
        return

    for root, dirs, files in os.walk(data_folder):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                sz = os.path.getsize(fpath)
                mtime = time.strftime("%H:%M:%S %d/%m", time.localtime(os.path.getmtime(fpath)))
                header = b""
                with open(fpath, "rb") as bf:
                    header = bf.read(16)
                is_sqlite = header.startswith(b"SQLite format 3")
                tag = "SQLITE-OPEN" if is_sqlite else f"HEADER:{header[:10]!r}"
                print(f"  -> {fpath} ({sz} bytes | Update: {mtime} | {tag})")

                if is_sqlite:
                    try:
                        conn = sqlite3.connect(f"file:{fpath}?mode=ro", uri=True)
                        cur = conn.cursor()
                        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                        print(f"     [TABEL SQLITE]: {tables}")
                        conn.close()
                    except Exception as sqle:
                        print(f"     [INFO SQLITE]: {sqle}")
            except Exception as e:
                print(f"  -> {fpath} (Error baca: {e})")


def inspect_ui_elements_deep(pid: int):
    """Periksa properti mendalam dari 702 elemen UI di gcbServer.exe."""
    print(f"\n[2/3] Memeriksa Struktur 702 Elemen UI gcbServer.exe (PID: {pid})...")
    if not HAS_PYWINAUTO:
        return

    try:
        app = Application(backend="uia").connect(process=pid)
        win = app.windows()[0]
        descendants = win.descendants()
        print(f"  -> Total Elemen UI: {len(descendants)}")

        class_counts = {}
        non_empty_samples = []

        for idx, d in enumerate(descendants):
            try:
                ei = d.element_info
                cname = getattr(ei, "class_name", "") or ""
                ctype = getattr(ei, "control_type", "") or ""
                ename = getattr(ei, "name", "") or ""
                key = f"{ctype}({cname})"
                class_counts[key] = class_counts.get(key, 0) + 1

                # Cek legacy IAccessible properties jika ada
                leg_val = ""
                leg_desc = ""
                try:
                    lp = d.legacy_properties()
                    leg_val = str(lp.get("Value", "") or "").strip()
                    leg_desc = str(lp.get("Description", "") or "").strip()
                    if not ename:
                        ename = str(lp.get("Name", "") or "").strip()
                except Exception:
                    pass

                combined = " | ".join(x for x in [ename, leg_val, leg_desc] if x)
                if combined and len(non_empty_samples) < 35:
                    rect = getattr(ei, "rectangle", None)
                    r_str = f"({rect.left},{rect.top})" if rect else ""
                    non_empty_samples.append(f"#{idx} [{key}] {r_str}: {combined}")
            except Exception:
                continue

        print(f"  -> Ringkasan Tipe Elemen: {class_counts}")
        print(f"  -> Elemen dengan Teks/Value ({len(non_empty_samples)} sampel pertama):")
        for s in non_empty_samples:
            print("    ", s)
    except Exception as e:
        print(f"  -> Gagal inspeksi UI mendalam: {e}")


# Konstanta Windows API untuk ReadProcessMemory
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_READONLY = 0x02
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


def scan_gcbserver_memory(pid: int, debug_first: bool = False):
    """
    Membaca string UTF-16LE (Qt4 QString) dan ASCII langsung dari RAM gcbServer.exe!
    Mencari teks kartu PC seperti 'VIP-13', 'VVIP-05', '6j 59m', '30m', dll.
    """
    kernel32 = ctypes.windll.kernel32
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_proc:
        if debug_first:
            print("[WARN] OpenProcess gagal. Pastikan dijalankan sebagai Administrator.")
        return {}

    mbi = MEMORY_BASIC_INFORMATION()
    addr = 0
    max_addr = 0x7FFFFFFF  # gcbServer.exe adalah aplikasi 32-bit!

    found_utf16_snippets = []
    time_strings_found = []

    # Regex UTF-16LE untuk mencari "VIP-" atau "VVIP-"
    vip_pattern_u16 = re.compile(b"(?:V\x00)?V\x00I\x00P\x00-\x00\d\x00\d\x00")
    time_pattern_u16 = re.compile(
        b"(?:\d\x00\d?\x00j\x00 \x00)?\d\x00\d?\x00m\x00"
    )

    try:
        while addr < max_addr:
            res = kernel32.VirtualQueryEx(
                h_proc, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)
            )
            if not res:
                break

            readable = mbi.State == MEM_COMMIT and (
                mbi.Protect in (PAGE_READWRITE, PAGE_READONLY, PAGE_WRITECOPY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE)
            )

            if readable and 0 < mbi.RegionSize <= 32 * 1024 * 1024:
                buf = ctypes.create_string_buffer(mbi.RegionSize)
                bytes_read = ctypes.c_size_t(0)
                if kernel32.ReadProcessMemory(
                    h_proc,
                    ctypes.c_void_p(mbi.BaseAddress),
                    buf,
                    mbi.RegionSize,
                    ctypes.byref(bytes_read),
                ):
                    raw = buf.raw[: bytes_read.value]

                    if debug_first:
                        for m in vip_pattern_u16.finditer(raw):
                            start = max(0, m.start() - 64)
                            end = min(len(raw), m.end() + 160)
                            chunk = raw[start:end].decode("utf-16le", errors="ignore")
                            clean_chunk = re.sub(r"[\x00-\x1f]+", " | ", chunk).strip(" |")
                            if len(found_utf16_snippets) < 40 and clean_chunk not in found_utf16_snippets:
                                found_utf16_snippets.append(clean_chunk)

                        for tm in time_pattern_u16.finditer(raw):
                            t_str = tm.group(0).decode("utf-16le", errors="ignore")
                            if any(c.isdigit() for c in t_str):
                                start = max(0, tm.start() - 96)
                                end = min(len(raw), tm.end() + 96)
                                context = raw[start:end].decode("utf-16le", errors="ignore")
                                clean_ctx = re.sub(r"[\x00-\x1f]+", " | ", context).strip(" |")
                                if ("j " in t_str or "m" in t_str) and len(time_strings_found) < 40:
                                    if re.search(r"\b(?:\d+j\s*)?\d+m\b", clean_ctx):
                                        time_strings_found.append(clean_ctx)

            addr = (mbi.BaseAddress or 0) + mbi.RegionSize
    finally:
        kernel32.CloseHandle(h_proc)

    if debug_first:
        print(f"\n[3/3] Hasil Scan Memori (RAM) gcbServer.exe:")
        print(f"  -> Ditemukan {len(found_utf16_snippets)} blok memori nama PC (VIP/VVIP):")
        for s in found_utf16_snippets[:15]:
            print("     [MEM-PC]  ", s[:120])
        print(f"  -> Ditemukan {len(time_strings_found)} blok memori sisa waktu (Xj Ym):")
        for t in time_strings_found[:20]:
            print("     [MEM-TIME]", t[:120])

    return {}


def get_active_client_ips_port_6895():
    """Fallback deteksi koneksi TCP aktif di port 6895 milik gcbServer.exe."""
    active_ips = set()
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if ":6895 " in line and "ESTABLISHED" in line.upper():
                parts = line.split()
                if len(parts) >= 3:
                    remote_ip = parts[2].split(":")[0]
                    active_ips.add(remote_ip)
    except Exception:
        pass
    return sorted(active_ips)


def main():
    parser = argparse.ArgumentParser(description="Faukay E-Sport gcbServer.exe Live Reader")
    parser.add_argument("--url", default="https://faukayesport-fky.vercel.app/api/pcs", help="URL API Website")
    parser.add_argument("--secret", default="", help="Secret key FAUKAY_SYNC_SECRET")
    parser.add_argument("--interval", type=int, default=4, help="Interval update (detik)")
    args = parser.parse_args()

    api_url = normalize_api_url(args.url)

    print("============================================================")
    print(" FAUKAY E-SPORT — GCBSERVER (CYBERINDO v1.8.5) LIVE READER")
    print(f" Target API : {api_url}")
    print(f" Interval   : {args.interval} detik")
    print("============================================================")

    pid = get_gcbserver_pid()
    if not pid:
        print("[ERROR] gcbServer.exe tidak ditemukan! Pastikan CyberIndo Billing Server berjalan.")
        return

    # Jalankan 3 diagnostik otomatis pada awal start
    inspect_database_folder()
    inspect_ui_elements_deep(pid)
    scan_gcbserver_memory(pid, debug_first=True)

    active_ips = get_active_client_ips_port_6895()
    print(f"\n[INFO] Total IP PC Client ESTABLISHED di Port 6895 saat ini: {len(active_ips)} IP")
    print(f"       Daftar IP: {', '.join(active_ips)}")
    print("\n============================================================")
    print(" Silakan foto hasil [1/3], [2/3], dan [3/3] di atas!")
    print("============================================================")

    while True:
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
