import { NextRequest, NextResponse } from 'next/server';
import {
  getLiveArenaState,
  randomizeSimulation,
  syncFromBillingPayload,
} from '@/lib/pc-store';
import { BillingSyncPayload } from '@/types/pc';

export const dynamic = 'force-dynamic';

export async function GET() {
  const data = getLiveArenaState();
  return NextResponse.json(data, {
    headers: {
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    if (body?.action === 'RANDOMIZE') {
      const data = randomizeSimulation(body.skippedVipNumbers);
      return NextResponse.json({ ok: true, ...data });
    }

    const expectedSecret = process.env.FAUKAY_SYNC_SECRET;
    if (expectedSecret && body?.secret !== expectedSecret) {
      return NextResponse.json(
        { ok: false, error: 'Invalid sync secret key' },
        { status: 401 }
      );
    }

    const payload: BillingSyncPayload = {
      source: body.source || 'CYBERINDO_AGENT',
      skippedVipNumbers: body.skippedVipNumbers,
      pcs: Array.isArray(body.pcs) ? body.pcs : [],
    };

    const data = syncFromBillingPayload(payload);
    return NextResponse.json({ ok: true, ...data });
  } catch (err) {
    return NextResponse.json(
      {
        ok: false,
        error: err instanceof Error ? err.message : 'Invalid request payload',
      },
      { status: 400 }
    );
  }
}
