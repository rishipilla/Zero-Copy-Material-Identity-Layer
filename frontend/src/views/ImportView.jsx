import { useState } from 'react';
import { api } from '../api';

export default function ImportView({ onImported }) {
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState([]);
  const [sourceSystem, setSourceSystem] = useState('SAP-C');
  const [error, setError] = useState(null);

  async function runSampleImport() {
    setBusy(true);
    setError(null);
    try {
      const results = await api.importSample();
      setLog((prev) => [...results.map(describeResult), ...prev]);
      onImported();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api.importCsv(sourceSystem, file);
      setLog((prev) => [describeResult(result), ...prev]);
      onImported();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
      e.target.value = '';
    }
  }

  async function handleReset() {
    if (!confirm('Clear every imported material, match, and identity? This cannot be undone.')) return;
    setBusy(true);
    try {
      await api.resetAll();
      setLog([]);
      onImported();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.intro}>
        <h1 style={styles.h1}>Bring in ERP records</h1>
        <p style={styles.lede}>
          Each source ERP's material list is read in as-is — nothing here rewrites or migrates
          the original rows. Import the two bundled datasets to see the whole pipeline run, or
          upload your own CSV per source system.
        </p>
      </div>

      <div style={styles.grid}>
        <section style={styles.panel}>
          <div style={styles.panelHead}>
            <span style={styles.panelKicker}>Fastest path</span>
            <h2 style={styles.panelTitle}>Load the demo datasets</h2>
          </div>
          <p style={styles.panelBody}>
            Two synthetic ERPs (SAP-A, SAP-B) with the same fasteners described differently —
            including one deliberate spec conflict, so you can see the review queue catch it.
          </p>
          <button style={styles.primaryBtn} onClick={runSampleImport} disabled={busy}>
            {busy ? 'Importing…' : 'Load sample ERP-A + ERP-B'}
          </button>
        </section>

        <section style={styles.panel}>
          <div style={styles.panelHead}>
            <span style={styles.panelKicker}>Your data</span>
            <h2 style={styles.panelTitle}>Upload a CSV</h2>
          </div>
          <p style={styles.panelBody}>
            Columns required: <code className="mono">legacy_code</code>,{' '}
            <code className="mono">description</code>. Optional: manufacturer, category, unit,
            specifications.
          </p>
          <label style={styles.label}>
            Source system name
            <input
              style={styles.input}
              value={sourceSystem}
              onChange={(e) => setSourceSystem(e.target.value)}
              placeholder="e.g. SAP-C"
            />
          </label>
          <label style={styles.fileBtn}>
            {busy ? 'Working…' : 'Choose CSV file'}
            <input type="file" accept=".csv" onChange={handleFile} disabled={busy} hidden />
          </label>
        </section>
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {log.length > 0 && (
        <section style={styles.logPanel}>
          <div style={styles.panelKicker}>Import log</div>
          <div style={styles.logList}>
            {log.map((entry, i) => (
              <div key={i} style={styles.logRow}>
                <span style={styles.logSource}>{entry.source_system}</span>
                <span style={styles.logDetail}>
                  {entry.imported} imported · {entry.skipped} skipped ·{' '}
                  {entry.matches_generated} candidates generated
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      <button style={styles.resetLink} onClick={handleReset} disabled={busy}>
        Clear all data
      </button>
    </div>
  );
}

function describeResult(r) {
  return r;
}

const styles = {
  page: { maxWidth: 880, margin: '0 auto', padding: '40px 32px 80px' },
  intro: { marginBottom: 32 },
  h1: { fontFamily: 'var(--font-display)', fontSize: 26, margin: '0 0 10px' },
  lede: { color: 'var(--text-muted)', maxWidth: 620, margin: 0 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  panel: {
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-md)',
    padding: 22,
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  panelHead: { marginBottom: 2 },
  panelKicker: {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    color: 'var(--accent-teal)',
    display: 'block',
    marginBottom: 6,
  },
  panelTitle: { fontFamily: 'var(--font-display)', fontSize: 16, margin: 0 },
  panelBody: { color: 'var(--text-muted)', fontSize: 13, margin: 0, lineHeight: 1.6 },
  primaryBtn: {
    marginTop: 'auto',
    background: 'var(--accent-amber)',
    color: '#1A1200',
    border: 'none',
    borderRadius: 'var(--radius-sm)',
    padding: '10px 16px',
    fontWeight: 600,
    fontSize: 13.5,
    alignSelf: 'flex-start',
  },
  label: { fontSize: 12.5, color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: 6 },
  input: {
    background: 'var(--bg-panel-raised)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-sm)',
    padding: '8px 10px',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
    fontSize: 13,
  },
  fileBtn: {
    marginTop: 'auto',
    background: 'var(--bg-panel-raised)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-sm)',
    padding: '10px 16px',
    fontSize: 13.5,
    textAlign: 'center',
    alignSelf: 'flex-start',
  },
  error: {
    marginTop: 20,
    background: 'var(--accent-danger-dim)',
    color: 'var(--accent-danger)',
    border: '1px solid var(--accent-danger)',
    borderRadius: 'var(--radius-sm)',
    padding: '10px 14px',
    fontSize: 13,
  },
  logPanel: { marginTop: 28 },
  logList: { display: 'flex', flexDirection: 'column', gap: 6, marginTop: 10 },
  logRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: 12.5,
    padding: '9px 12px',
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-sm)',
  },
  logSource: { fontFamily: 'var(--font-mono)', color: 'var(--accent-teal)' },
  logDetail: { color: 'var(--text-muted)' },
  resetLink: {
    marginTop: 32,
    background: 'transparent',
    border: 'none',
    color: 'var(--text-faint)',
    fontSize: 12,
    textDecoration: 'underline',
    padding: 0,
  },
};
