import { useEffect, useState } from 'react';
import { api } from '../api';

export default function AnalyticsView() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.getAnalytics().then(setData);
  }, []);

  if (!data) return null;

  const tiles = [
    { label: 'Materials imported', value: data.total_materials },
    { label: 'Canonical identities', value: data.total_identities },
    { label: 'Pending review', value: data.pending_candidates, accent: 'amber' },
    { label: 'Accepted matches', value: data.accepted_matches, accent: 'success' },
    { label: 'Rejected matches', value: data.rejected_matches },
    { label: 'Conflicts flagged', value: data.conflicts_flagged, accent: 'danger' },
  ];

  return (
    <div style={styles.page}>
      <div style={styles.head}>
        <h1 style={styles.h1}>Analytics</h1>
        <p style={styles.lede}>
          Figures reflect the current session's dataset — treat these as a live working view, not
          validated production metrics.
        </p>
      </div>

      <div style={styles.grid}>
        {tiles.map((t) => (
          <div key={t.label} style={styles.tile}>
            <div style={{ ...styles.tileValue, color: accentColor(t.accent) }}>{t.value}</div>
            <div style={styles.tileLabel}>{t.label}</div>
          </div>
        ))}
      </div>

      <div style={styles.sourcePanel}>
        <div style={styles.panelKicker}>Records by source system</div>
        <div style={styles.sourceList}>
          {Object.entries(data.source_systems).map(([name, count]) => (
            <div key={name} style={styles.sourceRow}>
              <span style={styles.sourceName}>{name}</span>
              <div style={styles.sourceBarTrack}>
                <div
                  style={{
                    ...styles.sourceBarFill,
                    width: `${(count / data.total_materials) * 100}%`,
                  }}
                />
              </div>
              <span style={styles.sourceCount}>{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function accentColor(accent) {
  if (accent === 'amber') return 'var(--accent-amber)';
  if (accent === 'success') return 'var(--accent-success)';
  if (accent === 'danger') return 'var(--accent-danger)';
  return 'var(--text-primary)';
}

const styles = {
  page: { maxWidth: 920, margin: '0 auto', padding: '40px 32px 80px' },
  head: { marginBottom: 24 },
  h1: { fontFamily: 'var(--font-display)', fontSize: 26, margin: '0 0 8px' },
  lede: { color: 'var(--text-muted)', margin: 0, maxWidth: 560 },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 12,
    marginBottom: 28,
  },
  tile: {
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-md)',
    padding: '18px 20px',
  },
  tileValue: { fontFamily: 'var(--font-mono)', fontSize: 28, fontWeight: 600, lineHeight: 1 },
  tileLabel: { fontSize: 12.5, color: 'var(--text-muted)', marginTop: 8 },
  sourcePanel: {
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-md)',
    padding: 20,
  },
  panelKicker: { fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-teal)', marginBottom: 14 },
  sourceList: { display: 'flex', flexDirection: 'column', gap: 10 },
  sourceRow: { display: 'flex', alignItems: 'center', gap: 12 },
  sourceName: { fontFamily: 'var(--font-mono)', fontSize: 12.5, width: 70, flexShrink: 0 },
  sourceBarTrack: { flex: 1, height: 6, background: 'var(--bg-panel-raised)', borderRadius: 3, overflow: 'hidden' },
  sourceBarFill: { height: '100%', background: 'var(--accent-teal)' },
  sourceCount: { fontFamily: 'var(--font-mono)', fontSize: 12.5, width: 24, textAlign: 'right' },
};
