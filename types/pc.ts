export type PCZone = 'VVIP' | 'VIP';

export type PCStatus = 'AVAILABLE' | 'IN_USE' | 'MAINTENANCE';

export interface PCUnit {
  /** ID unik misal 'VVIP-01' atau 'VIP-07' */
  id: string;
  /** Nama tampilan di kartu & sesuai nama workstation di CyberIndo */
  name: string;
  /** Nomor urut di zona tersebut */
  number: number;
  /** Kategori Ruangan: VVIP (18 PC) atau VIP (28 PC) */
  zone: PCZone;
  /** Status real-time PC */
  status: PCStatus;
  /** Sisa waktu dalam detik (0 jika AVAILABLE atau MAINTENANCE) */
  remainingSeconds: number;
  /** Total durasi paket dalam detik (untuk progress bar) */
  totalSeconds: number;
  /** Jenis paket / tipe member CyberIndo (misal: 'Member', 'Paket 3 Jam', 'Personal') */
  packageType: string;
  /** Username / akun member (disamarkan untuk privasi publik jika perlu) */
  currentUser?: string;
  /** Spesifikasi singkat ruangan */
  specs: string;
  /** Timestamp ISO kapan terakhir kali status PC ini diperbarui */
  updatedAt: string;
}

export interface ArenaSummary {
  totalPCs: number;
  availablePCs: number;
  inUsePCs: number;
  endingSoonPCs: number; // < 15 menit (900 detik)
  maintenancePCs: number;
  vvipAvailable: number;
  vvipTotal: number;
  vipAvailable: number;
  vipTotal: number;
  lastSyncAt: string;
  syncSource: 'SIMULATION' | 'CYBERINDO_AGENT' | 'MANUAL_ADMIN';
  skippedVipNumbers: number[];
}

export interface BillingSyncPayload {
  secret?: string;
  source?: 'SIMULATION' | 'CYBERINDO_AGENT' | 'MANUAL_ADMIN';
  skippedVipNumbers?: number[];
  pcs: Array<{
    id?: string;
    name?: string;
    zone?: PCZone;
    number?: number;
    status: PCStatus;
    remainingSeconds: number;
    totalSeconds?: number;
    packageType?: string;
    currentUser?: string;
  }>;
}
