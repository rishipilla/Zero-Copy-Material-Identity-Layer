const NAV_ITEMS = [
  { id: 'import', label: 'Import', glyph: '01' },
  { id: 'candidates', label: 'Review', glyph: '02' },
  { id: 'graph', label: 'Identity graph', glyph: '03' },
  { id: 'analytics', label: 'Analytics', glyph: '04' },
];

export default function Sidebar({ active, onSelect, pendingCount }) {
  return (
    <nav style={styles.rail}>
      <div style={styles.mark}>
        <div style={styles.markGlyph}>ZC</div>
        <div style={styles.markText}>
          <div style={styles.markTitle}>Zero-Copy</div>
          <div style={styles.markSub}>Material Identity</div>
        </div>
      </div>

      <div style={styles.items}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            style={{
              ...styles.item,
              ...(active === item.id ? styles.itemActive : {}),
            }}
          >
            <span style={styles.itemGlyph}>{item.glyph}</span>
            <span>{item.label}</span>
            {item.id === 'candidates' && pendingCount > 0 && (
              <span style={styles.badge}>{pendingCount}</span>
            )}
          </button>
        ))}
      </div>

      <div style={styles.footer}>
        <div style={styles.footerLine}>Team Jolly Rogers</div>
        <div style={styles.footerLine}>SIH26099</div>
      </div>
    </nav>
  );
}

const styles = {
  rail: {
    width: 220,
    flexShrink: 0,
    background: 'var(--bg-panel)',
    borderRight: '1px solid var(--border-hairline)',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 14px',
  },
  mark: { display: 'flex', alignItems: 'center', gap: 10, padding: '0 6px 24px' },
  markGlyph: {
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    fontSize: 13,
    color: 'var(--bg-base)',
    background: 'var(--accent-amber)',
    width: 30,
    height: 30,
    borderRadius: 'var(--radius-sm)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  markText: { lineHeight: 1.25 },
  markTitle: { fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14 },
  markSub: { fontSize: 11, color: 'var(--text-muted)' },
  items: { display: 'flex', flexDirection: 'column', gap: 2, flex: 1 },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    background: 'transparent',
    border: 'none',
    color: 'var(--text-muted)',
    padding: '9px 10px',
    borderRadius: 'var(--radius-sm)',
    fontSize: 13.5,
    textAlign: 'left',
    position: 'relative',
  },
  itemActive: {
    background: 'var(--bg-panel-raised)',
    color: 'var(--text-primary)',
  },
  itemGlyph: {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    color: 'var(--text-faint)',
    width: 16,
  },
  badge: {
    marginLeft: 'auto',
    background: 'var(--accent-amber-dim)',
    color: 'var(--accent-amber)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    padding: '1px 6px',
    borderRadius: 999,
  },
  footer: {
    borderTop: '1px solid var(--border-hairline)',
    paddingTop: 12,
    fontSize: 11,
    color: 'var(--text-faint)',
    fontFamily: 'var(--font-mono)',
  },
  footerLine: { lineHeight: 1.6 },
};
