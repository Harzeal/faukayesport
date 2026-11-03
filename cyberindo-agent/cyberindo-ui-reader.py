"""
FAUKAY E-SPORT — CyberIndo Pro Server v1.8.5 (gcbServer.exe) Live Reader
========================================================================
Melacak:
1. Baris lengkap LiveSystemLogs & Heartbeat (HB. ws: ...) di gbServer-YYYYMMDD.log
2. Header QStringData Qt4 pada offset 18 byte (sizeof(QStringData) di MSVC 32-bit = 18)
"""

import ctypes
from ctypes import wintypes
import glob
import os
import re
import struct
import subprocess
import warnings

warnings.filterwarnings("ignore")


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


def inspect_log_full():
    log_dir = r"D:\DataBaseBilling\GBillingServer\Logs"
    print(f"\n[1/2] Memeriksa Detail Lengkap Log di: {log_dir}")
    log_files = sorted(glob.glob(os.path.join(log_dir, "gbServer-*.log")), key=os.path.getmtime, reverse=True)
    if not log_files:
        return

    latest = log_files[0]
    try:
        with open(latest, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 1. Tampilkan 3 baris lengkap INSERT INTO LiveSystemLogs tanpa dipotong
        live_logs = [ln for ln in lines if "LiveSystemLogs" in ln]
        print(f"  -> Contoh Baris Lengkap LiveSystemLogs (Total {len(live_logs)}):")
        for ln in live_logs[-3:]:
            print("    ", ln)

        # 2. Tampilkan contoh baris HB (Heartbeat) yang memiliki ssid != 0 atau hs != -1
        hb_active = [ln for ln in lines if "HB. ws:" in ln and ("ssid: 0" not in ln or "hs: -1" not in ln)]
        print(f"\n  -> Contoh Baris Heartbeat PC Aktif (Total {len(hb_active)}):")
        for ln in hb_active[-10:]:
            print("    ", ln)

        # 3. Cari baris yang mengandung sessionUpdated atau order atau login
        sess_lines = [ln for ln in lines if any(k in ln for k in ["session", "Order", "login", "workstation", "VIP"]) and "LiveSystemLogs" not in ln]
        print(f"\n  -> 12 Baris Aktivitas Session/Workstation Terakhir:")
        for ln in sess_lines[-12:]:
            print("    ", ln[:220])
    except Exception as e:
        print(f"  -> Error baca log: {e}")


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


def trace_qt4_qstrings_offset18(pid: int):
    """
    Di Qt4 32-bit (MSVC), struct QString::Data berukuran 18 byte sebelum array UTF-16:
      offset 0  : int ref
      offset 4  : int alloc
      offset 8  : int size
      offset 12 : ushort* data  (berisi alamat karakter pertama = header_addr + 18!)
      offset 16 : ushort flags
      offset 18 : ushort array[1] (karakter pertama!)
    """
    print(f"\n[2/2] Melacak QStringData Qt4 (Offset 18 Byte) di RAM gcbServer.exe (PID: {pid})...")
    kernel32 = ctypes.windll.kernel32
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_proc:
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

    time_re = re.compile(rb"\x00((?:\d\x00\d?\x00j\x00 \x00)?\d\x00\d?\x00m\x00)\x00\x00")
    pc_re = re.compile(rb"((?:V\x00)?V\x00I\x00P\x00-\x00\d\x00\d\x00)\x00\x00")

    qstring_time_headers = {}
    qstring_pc_headers = {}

    for base, raw in regions:
        for m in time_re.finditer(raw):
            str_off = m.start(1)
            t_str = m.group(1).decode("utf-16le", errors="ignore")
            if not re.match(r"^(?:\d{1,2}j )?\d{1,2}m$", t_str):
                continue
            str_va = base + str_off
            # Cek offset 6 byte sebelum str_off (tempat field `ushort* data` berada jika header = 18 byte)
            for delta in (16, 18, 20, 24):
                if str_off >= delta:
                    qstring_time_headers[base + str_off - delta] = t_str

        for m in pc_re.finditer(raw):
            str_off = m.start(1)
            p_str = m.group(1).decode("utf-16le", errors="ignore").upper()
            for delta in (16, 18, 20, 24):
                if str_off >= delta:
                    qstring_pc_headers[base + str_off - delta] = p_str

    region_intervals = [(b, b + len(r), r) for b, r in regions]

    def read_qstring_at_ptr(ptr_val: int):
        if ptr_val < 0x10000 or ptr_val > 0x7FFF0000:
            return None
        for b_start, b_end, r_bytes in region_intervals:
            if b_start <= ptr_val < b_end - 36:
                off = ptr_val - b_start
                ref, alloc, size, data_ptr = struct.unpack_from("<iiiI", r_bytes, off)
                if 1 <= size <= 80 and (ptr_val + 14 <= data_ptr <= ptr_val + 28):
                    str_off = data_ptr - b_start
                    if 0 <= str_off and str_off + size * 2 <= len(r_bytes):
                        s = r_bytes[str_off : str_off + size * 2].decode("utf-16le", errors="ignore")
                        if s and all(32 <= ord(c) <= 126 for c in s):
                            return s
        return None

    time_hdr_set = set(qstring_time_headers.keys())
    pc_hdr_set = set(qstring_pc_headers.keys())

    matched_time_structs = []
    matched_pc_structs = []

    for base, raw in regions:
        limit = len(raw) - 4
        # Scan pada alignment 2-byte dan 4-byte
        for off in range(0, limit, 2):
            val = struct.unpack_from("<I", raw, off)[0]
            if val in time_hdr_set and len(matched_time_structs) < 25:
                t_str = qstring_time_headers[val]
                nearby = []
                for sub_off in range(max(0, off - 128), min(limit, off + 128), 2):
                    sub_ptr = struct.unpack_from("<I", raw, sub_off)[0]
                    qs = read_qstring_at_ptr(sub_ptr)
                    if qs:
                        nearby.append(f"[{sub_off - off:+d}]='{qs}'")
                if len(nearby) >= 2:
                    sig = f"TIME('{t_str}') -> " + ", ".join(nearby)
                    if sig not in matched_time_structs:
                        matched_time_structs.append(sig)

            elif val in pc_hdr_set and len(matched_pc_structs) < 25:
                p_str = qstring_pc_headers[val]
                nearby = []
                for sub_off in range(max(0, off - 128), min(limit, off + 128), 2):
                    sub_ptr = struct.unpack_from("<I", raw, sub_off)[0]
                    qs = read_qstring_at_ptr(sub_ptr)
                    if qs:
                        nearby.append(f"[{sub_off - off:+d}]='{qs}'")
                if len(nearby) >= 2:
                    sig = f"PC('{p_str}') -> " + ", ".join(nearby)
                    if sig not in matched_pc_structs:
                        matched_pc_structs.append(sig)

    print(f"  -> Struct Memori di sekitar Waktu ({len(matched_time_structs)} ditemukan):")
    for s in matched_time_structs[:15]:
        print("    ", s[:160])

    print(f"\n  -> Struct Memori di sekitar Nama PC ({len(matched_pc_structs)} ditemukan):")
    for s in matched_pc_structs[:15]:
        print("    ", s[:160])


def main():
    pid = get_gcbserver_pid()
    if not pid:
        print("[ERROR] gcbServer.exe tidak ditemukan!")
        return

    inspect_log_full()
    trace_qt4_qstrings_offset18(pid)
    print("\n============================================================")
    print(" Selesai! Silakan foto hasil [1/2] dan [2/2] di atas.")
    print("============================================================")


if __name__ == "__main__":
    main()
