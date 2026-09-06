import { useEffect, useRef, useState } from 'react';
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from 'd3-force';
import { api } from '../api';

const WIDTH = 760;
const HEIGHT = 520;

export default function GraphView() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [neo4jEnabled, setNeo4jEnabled] = useState(false);
  const [positions, setPositions] = useState({});
  const [selected, setSelected] = useState(null);
  const simRef = useRef(null);

  useEffect(() => {
    (async () => {
      const [g, status] = await Promise.all([api.getGraph(), api.graphStatus()]);
      setGraph(g);
      setNeo4jEnabled(status.neo4j_enabled);
    })();
  }, []);

  useEffect(() => {
    if (graph.nodes.length === 0) return;

    const nodes = graph.nodes.map((n) => ({ ...n }));
    const links = graph.edges.map((e) => ({ source: e.source, target: e.target, confidence: e.confidence }));

    const sim = forceSimulation(nodes)
      .force('link', forceLink(links).id((d) => d.id).distance(90).strength(0.6))
      .force('charge', forceManyBody().strength(-220))
      .force('center', forceCenter(WIDTH / 2, HEIGHT / 2))
      .force('collide', forceCollide(34))
      .stop();

    for (let i = 0; i < 220; i++) sim.tick();

    const posById = {};
    nodes.forEach((n) => { posById[n.id] = { x: n.x, y: n.y }; });
    setPositions(posById);
    simRef.current = { nodes, links };
  }, [graph]);

  const hasGraph = graph.nodes.length > 0;

  return (
    <div style={styles.page}>
      <div style={styles.head}>
        <h1 style={styles.h1}>Identity graph</h1>
        <p style={styles.lede}>
          One identity fans out to every legacy code it was matched to, across source systems.
          {neo4jEnabled
            ? ' Mirrored live into Neo4j.'
            : ' Rendered from the relational source of truth — connect Neo4j to also query this natively in Cypher.'}
        </p>
      </div>

      {!hasGraph && (
        <div style={styles.empty}>
          No accepted identities yet. Accept a candidate in Review to see it appear here.
        </div>
      )}

      {hasGraph && (
        <div style={styles.canvasWrap}>
          <svg width={WIDTH} height={HEIGHT} style={styles.svg}>
            {simRef.current?.links.map((l, i) => {
              const s = positions[l.source.id ?? l.source];
              const t = positions[l.target.id ?? l.target];
              if (!s || !t) return null;
              return (
                <line
                  key={i}
                  x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  stroke="var(--accent-teal)"
                  strokeOpacity={0.25 + (l.confidence || 0) * 0.5}
                  strokeWidth={1.5}
                />
              );
            })}
            {graph.nodes.map((n) => {
              const pos = positions[n.id];
              if (!pos) return null;
              const isIdentity = n.type === 'identity';
              return (
                <g
                  key={n.id}
                  transform={`translate(${pos.x}, ${pos.y})`}
                  onMouseEnter={() => setSelected(n)}
                  onMouseLeave={() => setSelected(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle
                    r={isIdentity ? 16 : 9}
                    fill={isIdentity ? 'var(--accent-amber)' : 'var(--bg-panel-raised)'}
                    stroke={isIdentity ? 'none' : 'var(--accent-teal)'}
                    strokeWidth={1.5}
                  />
                  <text
                    y={isIdentity ? 30 : 22}
                    textAnchor="middle"
                    fontSize={isIdentity ? 11 : 10}
                    fontFamily="var(--font-mono)"
                    fill={isIdentity ? 'var(--text-primary)' : 'var(--text-muted)'}
                  >
                    {isIdentity ? truncate(n.label, 18) : n.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {selected && (
            <div style={styles.tooltip}>
              <div style={styles.tooltipType}>{selected.type}</div>
              <div style={styles.tooltipLabel}>{selected.label}</div>
              {selected.source_system && <div style={styles.tooltipMeta}>{selected.source_system}</div>}
            </div>
          )}
        </div>
      )}

      <div style={styles.legend}>
        <LegendItem color="var(--accent-amber)" label="Canonical identity" filled />
        <LegendItem color="var(--accent-teal)" label="Legacy code (ERP record)" />
      </div>
    </div>
  );
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n - 1) + '…' : str;
}

function LegendItem({ color, label, filled }) {
  return (
    <div style={styles.legendItem}>
      <span
        style={{
          ...styles.legendDot,
          background: filled ? color : 'transparent',
          border: `1.5px solid ${color}`,
        }}
      />
      {label}
    </div>
  );
}

const styles = {
  page: { maxWidth: 920, margin: '0 auto', padding: '40px 32px 80px' },
  head: { marginBottom: 20 },
  h1: { fontFamily: 'var(--font-display)', fontSize: 26, margin: '0 0 8px' },
  lede: { color: 'var(--text-muted)', margin: 0, maxWidth: 640 },
  empty: { color: 'var(--text-faint)', fontSize: 13, padding: '60px 0', textAlign: 'center' },
  canvasWrap: {
    position: 'relative',
    background: 'var(--bg-panel)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-md)',
  },
  svg: { display: 'block' },
  tooltip: {
    position: 'absolute',
    top: 12,
    right: 12,
    background: 'var(--bg-panel-raised)',
    border: '1px solid var(--border-hairline)',
    borderRadius: 'var(--radius-sm)',
    padding: '8px 12px',
    fontSize: 12,
  },
  tooltipType: { color: 'var(--text-faint)', fontFamily: 'var(--font-mono)', fontSize: 10, textTransform: 'uppercase' },
  tooltipLabel: { fontWeight: 600, marginTop: 2 },
  tooltipMeta: { color: 'var(--accent-teal)', fontFamily: 'var(--font-mono)', fontSize: 11, marginTop: 2 },
  legend: { display: 'flex', gap: 20, marginTop: 16 },
  legendItem: { display: 'flex', alignItems: 'center', gap: 7, fontSize: 12, color: 'var(--text-muted)' },
  legendDot: { width: 9, height: 9, borderRadius: '50%', display: 'inline-block' },
};
