/**
 * FAUKAY E-SPORT — CyberIndo Sync Agent (Node.js)
 * ===============================================
 * Dapat dijalankan di PC Kasir maupun di laptop untuk mengirim update status 46 PC
 * (18 VVIP + 28 VIP) ke endpoint API website Faukay E-Sport.
 *
 * Cara pakai:
 *   node cyberindo-agent/agent.js --url=http://localhost:3000/api/pcs
 */

const args = Object.fromEntries(
  process.argv.slice(2).map((arg) => {
    const [k, v] = arg.replace(/^--/, '').split('=');
    return [k, v ?? 'true'];
  })
);

const API_URL = args.url || process.env.FAUKAY_API_URL || 'http://localhost:3000/api/pcs';
const SYNC_SECRET = args.secret || process.env.FAUKAY_SYNC_SECRET || '';
const INTERVAL_MS = parseInt(args.interval || '4000', 10);

function pad(n) {
  return String(n).padStart(2, '0');
}

// Daftar 18 PC VVIP (01-18) & 28 PC VIP (07-36 dengan skip 13 & 14)
function generateInitialFleet(skippedVip = [13, 14]) {
  const skipSet = new Set(skippedVip);
  const fleet = [];

  for (let i = 1; i <= 18; i++) {
    const active = i % 3 !== 0;
    const rem = active ? 600 + ((i * 520) % 9000) : 0;
    fleet.push({
      id: `VVIP-${pad(i)}`,
      status: active ? 'IN_USE' : 'AVAILABLE',
      remainingSeconds: rem,
      totalSeconds: active ? Math.max(rem, 7200) : 0,
      packageType: active ? 'Paket VVIP' : 'Siap Pakai',
    });
  }

  for (let i = 7; i <= 36; i++) {
    if (skipSet.has(i)) continue;
    const active = i % 4 !== 0;
    const rem = active ? 420 + ((i * 410) % 7200) : 0;
    fleet.push({
      id: `VIP-${pad(i)}`,
      status: active ? 'IN_USE' : 'AVAILABLE',
      remainingSeconds: rem,
      totalSeconds: active ? Math.max(rem, 7200) : 0,
      packageType: active ? 'Billing CyberIndo' : 'Siap Pakai',
    });
  }

  return fleet;
}

const fleetState = generateInitialFleet();

async function pushSync() {
  const stepSeconds = Math.round(INTERVAL_MS / 1000);

  for (const pc of fleetState) {
    if (pc.status === 'IN_USE') {
      pc.remainingSeconds = Math.max(0, pc.remainingSeconds - stepSeconds);
      if (pc.remainingSeconds === 0) {
        pc.status = 'AVAILABLE';
        pc.totalSeconds = 0;
        pc.packageType = 'Siap Pakai';
      }
    }
  }

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        secret: SYNC_SECRET,
        source: 'CYBERINDO_AGENT',
        pcs: fleetState,
      }),
    });

    if (response.ok) {
      const activeCount = fleetState.filter((p) => p.status === 'IN_USE').length;
      console.log(
        `[${new Date().toLocaleTimeString()}] SYNC OK -> ${activeCount}/${fleetState.length} PC Aktif dikirim ke ${API_URL}`
      );
    } else {
      console.error(`[SYNC ERROR] HTTP ${response.status}`);
    }
  } catch (err) {
    console.error(`[CONNECTION ERROR] Gagal menghubungi ${API_URL}:`, err.message);
  }
}

console.log('============================================================');
console.log(' FAUKAY E-SPORT — CYBERINDO AGENT');
console.log(` Target Endpoint : ${API_URL}`);
console.log('============================================================');

pushSync();
setInterval(pushSync, INTERVAL_MS);
