import { ArenaSummary, BillingSyncPayload, PCStatus, PCUnit } from '@/types/pc';
import {
  buildDefaultPCList,
  DEFAULT_SKIPPED_VIP_NUMBERS,
  padNumber,
  ZONE_SPECS,
} from '@/lib/pc-config';

interface StoreState {
  pcs: PCUnit[];
  skippedVipNumbers: number[];
  lastSyncAt: string;
  syncSource: 'SIMULATION' | 'CYBERINDO_AGENT' | 'MANUAL_ADMIN';
}

const PACKAGES = [
  { label: 'Paket 1 Jam', totalSeconds: 3600 },
  { label: 'Paket 2 Jam', totalSeconds: 7200 },
  { label: 'Paket 3 Jam', totalSeconds: 10800 },
  { label: 'Paket 5 Jam', totalSeconds: 18000 },
  { label: 'Member Reguler', totalSeconds: 14400 },
  { label: 'Paket Malam', totalSeconds: 21600 },
];

const SAMPLE_GAMERS = [
  'FK_Viper', 'Rexx_ID', 'ValoKing99', 'DotaSlayer', 'Member_082',
  'Member_114', 'AegisPro', 'PhantomX', 'ShadowFK', 'PB_Legend',
  'Member_209', 'ZephyrGG', 'ApexPredator', 'Kaze_FK', 'Ryu_Esport',
  'Member_041', 'NovaStrike', 'BlitzKrieg', 'CyberWolf', 'Orion_FK',
  'Member_312', 'VortexID', 'Hyperion', 'Draco_99', 'TacticalFK',
  'Member_019', 'SniperElite', 'Gladiator', 'FrostByte', 'Ignis_FK',
];

function createSeededSimulation(skippedVipNumbers: number[]): PCUnit[] {
  const baseList = buildDefaultPCList(skippedVipNumbers);
  const now = new Date().toISOString();

  // Buat distribusi realistis: sekitar ~65% PC sedang dipakai, beberapa < 15 menit (segera habis), 1 maintenance
  return baseList.map((pc, idx) => {
    // Gunakan pola deterministik + sedikit variasi agar langsung terlihat hidup
    const seed = (pc.number * 17 + idx * 31) % 100;

    // 1 PC Maintenance sebagai contoh
    if (pc.zone === 'VIP' && pc.number === 29) {
      return {
        ...pc,
        status: 'MAINTENANCE',
        remainingSeconds: 0,
        totalSeconds: 0,
        packageType: 'Maintenance / Cek Mouse',
        updatedAt: now,
      };
    }

    // Sekitar 32% PC Kosong (Available)
    if (seed < 32) {
      return {
        ...pc,
        status: 'AVAILABLE',
        remainingSeconds: 0,
        totalSeconds: 0,
        packageType: 'Siap Pakai',
        updatedAt: now,
      };
    }

    // Sisanya sedang digunakan (IN_USE)
    const pkg = PACKAGES[idx % PACKAGES.length];
    let remainingSeconds: number;

    if (seed >= 32 && seed < 46) {
      // Segera habis (< 15 menit: antara 2 menit s/d 14 menit)
      remainingSeconds = ((pc.number * 43) % 720) + 120;
    } else {
      // Masih lama (antara 20 menit s/d total paket)
      const minSec = 1200;
      const maxSec = pkg.totalSeconds - 180;
      remainingSeconds = minSec + ((pc.number * 613 + idx * 251) % Math.max(600, maxSec - minSec));
    }

    return {
      ...pc,
      status: 'IN_USE',
      remainingSeconds,
      totalSeconds: pkg.totalSeconds,
      packageType: pkg.label,
      currentUser: SAMPLE_GAMERS[idx % SAMPLE_GAMERS.length],
      updatedAt: now,
    };
  });
}

// Gunakan globalThis agar state bertahan saat Hot Reload di Next.js dev mode
const globalForStore = globalThis as unknown as {
  __faukayStore?: StoreState;
};

function getStore(): StoreState {
  if (!globalForStore.__faukayStore) {
    const skipped = [...DEFAULT_SKIPPED_VIP_NUMBERS];
    globalForStore.__faukayStore = {
      pcs: createSeededSimulation(skipped),
      skippedVipNumbers: skipped,
      lastSyncAt: new Date().toISOString(),
      syncSource: 'SIMULATION',
    };
  }
  return globalForStore.__faukayStore;
}

/**
 * Menghitung sisa waktu real-time setiap PC berdasarkan selisih waktu sekarang dengan `updatedAt`.
 */
export function getLiveArenaState(): { pcs: PCUnit[]; summary: ArenaSummary } {
  const store = getStore();
  const nowMs = Date.now();

  const livePcs: PCUnit[] = store.pcs.map((pc) => {
    if (pc.status !== 'IN_USE') {
      return pc;
    }

    const updatedMs = new Date(pc.updatedAt).getTime();
    const elapsedSeconds = Math.max(0, Math.floor((nowMs - updatedMs) / 1000));
    const currentRemaining = Math.max(0, pc.remainingSeconds - elapsedSeconds);

    if (currentRemaining <= 0) {
      return {
        ...pc,
        status: 'AVAILABLE',
        remainingSeconds: 0,
        totalSeconds: 0,
        packageType: 'Siap Pakai',
        currentUser: undefined,
      };
    }

    return {
      ...pc,
      remainingSeconds: currentRemaining,
    };
  });

  const vvipList = livePcs.filter((p) => p.zone === 'VVIP');
  const vipList = livePcs.filter((p) => p.zone === 'VIP');

  const summary: ArenaSummary = {
    totalPCs: livePcs.length,
    availablePCs: livePcs.filter((p) => p.status === 'AVAILABLE').length,
    inUsePCs: livePcs.filter((p) => p.status === 'IN_USE').length,
    endingSoonPCs: livePcs.filter(
      (p) => p.status === 'IN_USE' && p.remainingSeconds > 0 && p.remainingSeconds <= 900
    ).length,
    maintenancePCs: livePcs.filter((p) => p.status === 'MAINTENANCE').length,
    vvipAvailable: vvipList.filter((p) => p.status === 'AVAILABLE').length,
    vvipTotal: vvipList.length,
    vipAvailable: vipList.filter((p) => p.status === 'AVAILABLE').length,
    vipTotal: vipList.length,
    lastSyncAt: store.lastSyncAt,
    syncSource: store.syncSource,
    skippedVipNumbers: store.skippedVipNumbers,
  };

  return { pcs: livePcs, summary };
}

/**
 * Sinkronisasi data dari CyberIndo Agent di PC Kasir atau dari Panel Kontrol.
 */
export function syncFromBillingPayload(payload: BillingSyncPayload) {
  const store = getStore();
  const now = new Date().toISOString();

  // Jika ada perubahan daftar 2 nomor VIP yang dilewati
  if (
    Array.isArray(payload.skippedVipNumbers) &&
    payload.skippedVipNumbers.length > 0 &&
    JSON.stringify(payload.skippedVipNumbers) !== JSON.stringify(store.skippedVipNumbers)
  ) {
    store.skippedVipNumbers = payload.skippedVipNumbers;
    const rebuilt = buildDefaultPCList(store.skippedVipNumbers);
    const existingMap = new Map(store.pcs.map((p) => [p.id, p]));
    store.pcs = rebuilt.map((unit) => existingMap.get(unit.id) ?? unit);
  }

  if (Array.isArray(payload.pcs) && payload.pcs.length > 0) {
    const incomingMap = new Map<string, BillingSyncPayload['pcs'][number]>();

    for (const item of payload.pcs) {
      let targetId = item.id?.toUpperCase().trim();
      if (!targetId && item.zone && item.number !== undefined) {
        targetId = `${item.zone}-${padNumber(item.number)}`;
      } else if (!targetId && item.name) {
        // Normalisasi nama PC dari CyberIndo: misal "VVIP 01", "VVIP-01", "VIP07", "PC-07"
        const clean = item.name.toUpperCase().trim();
        const numMatch = clean.match(/(\d+)/);
        const num = numMatch ? parseInt(numMatch[1], 10) : null;
        if (num !== null) {
          if (clean.includes('VVIP')) {
            targetId = `VVIP-${padNumber(num)}`;
          } else {
            targetId = `VIP-${padNumber(num)}`;
          }
        }
      }
      if (targetId) {
        incomingMap.set(targetId, item);
      }
    }

    store.pcs = store.pcs.map((pc) => {
      const update = incomingMap.get(pc.id);
      if (!update) return pc;

      const status: PCStatus =
        update.status === 'IN_USE' && update.remainingSeconds <= 0
          ? 'AVAILABLE'
          : update.status;

      const remainingSeconds = status === 'IN_USE' ? Math.max(0, update.remainingSeconds) : 0;
      const totalSeconds =
        status === 'IN_USE'
          ? Math.max(remainingSeconds, update.totalSeconds || 7200)
          : 0;

      return {
        ...pc,
        status,
        remainingSeconds,
        totalSeconds,
        packageType:
          update.packageType ||
          (status === 'IN_USE' ? 'Billing Aktif' : status === 'MAINTENANCE' ? 'Maintenance' : 'Siap Pakai'),
        currentUser: status === 'IN_USE' ? update.currentUser || pc.currentUser : undefined,
        specs: ZONE_SPECS[pc.zone].specs,
        updatedAt: now,
      };
    });
  }

  store.lastSyncAt = now;
  if (payload.source) {
    store.syncSource = payload.source;
  }

  return getLiveArenaState();
}

/**
 * Reset / Acak ulang simulasi (berguna untuk demo di laptop sebelum disambung ke PC Kasir).
 */
export function randomizeSimulation(customSkippedVip?: number[]) {
  const store = getStore();
  if (Array.isArray(customSkippedVip) && customSkippedVip.length === 2) {
    store.skippedVipNumbers = customSkippedVip;
  }
  store.pcs = createSeededSimulation(store.skippedVipNumbers).map((pc) => {
    if (pc.status !== 'IN_USE') return pc;
    // Tambahkan sedikit variasi acak
    const jitter = Math.floor(Math.random() * 900) - 300;
    const rem = Math.max(90, pc.remainingSeconds + jitter);
    return {
      ...pc,
      remainingSeconds: rem,
      totalSeconds: Math.max(rem + 600, pc.totalSeconds),
    };
  });
  store.lastSyncAt = new Date().toISOString();
  store.syncSource = 'SIMULATION';
  return getLiveArenaState();
}
