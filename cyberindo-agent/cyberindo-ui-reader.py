"""
FAUKAY E-SPORT — CyberIndo Pro Server v1.8.5 (gcbServer.exe) Live Sync Agent
============================================================================
Membaca langsung C++ Workstation / UI Card Struct di memori (RAM) gcbServer.exe:
  Offset +0  : PC Name    ('VIP-10', 'VVIP-03', 'VVIP-09', 'VIP-15', dll.)
  Offset +4  : Username   ('LAMELO', 'BON1', 'JR', dll.)
  Offset +20 : Sisa Waktu ('5j 26m', '30m', '2j 41m', dll.)
Lalu mengirimkan (POST) secara real-time setiap 4 detik ke Website Faukay E-Sport!
"""

import argparse
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
    # Format "5j 26m" atau "2j 0m"
    m_jm = re.match(r"^(\d{1,2})\s*j\s*(\d{1,2})\s*m$", s, re.IGNORECASE)
    if m_jm:
        return int(m_jm.group(1)) * 3600 + int(m_jm.group(2)) * 60

    # Format "30m" atau "6m"
    m_only = re.match(r"^(\d{1,3})\s*m$", s, re.IGNORECASE)
    if m_only:
        return int(m_only.group(1)) * 60

    # Format "6j"
    h_only = re.match(r"^(\d{1,2})\s*j$", s, re.IGNORECASE)
    if h_only:
        return int(h_only.group(1)) * 3600

    return 0


def is_valid_time_str(s: str) -> bool:
    return bool(re.match(r"^(?:\d{1,2}\s*j\s*)?\d{1,2}\s*m$", s.strip(), re.IGNORECASE))


def is_valid_pc_id(s: str) -> bool:
    return bool(re.match(r"^(?:VVIP|VIP|PC)-\d{2}$", s.strip(), re.IGNORECASE))


def build_all_faukay_pcs():
    """Daftar 46 PC standar Faukay E-Sport: 18 VVIP (01-18) & 28 VIP (07-36, skip 24 & 1 nomor lain)."""
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


def extract_live_pcs_from_ram(pid: int, first_run: bool = False):
    """
    Membaca seluruh struct kartu PC aktif dari RAM gcbServer.exe.
    Mengembalikan dict { 'VIP-10': {'status': 'IN_USE', 'remainingSeconds': 1800, 'currentUser': 'LAMELO', ...} }
    """
    kernel32 = ctypes.windll.kernel32
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_proc:
        return []

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

    region_intervals = [(b, b + len(r), r) for b, r in regions]
    qstring_cache = {}

    def read_bytes_at_va(va: int, length: int):
        for b_start, b_end, r_bytes in region_intervals:
            if b_start <= va and va + length <= b_end:
                off = va - b_start
                return r_bytes[off : off + length]
        return None

    def read_qstring_at_ptr(ptr_val: int):
        if ptr_val in qstring_cache:
            return qstring_cache[ptr_val]
        if ptr_val < 0x10000 or ptr_val > 0x7FFF0000:
            return None

        hdr = read_bytes_at_va(ptr_val, 20)
        if not hdr or len(hdr) < 16:
            qstring_cache[ptr_val] = None
            return None

        ref, alloc, size, data_ptr = struct.unpack_from("<iiiI", hdr, 0)
        if not (1 <= ref <= 500000 and 0 <= size <= 120 and size <= alloc <= 4096):
            qstring_cache[ptr_val] = None
            return None

        if size == 0:
            qstring_cache[ptr_val] = ""
            return ""

        # data_ptr biasanya ptr_val + 18, tapi juga bisa menunjuk ke buffer UTF-16 di heap
        if not (0x10000 <= data_ptr <= 0x7FFF0000):
            qstring_cache[ptr_val] = None
            return None

        str_bytes = read_bytes_at_va(data_ptr, size * 2)
        if not str_bytes or len(str_bytes) < size * 2:
            qstring_cache[ptr_val] = None
            return None

        try:
            s = str_bytes.decode("utf-16le")
            if all(32 <= ord(c) <= 126 for c in s):
                qstring_cache[ptr_val] = s
                return s
        except Exception:
            pass

        qstring_cache[ptr_val] = None
        return None

    # Cari semua QStringData header untuk Nama PC ('VIP-07'..'VIP-36', 'VVIP-01'..'VVIP-18')
    pc_re = re.compile(rb"((?:V\x00)?V\x00I\x00P\x00-\x00\d\x00\d\x00)\x00\x00")
    pc_hdr_to_name = {}

    for base, raw in regions:
        for m in pc_re.finditer(raw):
            str_off = m.start(1)
            p_str = m.group(1).decode("utf-16le", errors="ignore").upper()
            if not is_valid_pc_id(p_str):
                continue
            for delta in (16, 18, 20):
                if str_off >= delta:
                    hdr_va = base + str_off - delta
                    if read_qstring_at_ptr(hdr_va) == p_str:
                        pc_hdr_to_name[hdr_va] = p_str

    # Scan semua struct di memori yang menunjuk ke pc_hdr_to_name
    pc_hdr_set = set(pc_hdr_to_name.keys())
    detected_active = {}  # pc_id -> { remainingSeconds, currentUser, game, rawTime, rawFields }
    debug_cards = []

    for base, raw in regions:
        limit = len(raw) - 4
        for off in range(0, limit, 2):
            val = struct.unpack_from("<I", raw, off)[0]
            if val not in pc_hdr_set:
                continue

            pc_id = pc_hdr_to_name[val]

            # Periksa field di struct kartu PC:
            # Dari dump terbukti:
            #   [+0]  = PC Name ('VIP-10', 'VVIP-03')
            #   [+4]  = Username ('LAMELO', 'BON1', 'JR')
            #   [+20] = Remaining Time ('5j 26m', '30m')
            #   [+68] = Status hover / Jam ('notHover', '21:11:02')
            fields = {}
            for rel in range(-24, 128, 4):
                pos = off + rel
                if 0 <= pos <= limit:
                    sub_ptr = struct.unpack_from("<I", raw, pos)[0]
                    qs = read_qstring_at_ptr(sub_ptr)
                    if qs is not None and qs != "":
                        fields[rel] = qs

            # Abaikan jika ini adalah tabel konfigurasi MAC Address (yang memiliki '1.8.5' di +12 atau IP di -8)
            if fields.get(12) == "1.8.5" or (fields.get(-8, "").startswith("192.168.")):
                continue

            # Cek apakah struct ini memiliki waktu sisa (di sekitar +16, +20, +24, dst.) atau username di +4
            found_time_str = None
            for rel_t in (20, 16, 24, 28, 8, 12, 32, 36, 40):
                cand = fields.get(rel_t, "")
                if is_valid_time_str(cand):
                    found_time_str = cand
                    break

            if not found_time_str:
                # Cek semua field positif
                for rel_k, cand in fields.items():
                    if rel_k > 0 and is_valid_time_str(cand):
                        found_time_str = cand
                        break

            user_cand = fields.get(4, "")
            # Validasi username (bukan nama PC lain, bukan param1, bukan kata sistem)
            if (
                not user_cand
                or is_valid_pc_id(user_cand)
                or user_cand.lower() in ("param1", "nothover", "username", "ms shell dlg 2", "wekaweka")
                or "192.168." in user_cand
            ):
                user_cand = ""

            if found_time_str or user_cand:
                rem_sec = parse_time_str_to_seconds(found_time_str) if found_time_str else 0
                sig_str = f"{pc_id}: user='{user_cand}', time='{found_time_str}' | fields={fields}"
                if sig_str not in debug_cards:
                    debug_cards.append(sig_str)

                prev = detected_active.get(pc_id)
                if not prev or rem_sec > prev["remainingSeconds"] or (user_cand and not prev["currentUser"]):
                    detected_active[pc_id] = {
                        "id": pc_id,
                        "status": "IN_USE",
                        "remainingSeconds": rem_sec if rem_sec > 0 else (prev["remainingSeconds"] if prev else 1800),
                        "totalSeconds": max(rem_sec, 7200),
                        "packageType": f"User: {user_cand}" if user_cand else "Billing CyberIndo",
                        "currentUser": user_cand or (prev["currentUser"] if prev else None),
                        "rawTime": found_time_str or "",
                    }

    if first_run:
        print(f"\n[INFO] Ditemukan {len(debug_cards)} struct kartu PC aktif di memori:")
        for dc in debug_cards[:30]:
            print("  ->", dc[:150])

    fleet = build_all_faukay_pcs()
    for pc_id, active_info in detected_active.items():
        if pc_id in fleet and active_info["remainingSeconds"] > 0:
            fleet[pc_id] = {
                "id": pc_id,
                "status": "IN_USE",
                "remainingSeconds": active_info["remainingSeconds"],
                "totalSeconds": active_info["totalSeconds"],
                "packageType": active_info["packageType"],
                "currentUser": active_info["currentUser"],
            }

    return list(fleet.values()), detected_active


def main():
    parser = argparse.ArgumentParser(description="Faukay E-Sport CyberIndo Live Sync Agent")
    parser.add_argument("--url", default="https://faukayesport-fky.vercel.app/api/pcs", help="URL API Website")
    parser.add_argument("--secret", default="", help="Secret key FAUKAY_SYNC_SECRET")
    parser.add_argument("--interval", type=int, default=4, help="Interval update dalam detik")
    args = parser.parse_args()

    api_url = normalize_api_url(args.url)

    print("============================================================")
    print(" FAUKAY E-SPORT — CYBERINDO LIVE SYNC AGENT (RAM TELEMETRY)")
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
            pcs_payload, active_map = extract_live_pcs_from_ram(pid, first_run=first_run)
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
                f"{k}({v.get('currentUser') or '-'} {v.get('rawTime') or ''})".strip()
                for k, v in sorted(active_map.items())
                if v["remainingSeconds"] > 0
            )
            print(
                f"\n[{time.strftime('%H:%M:%S')}] SYNC OK (HTTP {res.status_code}) -> "
                f"{len(active_map)} PC Aktif dari {len(pcs_payload)} Total PC"
            )
            if active_summary:
                print(f"  PC Aktif: {active_summary}")
        except Exception as err:
            print(f"[{time.strftime('%H:%M:%S')}] [ERROR] {err}")

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
