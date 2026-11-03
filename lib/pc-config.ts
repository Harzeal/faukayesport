import { PCUnit, PCZone } from '@/types/pc';

/**
 * Default 2 nomor PC di rentang VIP (07-36) yang dilewati sehingga total VIP = 28 PC.
 * Dapat diubah kapan saja langsung dari pengaturan UI website atau dari CyberIndo Agent.
 */
export const DEFAULT_SKIPPED_VIP_NUMBERS = [24];

export const ZONE_SPECS: Record<PCZone, { title: string; badge: string; specs: string; rateInfo: string }> = {
  VVIP: {
    title: 'ZONA VVIP ARENA',
    badge: '18 UNIT • PC 01 - 18',
    specs: '240Hz Gaming Monitor • RTX Series • Mechanical Gear • Kursi Gaming Ergonomis',
    rateInfo: 'Ruang Eksklusif Ber-AC Dingin • Prioritas Turnamen & Kompetitif',
  },
  VIP: {
    title: 'ZONA VIP PRO',
    badge: '28 UNIT • PC 07 - 36',
    specs: '165Hz/180Hz Monitor • GTX/RTX Series • Full Mechanical • Headset Gaming 7.1',
    rateInfo: 'Performa Tinggi Stabil • Nyaman untuk Mabar & Push Rank',
  },
};

export function padNumber(num: number): string {
  return num.toString().padStart(2, '0');
}

/**
 * Membangun daftar lengkap 46 PC Faukay E-Sport:
 * - 18 PC VVIP (VVIP-01 s/d VVIP-18)
 * - 28 PC VIP (VIP-07 s/d VIP-36, melewati 2 nomor di skippedVipNumbers)
 */
export function buildDefaultPCList(skippedVipNumbers: number[] = DEFAULT_SKIPPED_VIP_NUMBERS): PCUnit[] {
  const now = new Date().toISOString();
  const units: PCUnit[] = [];

  // 1. 18 PC VVIP (PC 01 - 18)
  for (let i = 1; i <= 18; i++) {
    const id = `VVIP-${padNumber(i)}`;
    units.push({
      id,
      name: `VVIP ${padNumber(i)}`,
      number: i,
      zone: 'VVIP',
      status: 'AVAILABLE',
      remainingSeconds: 0,
      totalSeconds: 0,
      packageType: '-',
      specs: ZONE_SPECS.VVIP.specs,
      updatedAt: now,
    });
  }

  // 2. 28 PC VIP (PC 07 - 36, skip 2 nomor)
  const skipSet = new Set(skippedVipNumbers);
  for (let i = 7; i <= 36; i++) {
    if (skipSet.has(i)) continue;
    const id = `VIP-${padNumber(i)}`;
    units.push({
      id,
      name: `VIP ${padNumber(i)}`,
      number: i,
      zone: 'VIP',
      status: 'AVAILABLE',
      remainingSeconds: 0,
      totalSeconds: 0,
      packageType: '-',
      specs: ZONE_SPECS.VIP.specs,
      updatedAt: now,
    });
  }

  return units;
}

/**
 * Format detik menjadi HH:MM:SS
 */
export function formatSecondsToHMS(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const seconds = safe % 60;
  return `${padNumber(hours)}:${padNumber(minutes)}:${padNumber(seconds)}`;
}

/**
 * Mengubah string waktu CyberIndo (misal "02:15:30" atau "01:20" atau "85 mnt") menjadi detik.
 */
export function parseCyberIndoTime(raw: string | number | null | undefined): number {
  if (typeof raw === 'number') return Math.max(0, Math.floor(raw));
  if (!raw) return 0;
  const text = String(raw).trim();
  if (!text || text === '-' || text === '00:00:00' || text === '00:00') return 0;

  // Format CyberIndo Indonesia: "6j 59m", "1j 8m", "30m", "6m"
  const jmMatch = text.match(/(?:(\d+)\s*j\s*)?(?:(\d+)\s*m)/i);
  if (jmMatch && (jmMatch[1] || jmMatch[2])) {
    const hours = jmMatch[1] ? parseInt(jmMatch[1], 10) : 0;
    const minutes = jmMatch[2] ? parseInt(jmMatch[2], 10) : 0;
    return hours * 3600 + minutes * 60;
  }

  // Format HH:MM:SS atau MM:SS
  const colonParts = text.split(':').map((p) => parseInt(p.trim(), 10));
  if (colonParts.length === 3 && colonParts.every((n) => !Number.isNaN(n))) {
    return colonParts[0] * 3600 + colonParts[1] * 60 + colonParts[2];
  }
  if (colonParts.length === 2 && colonParts.every((n) => !Number.isNaN(n))) {
    return colonParts[0] * 3600 + colonParts[1] * 60;
  }

  const numeric = parseInt(text.replace(/[^\d]/g, ''), 10);
  return Number.isNaN(numeric) ? 0 : numeric * 60;
}
