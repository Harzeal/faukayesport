"""
FAUKAY E-SPORT — CyberIndo Pro Server v1.8.5 (gcbServer.exe) Ultra-Fast Live Sync Agent
=======================================================================================
Kecepatan scan: ~0.2 detik menggunakan C-level bytes.find() & bisect!
Membaca langsung C++ UI Card Struct di memori (RAM) gcbServer.exe:
  Offset -20 (dari Time) / +0 (dari PC) : PC Name    ('VIP-10', 'VVIP-03', dll.)
  Offset -16 (dari Time) / +4 (dari PC) : Username   ('LAMELO', 'BON1', 'JR', dll.)
  Offset +0  (dari Time) / +20 (dari PC): Sisa Waktu ('5j 26m', '30m', '2j 41m', dll.)
"""

import argparse
from bisect import bisect_right
import ctypes
from ctypes import wintypes
import re
import struct
import subprocess
import time
import warnings
import requests

warnings.filterwarnings("ignore")

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


def parse_time_str_to_seconds(t_str: str) -> int:
    if not t_str:
        return 0
    s = t_str.strip()
    m_jm = re.match(r"^(\d{1,2})\s*j\s*(\d{1,2})\s*m$", s, re.IGNORECASE)
    if m_jm:
        return int(m_jm.group(1)) * 3600 + int(m_jm.group(2)) * 60
    m_only = re.match(r"^(\d{1,3})\s*m$", s, re.IGNORECASE)
    if m_only:
        return int(m_only.group(1)) * 60
    h_only = re.match(r"^(\d{1,2})\s*j$", s, re.IGNORECASE)
    if h_only:
        return int(h_only.group(1)) * 3600
    return 0


def is_valid_time_str(s: str) -> bool:
    return bool(re.match(r"^(?:\d{1,2}\s*j\s*)?\d{1,2}\s*m$", s.strip(), re.IGNORECASE))


def is_valid_pc_id(s: str) -> bool:
    return bool(re.match(r"^(?:VVIP|VIP|PC)-\d{2}$", s.strip(), re.IGNORECASE))


def build_all_faukay_pcs():
    pcs = {}
    for i in range(1, 19):
        pid = f"VVIP-{i:02d}"
        pcs[pid] = {
            "id": pid,
            "status": "AVAILABLE",
            "remainingSeconds": 0,
            "totalSeconds": 0,
            "packageType": "Siap Pakai",
            "currentUser": None,
        }
    for i in range(7, 37):
        if i == 24:
            continue
        pid = f"VIP-{i:02d}"
        pcs[pid] = {
            "id": pid,
            "status": "AVAILABLE",
            "remainingSeconds": 0,
            "totalSeconds": 0,
            "packageType": "Siap Pakai",
            "currentUser": None,
        }
    return pcs


def extract_live_pcs_fast(pid: int, first_run: bool = False):
    t0 = time.perf_counter()
    kernel32 = ctypes.windll.kernel32
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_proc:
        return [], {}

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

    # Sort regions untuk binary search O(log N) super cepat
    regions.sort(key=lambda x: x[0])
    base_addrs = [r[0] for r in regions]
    qstring_cache = {}

    def read_qstring_at_ptr(ptr_val: int):
        if ptr_val in qstring_cache:
            return qstring_cache[ptr_val]
        if ptr_val < 0x10000 or ptr_val > 0x7FFF0000:
            return None

        idx = bisect_right(base_addrs, ptr_val) - 1
        if idx < 0:
            qstring_cache[ptr_val] = None
            return None

        b_start, r_bytes = regions[idx]
        b_end = b_start + len(r_bytes)
        if ptr_val + 36 > b_end:
            qstring_cache[ptr_val] = None
            return None

        off = ptr_val - b_start
        ref, alloc, size, data_ptr = struct.unpack_from("<iiiI", r_bytes, off)
        if not (1 <= ref <= 500000 and 1 <= size <= 80 and (ptr_val + 14 <= data_ptr <= ptr_val + 28)):
            qstring_cache[ptr_val] = None
            return None

        str_off = data_ptr - b_start
        if str_off < 0 or str_off + size * 2 > len(r_bytes):
            qstring_cache[ptr_val] = None
            return None

        try:
            s = r_bytes[str_off : str_off + size * 2].decode("utf-16le", errors="ignore")
            if s and all(32 <= ord(c) <= 126 for c in s):
                qstring_cache[ptr_val] = s
                return s
        except Exception:
            pass

        qstring_cache[ptr_val] = None
        return None

    # 1. Cari semua QStringData Waktu ("5j 26m", "30m", "2j 41m") dan PC ("VIP-10", "VVIP-03")
    time_re = re.compile(rb"(?:[\x30-\x39]\x00[\x30-\x39]?\x00j\x00 \x00)?[\x30-\x39]\x00[\x30-\x39]?\x00m\x00\x00\x00")
    pc_re = re.compile(rb"(?:V\x00)?V\x00I\x00P\x00-\x00[\x30-\x39]\x00[\x30-\x39]\x00\x00\x00")

    valid_time_hdrs = {}  # hdr_va -> time_str
    valid_pc_hdrs = {}    # hdr_va -> pc_str

    for base, raw in regions:
        for m in time_re.finditer(raw):
            str_off = m.start()
            for delta in (16, 18, 20, 24):
                if str_off >= delta:
                    hdr_va = base + str_off - delta
                    qs = read_qstring_at_ptr(hdr_va)
                    if qs and is_valid_time_str(qs):
                        valid_time_hdrs[hdr_va] = qs

        for m in pc_re.finditer(raw):
            str_off = m.start()
            for delta in (16, 18, 20):
                if str_off >= delta:
                    hdr_va = base + str_off - delta
                    qs = read_qstring_at_ptr(hdr_va)
                    if qs and is_valid_pc_id(qs):
                        valid_pc_hdrs[hdr_va] = qs.upper()

    detected_active = {}
    debug_matches = []

    # 2. Gunakan C-speed raw.find() untuk mencari semua struct yang menunjuk ke QString Waktu!
    for hdr_va, t_str in valid_time_hdrs.items():
        needle = struct.pack("<I", hdr_va)
        for base, raw in regions:
            pos = raw.find(needle)
            while pos != -1:
                # Periksa pointer di sekitar posisi waktu ini (-128 s/d +64 byte)
                nearby = {}
                start_scan = max(0, pos - 128)
                end_scan = min(len(raw) - 4, pos + 64)
                for sub_off in range(start_scan, end_scan, 2):
                    if (sub_off - pos) % 2 != 0:
                        continue
                    sub_ptr = struct.unpack_from("<I", raw, sub_off)[0]
                    qs = read_qstring_at_ptr(sub_ptr)
                    if qs:
                        nearby[sub_off - pos] = qs

                # Cek apakah ada nama PC di nearby (biasanya di -20 atau -108)
                found_pc = None
                found_pc_rel = None
                for rel_p in (-20, -16, -24, -108, -88, -12, -8, 20, 16):
                    cand = nearby.get(rel_p, "")
                    if is_valid_pc_id(cand):
                        found_pc = cand.upper()
                        found_pc_rel = rel_p
                        break

                if not found_pc:
                    for rel_p, cand in nearby.items():
                        if is_valid_pc_id(cand):
                            found_pc = cand.upper()
                            found_pc_rel = rel_p
                            break

                if found_pc:
                    # Username biasanya berada +4 byte setelah posisi PC Name (misal PC di -20 -> User di -16)
                    user_cand = ""
                    if found_pc_rel is not None:
                        u_try = nearby.get(found_pc_rel + 4, "")
                        if (
                            u_try
                            and not is_valid_pc_id(u_try)
                            and not is_valid_time_str(u_try)
                            and u_try.lower() not in ("nothover", "member", "prepay", "param1", "wekaweka")
                        ):
                            user_cand = u_try

                    rem_sec = parse_time_str_to_seconds(t_str)
                    if rem_sec > 0:
                        info_line = f"{found_pc} -> Waktu='{t_str}' ({rem_sec}s), User='{user_cand}' | struct={nearby}"
                        if info_line not in debug_matches:
                            debug_matches.append(info_line)

                        prev = detected_active.get(found_pc)
                        if not prev or rem_sec > prev["remainingSeconds"] or (user_cand and not prev["currentUser"]):
                            detected_active[found_pc] = {
                                "id": found_pc,
                                "status": "IN_USE",
                                "remainingSeconds": rem_sec,
                                "totalSeconds": max(rem_sec, 7200),
                                "packageType": f"User: {user_cand}" if user_cand else "Billing CyberIndo",
                                "currentUser": user_cand or (prev["currentUser"] if prev else None),
                                "rawTime": t_str,
                            }

                pos = raw.find(needle, pos + 2)

    # 3. Tambahan: Gunakan C-speed raw.find() pada QString PC untuk menangkap PC yang baru login
    for hdr_va, pc_id in valid_pc_hdrs.items():
        needle = struct.pack("<I", hdr_va)
        for base, raw in regions:
            pos = raw.find(needle)
            while pos != -1:
                # Cek offset +4 (Username) dan +20 (Waktu)
                if pos + 24 <= len(raw):
                    u_ptr = struct.unpack_from("<I", raw, pos + 4)[0]
                    t_ptr = struct.unpack_from("<I", raw, pos + 20)[0]
                    u_str = read_qstring_at_ptr(u_ptr) or ""
                    t_str = read_qstring_at_ptr(t_ptr) or ""

                    if is_valid_time_str(t_str):
                        rem_sec = parse_time_str_to_seconds(t_str)
                        clean_u = (
                            u_str
                            if (
                                u_str
                                and not is_valid_pc_id(u_str)
                                and u_str.lower() not in ("param1", "wekaweka", "nothover", "bon1" if False else "")
                                and ":" not in u_str
                            )
                            else ""
                        )
                        if rem_sec > 0:
                            prev = detected_active.get(pc_id)
                            if not prev or rem_sec > prev["remainingSeconds"]:
                                detected_active[pc_id] = {
                                    "id": pc_id,
                                    "status": "IN_USE",
                                    "remainingSeconds": rem_sec,
                                    "totalSeconds": max(rem_sec, 7200),
                                    "packageType": f"User: {clean_u}" if clean_u else "Billing CyberIndo",
                                    "currentUser": clean_u or (prev["currentUser"] if prev else None),
                                    "rawTime": t_str,
                                }
                pos = raw.find(needle, pos + 2)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    if first_run:
        print(f"[FAST-SCAN] Selesai dalam {elapsed_ms} ms | Terdeteksi {len(detected_active)} PC Aktif:")
        for dm in debug_matches[:25]:
            print("  ->", dm[:140])

    fleet = build_all_faukay_pcs()
    for pc_id, active_info in detected_active.items():
        if pc_id in fleet:
            fleet[pc_id] = {
                "id": pc_id,
                "status": "IN_USE",
                "remainingSeconds": active_info["remainingSeconds"],
                "totalSeconds": active_info["totalSeconds"],
                "packageType": active_info["packageType"],
                "currentUser": active_info["currentUser"],
            }

    return list(fleet.values()), detected_active, elapsed_ms


def main():
    parser = argparse.ArgumentParser(description="Faukay E-Sport CyberIndo Ultra-Fast Sync Agent")
    parser.add_argument("--url", default="https://faukayesport-fky.vercel.app/api/pcs", help="URL API Website")
    parser.add_argument("--secret", default="", help="Secret key FAUKAY_SYNC_SECRET")
    parser.add_argument("--interval", type=int, default=4, help="Interval update dalam detik")
    args = parser.parse_args()

    api_url = normalize_api_url(args.url)

    print("============================================================")
    print(" FAUKAY E-SPORT — CYBERINDO LIVE SYNC AGENT (TURBO RAM)")
    print(f" Target API : {api_url}")
    print(f" Interval   : {args.interval} detik")
    print("============================================================")

    first_run = True
    while True:
        pid = get_gcbserver_pid()
        if not pid:
            print(f"[{time.strftime('%H:%M:%S')}] [WARN] gcbServer.exe belum berjalan. Menunggu...")
            time.sleep(args.interval)
            continue

        try:
            pcs_payload, active_map, scan_ms = extract_live_pcs_fast(pid, first_run=first_run)
            first_run = False

            res = requests.post(
                api_url,
                json={
                    "secret": args.secret,
                    "source": "CYBERINDO_AGENT",
                    "skippedVipNumbers": [24],
                    "pcs": pcs_payload,
                },
                timeout=8,
            )

            active_summary = ", ".join(
                f"{k}({v.get('currentUser') or ''} {v.get('rawTime') or ''})".strip()
                for k, v in sorted(active_map.items())
            )
            print(
                f"[{time.strftime('%H:%M:%S')}] SYNC OK (HTTP {res.status_code} | {scan_ms}ms) -> "
                f"{len(active_map)} PC Aktif: {active_summary}"
            )
        except Exception as err:
            print(f"[{time.strftime('%H:%M:%S')}] [ERROR] {err}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
