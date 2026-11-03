"""
FAUKAY E-SPORT — CyberIndo Pro Server v1.8.5 (gcbServer.exe) Live Reader
========================================================================
Membaca:
1. Isi file log aktif D:\\DataBaseBilling\\GBillingServer\\Logs\\gbServer-YYYYMMDD.log
2. Struktur C++ Workstation / QString Pointer di RAM gcbServer.exe
3. Elemen UI pada tab 'Komputer'
"""

import argparse
import ctypes
from ctypes import wintypes
import glob
import os
import re
import struct
import subprocess
import time
import warnings

warnings.filterwarnings("ignore")

try:
    from pywinauto import Application
    HAS_PYWINAUTO = True
except ImportError:
    HAS_PYWINAUTO = False


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


def inspect_latest_log_file():
    """Baca baris terakhir & baris penting dari D:\\DataBaseBilling\\GBillingServer\\Logs\\gbServer-*.log"""
    log_dir = r"D:\DataBaseBilling\GBillingServer\Logs"
    print(f"\n[1/3] Memeriksa File Log Terbaru di: {log_dir}")
    if not os.path.exists(log_dir):
        print("  -> Folder Logs tidak ditemukan.")
        return

    log_files = sorted(glob.glob(os.path.join(log_dir, "gbServer-*.log")), key=os.path.getmtime, reverse=True)
    if not log_files:
        print("  -> Tidak ada file gbServer-*.log.")
        return

    latest = log_files[0]
    print(f"  -> File Log Aktif: {latest} ({os.path.getsize(latest)} bytes)")
    try:
        with open(latest, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]

        print(f"  -> Total Baris Log: {len(lines)}")
        print("  -> 20 Baris Terakhir di Log:")
        for ln in lines[-20:]:
            print("    ", ln[:140])

        vip_lines = [ln for ln in lines if re.search(r"VIP|192\.168\.10\.|login|order|time|session", ln, re.I)]
        print(f"  -> 15 Baris Log Terkait PC / IP / Session (dari total {len(vip_lines)} cocok):")
        for ln in vip_lines[-15:]:
            print("    ", ln[:140])
    except Exception as e:
        print(f"  -> Gagal baca log: {e}")


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
READABLE_PAGES = (0x02, 0x04, 0x08, 0x20, 0x40)


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


def map_qstrings_and_structs(pid: int):
    """
    Melacak pointer Qt4 QStringData di RAM gcbServer.exe untuk menghubungkan
    Nama PC ('VIP-13', 'VVIP-05') dengan Sisa Waktu ('6j 59m', '2j 20m') dan Username!
    """
    print(f"\n[2/3] Melacak Tabel Objek PC & Pointer QString di RAM gcbServer.exe (PID: {pid})...")
    kernel32 = ctypes.windll.kernel32
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_proc:
        print("  -> Gagal OpenProcess.")
        return

    mbi = MEMORY_BASIC_INFORMATION()
    addr = 0
    max_addr = 0x7FFFFFFF

    regions = []
    try:
        while addr < max_addr:
            res = kernel32.VirtualQueryEx(h_proc, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
            if not res:
                break
            if mbi.State == MEM_COMMIT and mbi.Protect in READABLE_PAGES and 0 < mbi.RegionSize <= 32 * 1024 * 1024:
                buf = ctypes.create_string_buffer(mbi.RegionSize)
                bytes_read = ctypes.c_size_t(0)
                if kernel32.ReadProcessMemory(
                    h_proc, ctypes.c_void_p(mbi.BaseAddress), buf, mbi.RegionSize, ctypes.byref(bytes_read)
                ):
                    regions.append((mbi.BaseAddress, buf.raw[: bytes_read.value]))
            addr = (mbi.BaseAddress or 0) + mbi.RegionSize
    finally:
        kernel32.CloseHandle(h_proc)

    print(f"  -> Berhasil membaca {len(regions)} region memori.")

    # 1. Cari alamat QStringData untuk waktu aktif (misal "5j 19m", "2j 20m", "1j 53m", dll.)
    time_re = re.compile(b"\x00((?:\d\x00\d?\x00j\x00 \x00)?\d\x00\d?\x00m\x00)\x00\x00")
    pc_re = re.compile(b"((?:V\x00)?V\x00I\x00P\x00-\x00\d\x00\d\x00)\x00\x00")

    qstring_time_headers = {}  # header_addr -> time_str
    qstring_pc_headers = {}    # header_addr -> pc_str

    for base, raw in regions:
        for m in time_re.finditer(raw):
            str_offset = m.start(1)
            t_str = m.group(1).decode("utf-16le", errors="ignore")
            if not re.match(r"^(?:\d{1,2}j )?\d{1,2}m$", t_str):
                continue
            # Di Qt4 32-bit, QStringData header berada 16 atau 20 byte sebelum karakter pertama
            for hdr_delta in (16, 20):
                if str_offset >= hdr_delta:
                    hdr_addr = base + str_offset - hdr_delta
                    qstring_time_headers[hdr_addr] = t_str

        for m in pc_re.finditer(raw):
            str_offset = m.start(1)
            p_str = m.group(1).decode("utf-16le", errors="ignore").upper()
            for hdr_delta in (16, 20):
                if str_offset >= hdr_delta:
                    hdr_addr = base + str_offset - hdr_delta
                    qstring_pc_headers[hdr_addr] = p_str

    print(f"  -> Ditemukan {len(qstring_pc_headers)} kandidat QStringData PC & {len(qstring_time_headers)} QStringData Waktu.")

    # Buat helper untuk baca QString dari pointer 32-bit (QStringData*)
    region_Intervals = [(b, b + len(r), r) for b, r in regions]

    def read_qstring_at_ptr(ptr_val: int):
        if ptr_val < 0x10000 or ptr_val > 0x7FFF0000:
            return None
        for b_start, b_end, r_bytes in region_Intervals:
            if b_start <= ptr_val < b_end - 32:
                off = ptr_val - b_start
                # Cek apakah struktur QStringData valid (ref > 0, sizeantara 1..64)
                ref, alloc, size, data_ptr = struct.unpack_from("<iiiI", r_bytes, off)
                if 1 <= size <= 64 and (ptr_val + 16 <= data_ptr <= ptr_val + 24):
                    str_off = data_ptr - b_start
                    if str_off + size * 2 <= len(r_bytes):
                        s = r_bytes[str_off : str_off + size * 2].decode("utf-16le", errors="ignore")
                        if all(32 <= ord(c) <= 126 for c in s):
                            return s
        return None

    # 2. Cari objek C++ di memori yang memiliki pointer ke QStringData Waktu!
    time_hdr_set = set(qstring_time_headers.keys())
    matched_structs = []

    for base, raw in regions:
        # Scan setiap 4-byte aligned dword
        limit = len(raw) - 4
        for off in range(0, limit, 4):
            val = struct.unpack_from("<I", raw, off)[0]
            if val in time_hdr_set:
                t_str = qstring_time_headers[val]
                # Periksa semua pointer QString di sekitar struct ini (-128 s/d +128 bytes)
                nearby_strings = []
                scan_start = max(0, off - 160)
                scan_end = min(len(raw) - 4, off + 160)
                for sub_off in range(scan_start, scan_end, 4):
                    sub_ptr = struct.unpack_from("<I", raw, sub_off)[0]
                    qs = read_qstring_at_ptr(sub_ptr)
                    if qs:
                        rel = sub_off - off
                        nearby_strings.append(f"[{rel:+d}]='{qs}'")
                if len(nearby_strings) >= 2:
                    sig = f"TIME='{t_str}' -> " + ", ".join(nearby_strings)
                    if sig not in matched_structs:
                        matched_structs.append(sig)

    print(f"  -> Ditemukan {len(matched_structs)} C++ Struct yang menunjuk ke QString Waktu:")
    for ms in matched_structs[:30]:
        print("    ", ms[:150])


def main():
    pid = get_gcbserver_pid()
    if not pid:
        print("[ERROR] gcbServer.exe tidak ditemukan!")
        return

    inspect_latest_log_file()
    map_qstrings_and_structs(pid)
    print("\n============================================================")
    print(" Selesai! Silakan foto hasil [1/3] dan [2/3] di atas.")
    print("============================================================")


if __name__ == "__main__":
    main()
