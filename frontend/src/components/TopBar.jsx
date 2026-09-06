const STAGES = ['Import', 'Normalize', 'Match', 'Review', 'Graph'];

export default function TopBar({ activeStageIndex, sourceSystems }) {
  return (
    <header style={styles.bar}>
      <div style={styles.pipeline}>
        {STAGES.map((stage, i) => (
          <div key={stage} style={styles.stageWrap}>
            <div
              style={{
                ...styles.stage,
                color: i <= activeStageIndex ? 'var(--text-primary)' : 'var(--text-faint)',
              }}
            >
              <span
                style={{
                  ...styles.stageDot,
                  background: i <= activeStageIndex ? 'var(--accent-amber)' : 'var(--border-hairline)',
                }}
              />
              {stage}
            </div>
            {i < STAGES.length - 1 && <span style={styles.stageSep}>—</span>}
          </div>
        ))}
      </div>

      <div style={styles.sources}>
        {Object.entries(sourceSystems || {}).map(([name, count]) => (
          <div key={name} style={styles.sourceChip}>
            <span style={styles.sourceName}>{name}</span>
            <span style={styles.sourceCount}>{count}</span>
          </div>
        ))}
      </div>
    </header>
  );
}

const styles = {
  bar: {
    height: 52,
    flexShrink: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    borderBottom: '1px solid var(--border-hairline)',
    background: 'var(--bg-base)',
  },
  pipeline: { display: 'flex', alignItems: 'center', gap: 8 },
  stageWrap: { display: 'flex', alignItems: 'center', gap: 8 },
  stage: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontFamily: 'var(--font-mono)' },
  stageDot: { width: 6, height: 6, borderRadius: '50%', display: 'inline-block' },
  stageSep: { color: 'var(--text-faint)', fontSize: 12 },
  sources: { display: 'flex', gap: 8 },
  sourceChip: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-sm)',
    padding: '4px 9px',
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
  },
  sourceName: { color: 'var(--text-muted)' },
  sourceCount: { color: 'var(--text-primary)', fontWeight: 600 },
};
