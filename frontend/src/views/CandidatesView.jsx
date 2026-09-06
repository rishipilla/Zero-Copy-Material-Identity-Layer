import { useEffect, useState } from 'react';
import { api } from '../api';

const TABS = [
  { id: 'pending', label: 'Pending' },
  { id: 'accepted', label: 'Accepted' },
  { id: 'rejected', label: 'Rejected' },
];

export default function CandidatesView({ onResolved }) {
  const [tab, setTab] = useState('pending');
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [resolving, setResolving] = useState(null);

  useEffect(() => {
    load(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  async function load(status) {
    setLoading(true);
    const data = await api.listMatches(status);
    setMatches(data);
    setLoading(false);
  }

  async function resolve(match, action) {
    setResolving(match.id);
    try {
      await api.resolveMatch(match.id, action);
      setMatches((prev) => prev.filter((m) => m.id !== match.id));
      onResolved();
    } finally {
      setResolving(null);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.head}>
        <h1 style={styles.h1}>Duplicate candidates</h1>
        <p style={styles.lede}>
          The engine never merges on similarity alone — a hard spec conflict always waits for you.
        </p>
      </div>

      <div style={styles.tabs}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{ ...styles.tab, ...(tab === t.id ? styles.tabActive : {}) }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <div style={styles.empty}>Loading…</div>}

      {!loading && matches.length === 0 && (
        <div style={styles.empty}>
          {tab === 'pending'
            ? 'No candidates waiting for review. Import data to generate some.'
            : `No ${tab} matches yet.`}
        </div>
      )}

      <div style={styles.list}>
        {matches.map((m) => (
          <CandidateRow
            key={m.id}
            match={m}
            expanded={expanded === m.id}
            onToggle={() => setExpanded(expanded === m.id ? null : m.id)}
            onAccept={() => resolve(m, 'accept')}
            onReject={() => resolve(m, 'reject')}
            resolving={resolving === m.id}
            showActions={tab === 'pending'}
          />
        ))}
      </div>
    </div>
  );
}

function CandidateRow({ match, expanded, onToggle, onAccept, onReject, resolving, showActions }) {
  const pct = Math.round(match.final_confidence * 100);
  const isConflict = Boolean(match.conflict_reason);
  const barColor = isConflict ? 'var(--accent-danger)' : 'var(--accent-amber)';

  return (
    <div style={styles.row}>
      <button style={styles.rowHead} onClick={onToggle}>
        <div style={styles.pairCodes}>
          <CodeBadge material={match.material_a_detail} />
          <span style={styles.pairSep}>↔</span>
          <CodeBadge material={match.material_b_detail} />
        </div>

        <div style={styles.confidenceWrap}>
          <div style={styles.confidenceTrack}>
            <div style={{ ...styles.confidenceFill, width: `${pct}%`, background: barColor }} />
          </div>
          <span style={{ ...styles.confidenceLabel, color: barColor }}>{pct}%</span>
        </div>
      </button>

      {isConflict && <div style={styles.conflictBanner}>⚠ {match.conflict_reason}</div>}

      {expanded && (
        <div style={styles.detail}>
          <AttributeDiff a={match.material_a_detail} b={match.material_b_detail} />
          <div style={styles.scoreBreakdown}>
            <ScoreItem label="Semantic" value={match.semantic_score} />
            <ScoreItem label="Attribute" value={match.attribute_score} />
            <ScoreItem label="Rule" value={match.rule_score} />
          </div>
        </div>
      )}

      {showActions && (
        <div style={styles.actions}>
          <button style={styles.rejectBtn} onClick={onReject} disabled={resolving}>
            Reject
          </button>
          <button style={styles.acceptBtn} onClick={onAccept} disabled={resolving}>
            {resolving ? 'Saving…' : isConflict ? 'Accept anyway' : 'Accept as same identity'}
          </button>
        </div>
      )}
    </div>
  );
}

function CodeBadge({ material }) {
  if (!material) return null;
  return (
    <div style={styles.codeBadge}>
      <span style={styles.codeSource}>{material.source_system}</span>
      <span style={styles.codeValue}>{material.legacy_code}</span>
      <span style={styles.codeDesc}>{material.description}</span>
    </div>
  );
}

function AttributeDiff({ a, b }) {
  const keys = Array.from(
    new Set([...(a?.attributes || []), ...(b?.attributes || [])].map((x) => x.attribute_name))
  );
  const find = (mat, key) => mat?.attributes?.find((x) => x.attribute_name === key)?.normalized_value;

  return (
    <table style={styles.diffTable}>
      <thead>
        <tr>
          <th style={styles.diffHeadCell}>Attribute</th>
          <th style={styles.diffHeadCell}>{a?.source_system}</th>
          <th style={styles.diffHeadCell}>{b?.source_system}</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((key) => {
          const va = find(a, key);
          const vb = find(b, key);
          const differs = va && vb && va !== vb;
          return (
            <tr key={key}>
              <td style={styles.diffLabelCell}>{key}</td>
              <td style={{ ...styles.diffValueCell, color: differs ? 'var(--accent-danger)' : undefined }}>
                {va || '—'}
              </td>
              <td style={{ ...styles.diffValueCell, color: differs ? 'var(--accent-danger)' : undefined }}>
                {vb || '—'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function ScoreItem({ label, value }) {
  return (
    <div style={styles.scoreItem}>
      <span style={styles.scoreLabel}>{label}</span>
      <span style={styles.scoreValue}>{Math.round(value * 100)}%</span>
    </div>
  );
}

const styles = {
  page: { maxWidth: 920, margin: '0 auto', padding: '40px 32px 80px' },
  head: { marginBottom: 20 },
  h1: { fontFamily: 'var(--font-display)', fontSize: 26, margin: '0 0 8px' },
  lede: { color: 'var(--text-muted)', margin: 0 },
  tabs: { display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid var(--border-hairline)' },
  tab: {
    background: 'transparent',
    border: 'none',
    borderBottom: '2px solid transparent',
    color: 'var(--text-muted)',
    padding: '8px 4px',
    marginRight: 20,
    fontSize: 13,
  },
  tabActive: { color: 'var(--text-primary)', borderBottomColor: 'var(--accent-amber)' },
  empty: { color: 'var(--text-faint)', fontSize: 13, padding: '40px 0', textAlign: 'center' },
  list: { display: 'flex', flexDirection: 'column', gap: 10 },
  row: {
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-md)',
    overflow: 'hidden',
  },
  rowHead: {
    width: '100%',
    background: 'transparent',
    border: 'none',
    color: 'inherit',
    padding: '14px 16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 20,
    textAlign: 'left',
  },
  pairCodes: { display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 },
  pairSep: { color: 'var(--text-faint)', flexShrink: 0 },
  codeBadge: { display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0, flex: 1 },
  codeSource: { fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-teal)' },
  codeValue: { fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600 },
  codeDesc: {
    fontSize: 12,
    color: 'var(--text-muted)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  confidenceWrap: { display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, width: 160 },
  confidenceTrack: {
    flex: 1,
    height: 5,
    background: 'var(--bg-panel-raised)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confidenceFill: { height: '100%' },
  confidenceLabel: { fontFamily: 'var(--font-mono)', fontSize: 12.5, width: 36, textAlign: 'right' },
  conflictBanner: {
    background: 'var(--accent-danger-dim)',
    color: 'var(--accent-danger)',
    fontSize: 12.5,
    padding: '7px 16px',
    borderTop: '1px solid var(--border-hairline)',
  },
  detail: { padding: '4px 16px 16px', borderTop: '1px solid var(--border-hairline)' },
  diffTable: { width: '100%', borderCollapse: 'collapse', marginTop: 12, fontSize: 12.5 },
  diffHeadCell: {
    textAlign: 'left',
    color: 'var(--text-faint)',
    fontWeight: 500,
    padding: '4px 8px',
    borderBottom: '1px solid var(--border-hairline)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
  },
  diffLabelCell: { padding: '5px 8px', color: 'var(--text-muted)' },
  diffValueCell: { padding: '5px 8px', fontFamily: 'var(--font-mono)' },
  scoreBreakdown: { display: 'flex', gap: 20, marginTop: 14 },
  scoreItem: { display: 'flex', flexDirection: 'column', gap: 2 },
  scoreLabel: { fontSize: 10.5, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: 0.4 },
  scoreValue: { fontFamily: 'var(--font-mono)', fontSize: 13 },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 8,
    padding: '10px 16px',
    borderTop: '1px solid var(--border-hairline)',
  },
  rejectBtn: {
    background: 'transparent',
    border: '1px solid var(--border-hairline)',
    color: 'var(--text-muted)',
    borderRadius: 'var(--radius-sm)',
    padding: '7px 14px',
    fontSize: 12.5,
  },
  acceptBtn: {
    background: 'var(--accent-amber)',
    border: 'none',
    color: '#1A1200',
    fontWeight: 600,
    borderRadius: 'var(--radius-sm)',
    padding: '7px 14px',
    fontSize: 12.5,
  },
};
