'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Monitor,
  RefreshCw,
  Search,
  Settings,
  Terminal,
  Wrench,
  X,
  Zap,
} from 'lucide-react';
import { ArenaSummary, PCStatus, PCUnit, PCZone } from '@/types/pc';
import { formatSecondsToHMS, padNumber, ZONE_SPECS } from '@/lib/pc-config';

type ZoneFilter = 'ALL' | PCZone;
type StatusFilter = 'ALL' | 'AVAILABLE' | 'IN_USE' | 'ENDING_SOON';

export default function FaukayEsportPage() {
  const [pcs, setPcs] = useState<PCUnit[]>([]);
  const [summary, setSummary] = useState<ArenaSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [zoneFilter, setZoneFilter] = useState<ZoneFilter>('ALL');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modal states
  const [selectedPc, setSelectedPc] = useState<PCUnit | null>(null);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);
  const [showGuideModal, setShowGuideModal] = useState<boolean>(false);
  const [tempSkippedVip, setTempSkippedVip] = useState<number[]>([13, 14]);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  const fetchArenaData = useCallback(async () => {
    try {
      const res = await fetch('/api/pcs', { cache: 'no-store' });
      if (!res.ok) return;
      const data = await res.json();
      setPcs(data.pcs || []);
      setSummary(data.summary || null);
      if (data.summary?.skippedVipNumbers) {
        setTempSkippedVip(data.summary.skippedVipNumbers);
      }
    } catch (err) {
      console.error('Failed to fetch PC status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Poll dari server setiap 5 detik untuk sinkronisasi dengan CyberIndo Agent
  useEffect(() => {
    fetchArenaData();
    const syncInterval = setInterval(fetchArenaData, 5000);
    return () => clearInterval(syncInterval);
  }, [fetchArenaData]);

  // Countdown real-time setiap 1 detik di sisi browser agar detik berjalan mulus
  useEffect(() => {
    const tickInterval = setInterval(() => {
      setPcs((prevPcs) =>
        prevPcs.map((pc) => {
          if (pc.status !== 'IN_USE') return pc;
          const nextSec = Math.max(0, pc.remainingSeconds - 1);
          if (nextSec === 0) {
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
            remainingSeconds: nextSec,
          };
        })
      );
    }, 1000);

    return () => clearInterval(tickInterval);
  }, []);

  // Hitung summary dinamis setiap detik mengikuti state `pcs`
  const liveSummary = useMemo(() => {
    const vvipList = pcs.filter((p) => p.zone === 'VVIP');
    const vipList = pcs.filter((p) => p.zone === 'VIP');
    const inUse = pcs.filter((p) => p.status === 'IN_USE');
    const endingSoon = inUse
      .filter((p) => p.remainingSeconds > 0 && p.remainingSeconds <= 900)
      .sort((a, b) => a.remainingSeconds - b.remainingSeconds);

    return {
      totalPCs: pcs.length,
      availablePCs: pcs.filter((p) => p.status === 'AVAILABLE').length,
      inUsePCs: inUse.length,
      endingSoonPCs: endingSoon.length,
      nearestEndingPc: endingSoon[0] || null,
      maintenancePCs: pcs.filter((p) => p.status === 'MAINTENANCE').length,
      vvipAvailable: vvipList.filter((p) => p.status === 'AVAILABLE').length,
      vvipTotal: vvipList.length,
      vipAvailable: vipList.filter((p) => p.status === 'AVAILABLE').length,
      vipTotal: vipList.length,
      syncSource: summary?.syncSource || 'SIMULATION',
      lastSyncAt: summary?.lastSyncAt || '',
      skippedVipNumbers: summary?.skippedVipNumbers || [13, 14],
    };
  }, [pcs, summary]);

  const filteredPcs = useMemo(() => {
    return pcs.filter((pc) => {
      if (zoneFilter !== 'ALL' && pc.zone !== zoneFilter) return false;
      if (statusFilter === 'AVAILABLE' && pc.status !== 'AVAILABLE') return false;
      if (statusFilter === 'IN_USE' && pc.status !== 'IN_USE') return false;
      if (
        statusFilter === 'ENDING_SOON' &&
        !(pc.status === 'IN_USE' && pc.remainingSeconds > 0 && pc.remainingSeconds <= 900)
      ) {
        return false;
      }
      if (searchQuery.trim() !== '') {
        const q = searchQuery.toLowerCase().trim();
        const matchName = pc.name.toLowerCase().includes(q) || pc.id.toLowerCase().includes(q);
        const matchUser = pc.currentUser?.toLowerCase().includes(q);
        return matchName || matchUser;
      }
      return true;
    });
  }, [pcs, zoneFilter, statusFilter, searchQuery]);

  const vvipFiltered = useMemo(
    () => filteredPcs.filter((p) => p.zone === 'VVIP'),
    [filteredPcs]
  );
  const vipFiltered = useMemo(
    () => filteredPcs.filter((p) => p.zone === 'VIP'),
    [filteredPcs]
  );

  const handleRandomizeSimulation = async () => {
    setIsSyncing(true);
    try {
      const res = await fetch('/api/pcs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'RANDOMIZE' }),
      });
      if (res.ok) {
        const data = await res.json();
        setPcs(data.pcs);
        setSummary(data.summary);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSaveSkippedVip = async () => {
    if (tempSkippedVip.length !== 2) {
      alert('Silakan pilih tepat 2 nomor PC VIP (antara 07 s/d 36) yang tidak dipakai/dilewati.');
      return;
    }
    setIsSyncing(true);
    try {
      const res = await fetch('/api/pcs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: 'MANUAL_ADMIN',
          skippedVipNumbers: tempSkippedVip.sort((a, b) => a - b),
          pcs: [],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPcs(data.pcs);
        setSummary(data.summary);
        setShowConfigModal(false);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  const handleManualPcUpdate = async (
    pc: PCUnit,
    newStatus: PCStatus,
    minutesToAdd: number,
    packageLabel: string
  ) => {
    setIsSyncing(true);
    try {
      const remainingSeconds = newStatus === 'IN_USE' ? minutesToAdd * 60 : 0;
      const res = await fetch('/api/pcs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source: 'MANUAL_ADMIN',
          pcs: [
            {
              id: pc.id,
              status: newStatus,
              remainingSeconds,
              totalSeconds: Math.max(remainingSeconds, 3600),
              packageType: packageLabel,
            },
          ],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setPcs(data.pcs);
        setSummary(data.summary);
        setSelectedPc(null);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  const toggleSkippedNumber = (num: number) => {
    setTempSkippedVip((prev) => {
      if (prev.includes(num)) {
        return prev.filter((n) => n !== num);
      }
      if (prev.length >= 2) {
        return [prev[1], num];
      }
      return [...prev, num];
    });
  };

  const renderPcCard = (pc: PCUnit) => {
    const isEndingSoon =
      pc.status === 'IN_USE' && pc.remainingSeconds > 0 && pc.remainingSeconds <= 900;

    let cardClass = 'pc-card ';
    let badgeClass = 'pc-status-badge ';
    let badgeText = '';

    if (pc.status === 'AVAILABLE') {
      cardClass += 'status-available';
      badgeClass += 'badge-available';
      badgeText = 'KOSONG';
    } else if (pc.status === 'MAINTENANCE') {
      cardClass += 'status-maintenance';
      badgeClass += 'badge-maintenance';
      badgeText = 'MAINT';
    } else if (isEndingSoon) {
      cardClass += 'status-ending';
      badgeClass += 'badge-ending';
      badgeText = 'SEGERA HABIS';
    } else {
      cardClass += 'status-inuse';
      badgeClass += 'badge-inuse';
      badgeText = 'AKTIF';
    }

    const progressPercent =
      pc.status === 'IN_USE' && pc.totalSeconds > 0
        ? Math.min(100, Math.max(4, Math.round((pc.remainingSeconds / pc.totalSeconds) * 100)))
        : 0;

    return (
      <button
        key={pc.id}
        type="button"
        className={cardClass}
        onClick={() => setSelectedPc(pc)}
        title={`Klik untuk detail / simulasi kontrol ${pc.name}`}
      >
        <div className="pc-card-top">
          <span className="pc-name">{pc.name}</span>
          <span className={badgeClass}>{badgeText}</span>
        </div>

        <div className="pc-card-middle">
          {pc.status === 'IN_USE' ? (
            <>
              <span className="pc-timer-label">Sisa Waktu Billing</span>
              <span className="pc-timer-value">
                {formatSecondsToHMS(pc.remainingSeconds)}
              </span>
            </>
          ) : pc.status === 'AVAILABLE' ? (
            <>
              <span className="pc-timer-label">Status Kursi</span>
              <span className="pc-ready-big">SIAP PAKAI</span>
            </>
          ) : (
            <>
              <span className="pc-timer-label">Status Kursi</span>
              <span className="pc-maint-big">PERBAIKAN</span>
            </>
          )}
        </div>

        <div className="pc-card-bottom">
          <div className="pc-meta-row">
            <span>{pc.packageType}</span>
            {pc.status === 'IN_USE' && (
              <span style={{ color: isEndingSoon ? '#ff6b72' : '#94a3b8' }}>
                {Math.ceil(pc.remainingSeconds / 60)} mnt
              </span>
            )}
          </div>
          {pc.status === 'IN_USE' ? (
            <div className="pc-progress-track">
              <div
                className="pc-progress-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          ) : (
            <div
              className="pc-progress-track"
              style={{
                background:
                  pc.status === 'AVAILABLE'
                    ? 'rgba(16, 185, 129, 0.28)'
                    : 'rgba(100, 116, 139, 0.2)',
              }}
            />
          )}
        </div>
      </button>
    );
  };

  return (
    <div className="app-shell">
      {/* Top Brand Header */}
      <header className="top-header">
        <div className="brand-cluster">
          <div className="brand-logo-frame">
            <img
              src="/logo.png"
              alt="Faukay E-Sport Logo"
              className="brand-logo-img"
            />
          </div>
          <div className="brand-titles">
            <span className="brand-eyebrow">
              <Zap size={13} /> CYBERINDO LIVE TELEMETRY SYSTEM
            </span>
            <h1 className="brand-main-name">
              <span>[ FAUKAY ]</span>
              <span className="brand-esport-ribbon">E-SPORT</span>
            </h1>
            <p className="brand-subtitle">
              Real-Time Status PC & Sisa Waktu Billing • 18 VVIP & 28 VIP
            </p>
          </div>
        </div>

        <div className="header-actions">
          <div className="live-pill">
            <span className="live-dot" />
            <span>
              {liveSummary.syncSource === 'CYBERINDO_AGENT'
                ? 'TERHUBUNG: CYBERINDO KASIR'
                : 'LIVE MODE: SIMULASI AKTIF'}
            </span>
          </div>

          <button
            type="button"
            className="btn-tactical"
            onClick={() => setShowConfigModal(true)}
          >
            <Settings size={15} />
            <span>Atur PC VIP</span>
          </button>

          <button
            type="button"
            className="btn-tactical"
            onClick={handleRandomizeSimulation}
            disabled={isSyncing}
          >
            <RefreshCw size={15} />
            <span>Acak Simulasi</span>
          </button>

          <button
            type="button"
            className="btn-tactical btn-tactical-primary"
            onClick={() => setShowGuideModal(true)}
          >
            <Terminal size={15} />
            <span>Cara Konek CyberIndo</span>
          </button>

          <a
            href="/login"
            className="btn-tactical"
            style={{ textDecoration: 'none' }}
          >
            <span>Login Staff</span>
          </a>
        </div>
      </header>

      {/* 4 Telemetry Summary Cards */}
      <section className="telemetry-grid">
        <div className="stat-card stat-ready">
          <div className="stat-top">
            <span>PC KOSONG (TERSEDIA)</span>
            <CheckCircle2 size={17} color="#10b981" />
          </div>
          <div className="stat-value-row">
            <span className="stat-number">{liveSummary.availablePCs}</span>
            <span className="stat-unit">dari {liveSummary.totalPCs} PC Siap Pakai</span>
          </div>
          <div className="stat-subtext">
            <span>VVIP Kosong: <strong>{liveSummary.vvipAvailable}</strong></span>
            <span>•</span>
            <span>VIP Kosong: <strong>{liveSummary.vipAvailable}</strong></span>
          </div>
        </div>

        <div className="stat-card stat-inuse">
          <div className="stat-top">
            <span>PC SEDANG DIGUNAKAN</span>
            <Activity size={17} color="#ea8215" />
          </div>
          <div className="stat-value-row">
            <span className="stat-number">{liveSummary.inUsePCs}</span>
            <span className="stat-unit">Unit Aktif Bermain</span>
          </div>
          <div className="stat-subtext">
            <span>Okupansi Arena: <strong>{liveSummary.totalPCs > 0 ? Math.round((liveSummary.inUsePCs / liveSummary.totalPCs) * 100) : 0}%</strong></span>
          </div>
        </div>

        <div className="stat-card stat-ending">
          <div className="stat-top">
            <span>SEGERA HABIS (&lt; 15 MENIT)</span>
            <AlertTriangle size={17} color="#e50914" />
          </div>
          <div className="stat-value-row">
            <span className="stat-number">{liveSummary.endingSoonPCs}</span>
            <span className="stat-unit">PC Sebentar Lagi Kosong</span>
          </div>
          <div className="stat-subtext">
            {liveSummary.nearestEndingPc ? (
              <span>
                Tercepat: <strong style={{ color: '#ff6b72' }}>{liveSummary.nearestEndingPc.name}</strong> ({formatSecondsToHMS(liveSummary.nearestEndingPc.remainingSeconds)})
              </span>
            ) : (
              <span>Semua PC masih memiliki sisa waktu &gt; 15 menit</span>
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>KAPASITAS FAUKAY E-SPORT</span>
            <Cpu size={17} color="#94a3b8" />
          </div>
          <div className="stat-value-row">
            <span className="stat-number">{liveSummary.totalPCs}</span>
            <span className="stat-unit">Total Workstation</span>
          </div>
          <div className="stat-subtext">
            <span>18 VVIP (01-18)</span>
            <span>•</span>
            <span>28 VIP (07-36)</span>
          </div>
        </div>
      </section>

      {/* Filter & Search Bar */}
      <section className="control-bar">
        <div className="filter-group">
          <button
            type="button"
            className={`filter-tab ${zoneFilter === 'ALL' ? 'active' : ''}`}
            onClick={() => setZoneFilter('ALL')}
          >
            <Monitor size={14} /> SEMUA ZONA ({liveSummary.totalPCs})
          </button>
          <button
            type="button"
            className={`filter-tab ${zoneFilter === 'VVIP' ? 'active-red' : ''}`}
            onClick={() => setZoneFilter('VVIP')}
          >
            ZONA VVIP ({liveSummary.vvipAvailable}/{liveSummary.vvipTotal} Kosong)
          </button>
          <button
            type="button"
            className={`filter-tab ${zoneFilter === 'VIP' ? 'active' : ''}`}
            onClick={() => setZoneFilter('VIP')}
          >
            ZONA VIP ({liveSummary.vipAvailable}/{liveSummary.vipTotal} Kosong)
          </button>
        </div>

        <div className="filter-group">
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ALL' ? 'active' : ''}`}
            onClick={() => setStatusFilter('ALL')}
          >
            Semua Status
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'AVAILABLE' ? 'active-green' : ''}`}
            onClick={() => setStatusFilter('AVAILABLE')}
          >
            Hanya Kosong ({liveSummary.availablePCs})
          </button>
          <button
            type="button"
            className={`filter-tab ${statusFilter === 'ENDING_SOON' ? 'active-red' : ''}`}
            onClick={() => setStatusFilter('ENDING_SOON')}
          >
            <Clock size={14} /> Segera Habis ({liveSummary.endingSoonPCs})
          </button>
        </div>

        <div className="search-box">
          <Search size={15} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Cari nomor PC (misal: VVIP 05, VIP 12)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </section>

      {loading ? (
        <div style={{ padding: '4rem 0', textAlign: 'center', color: '#94a3b8' }}>
          Memuat data telemetri PC Faukay E-Sport...
        </div>
      ) : (
        <>
          {/* ZONA VVIP (18 PC: 01 - 18) */}
          {(zoneFilter === 'ALL' || zoneFilter === 'VVIP') && (
            <section className="zone-section">
              <div className="zone-header">
                <div className="zone-title-wrap">
                  <div className="zone-title-row">
                    <h2 className="zone-title">{ZONE_SPECS.VVIP.title}</h2>
                    <span className="zone-badge-vvip">{ZONE_SPECS.VVIP.badge}</span>
                  </div>
                  <p className="zone-specs">{ZONE_SPECS.VVIP.specs}</p>
                </div>
                <div className="zone-availability-pill">
                  TERSEDIA: {liveSummary.vvipAvailable} / {liveSummary.vvipTotal} PC
                </div>
              </div>

              {vvipFiltered.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
                  Tidak ada PC VVIP yang cocok dengan filter saat ini.
                </p>
              ) : (
                <div className="pc-grid">{vvipFiltered.map(renderPcCard)}</div>
              )}
            </section>
          )}

          {/* ZONA VIP (28 PC: 07 - 36) */}
          {(zoneFilter === 'ALL' || zoneFilter === 'VIP') && (
            <section className="zone-section">
              <div className="zone-header">
                <div className="zone-title-wrap">
                  <div className="zone-title-row">
                    <h2 className="zone-title">{ZONE_SPECS.VIP.title}</h2>
                    <span className="zone-badge-vip">{ZONE_SPECS.VIP.badge}</span>
                  </div>
                  <p className="zone-specs">
                    {ZONE_SPECS.VIP.specs} • (Nomor VIP tidak dipakai:{' '}
                    {liveSummary.skippedVipNumbers.map((n) => `VIP ${padNumber(n)}`).join(', ')})
                  </p>
                </div>
                <div className="zone-availability-pill">
                  TERSEDIA: {liveSummary.vipAvailable} / {liveSummary.vipTotal} PC
                </div>
              </div>

              {vipFiltered.length === 0 ? (
                <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
                  Tidak ada PC VIP yang cocok dengan filter saat ini.
                </p>
              ) : (
                <div className="pc-grid">{vipFiltered.map(renderPcCard)}</div>
              )}
            </section>
          )}
        </>
      )}

      {/* Modal Detail & Kontrol Manual PC */}
      {selectedPc && (
        <div className="modal-backdrop" onClick={() => setSelectedPc(null)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">{selectedPc.name} — DETAIL & KONTROL</h3>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  Zona {selectedPc.zone} • {selectedPc.specs}
                </p>
              </div>
              <button
                type="button"
                className="btn-tactical"
                onClick={() => setSelectedPc(null)}
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'grid', gap: '1rem' }}>
              <div
                style={{
                  background: '#0b0c10',
                  padding: '1rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.08)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>STATUS SAAT INI</div>
                  <div
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '1.25rem',
                      fontWeight: 700,
                      color:
                        selectedPc.status === 'AVAILABLE'
                          ? '#34d399'
                          : selectedPc.status === 'IN_USE'
                          ? '#ff9829'
                          : '#94a3b8',
                    }}
                  >
                    {selectedPc.status === 'AVAILABLE'
                      ? 'KOSONG (SIAP PAKAI)'
                      : selectedPc.status === 'IN_USE'
                      ? 'SEDANG DIGUNAKAN'
                      : 'MAINTENANCE / PERBAIKAN'}
                  </div>
                </div>
                {selectedPc.status === 'IN_USE' && (
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>SISA WAKTU</div>
                    <div
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '1.45rem',
                        fontWeight: 800,
                        color: '#ff9829',
                      }}
                    >
                      {formatSecondsToHMS(selectedPc.remainingSeconds)}
                    </div>
                  </div>
                )}
              </div>

              <div>
                <p
                  style={{
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    color: '#cbd5e1',
                    marginBottom: '0.6rem',
                  }}
                >
                  Simulasi / Ubah Status Manual untuk {selectedPc.name}:
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.55rem' }}>
                  <button
                    type="button"
                    className="btn-tactical"
                    style={{ borderColor: '#10b981', color: '#34d399' }}
                    onClick={() =>
                      handleManualPcUpdate(selectedPc, 'AVAILABLE', 0, 'Siap Pakai')
                    }
                  >
                    <CheckCircle2 size={15} /> Set PC Kosong
                  </button>
                  <button
                    type="button"
                    className="btn-tactical"
                    onClick={() =>
                      handleManualPcUpdate(selectedPc, 'IN_USE', 10, 'Sisa < 15 Menit')
                    }
                  >
                    <Clock size={15} /> Set Sisa 10 Menit
                  </button>
                  <button
                    type="button"
                    className="btn-tactical"
                    onClick={() =>
                      handleManualPcUpdate(selectedPc, 'IN_USE', 60, 'Paket 1 Jam')
                    }
                  >
                    <Zap size={15} /> Set Paket 1 Jam
                  </button>
                  <button
                    type="button"
                    className="btn-tactical"
                    onClick={() =>
                      handleManualPcUpdate(selectedPc, 'IN_USE', 180, 'Paket 3 Jam')
                    }
                  >
                    <Zap size={15} /> Set Paket 3 Jam
                  </button>
                  <button
                    type="button"
                    className="btn-tactical"
                    onClick={() =>
                      handleManualPcUpdate(
                        selectedPc,
                        'MAINTENANCE',
                        0,
                        'Maintenance / Cek Gear'
                      )
                    }
                  >
                    <Wrench size={15} /> Set Maintenance
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Pengaturan 2 Nomor VIP yang Dilewati (07-36 -> 28 PC) */}
      {showConfigModal && (
        <div className="modal-backdrop" onClick={() => setShowConfigModal(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">PENGATURAN NOMOR PC VIP (28 UNIT)</h3>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  Pilih 2 nomor di rentang VIP (07 s/d 36) yang tidak dipakai/dilewati di warnet Anda.
                </p>
              </div>
              <button
                type="button"
                className="btn-tactical"
                onClick={() => setShowConfigModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            <div>
              <p style={{ fontSize: '0.84rem', color: '#e2e8f0' }}>
                Nomor yang dilewati saat ini:{' '}
                <strong style={{ color: '#ff6b72' }}>
                  {tempSkippedVip.length > 0
                    ? tempSkippedVip.map((n) => `VIP-${padNumber(n)}`).join(' & ')
                    : 'Belum dipilih'}
                </strong>{' '}
                (Total VIP Aktif: {30 - tempSkippedVip.length} PC)
              </p>

              <div className="skip-number-grid">
                {Array.from({ length: 30 }, (_, i) => i + 7).map((num) => {
                  const isSelected = tempSkippedVip.includes(num);
                  return (
                    <button
                      key={num}
                      type="button"
                      className={`skip-num-btn ${isSelected ? 'selected' : ''}`}
                      onClick={() => toggleSkippedNumber(num)}
                    >
                      VIP {padNumber(num)}
                    </button>
                  );
                })}
              </div>

              <div
                style={{
                  marginTop: '1.25rem',
                  display: 'flex',
                  justifyContent: 'flex-end',
                  gap: '0.75rem',
                }}
              >
                <button
                  type="button"
                  className="btn-tactical"
                  onClick={() => setShowConfigModal(false)}
                >
                  Batal
                </button>
                <button
                  type="button"
                  className="btn-tactical btn-tactical-primary"
                  onClick={handleSaveSkippedVip}
                >
                  Simpan Konfigurasi VIP
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Panduan Koneksi CyberIndo di PC Kasir */}
      {showGuideModal && (
        <div className="modal-backdrop" onClick={() => setShowGuideModal(false)}>
          <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 className="modal-title">CARA MENGHUBUNGKAN KE CYBERINDO KASIR</h3>
                <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                  Langkah praktis saat nanti Anda berada di PC Server Billing Kasir Faukay E-Sport
                </p>
              </div>
              <button
                type="button"
                className="btn-tactical"
                onClick={() => setShowGuideModal(false)}
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ fontSize: '0.86rem', color: '#cbd5e1', lineHeight: 1.6 }}>
              <p style={{ marginBottom: '0.75rem' }}>
                Di dalam proyek ini sudah disiapkan folder{' '}
                <code style={{ color: '#ff9829' }}>cyberindo-agent/</code> yang berisi program jembatan untuk PC Kasir:
              </p>

              <p>
                <strong>Langkah 1 — Jalankan Pendeteksi Otomatis di PC Kasir</strong>
                <br />
                Copy folder <code style={{ color: '#ff9829' }}>cyberindo-agent</code> ke PC Kasir, lalu jalankan script PowerShell berikut untuk mendeteksi otomatis letak database CyberIndo dan daftar kolom tabel aplikasinya:
              </p>
              <div className="code-step-box">
                powershell -ExecutionPolicy Bypass -File .\cyberindo-agent\inspect-cyberindo.ps1
              </div>

              <p>
                <strong>Langkah 2 — Jalankan CyberIndo Live Reader Agent</strong>
                <br />
                Gunakan pembaca otomatis tampilan tabel CyberIndo Kasir (<code style={{ color: '#ff9829' }}>cyberindo-ui-reader.py</code>) atau Node.js Agent yang mengirim status 18 PC VVIP & 28 PC VIP setiap 3 detik ke website ini:
              </p>
              <div className="code-step-box">
                # Mode Pembaca Tabel Aplikasi CyberIndo Server (Python):{'\n'}
                pip install pywinauto requests{'\n'}
                python .\cyberindo-agent\cyberindo-ui-reader.py --url http://localhost:3000/api/pcs{'\n\n'}
                # Atau Mode Node.js Agent:{'\n'}
                node .\cyberindo-agent\agent.js --url=http://localhost:3000/api/pcs
              </div>

              <p style={{ color: '#94a3b8', fontSize: '0.8rem' }}>
                Catatan: Saat website ini sudah di-online-kan ke Vercel (misal{' '}
                <code>https://faukay-esport.vercel.app</code>), cukup ganti parameter{' '}
                <code>--url</code> dengan alamat website Vercel Anda.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
