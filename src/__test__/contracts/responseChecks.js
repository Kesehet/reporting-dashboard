import {
  dataParser, generateBarChartData, generatePieChartData, generateLineChartData,
  generateStackedBarChartData, generateBarWithLineChartData,
} from '../../Utils/Components/Utils';
import { normalizeChartPayload } from '../../Utils/Components/CardReport';

const generators = {
  pie: generatePieChartData, bar: generateBarChartData, line: generateLineChartData,
  stacked: generateStackedBarChartData, mixed: generateBarWithLineChartData,
};

export function responseProblems(wire, kind, name) {
  const issues = [];
  if (!wire || typeof wire !== 'object') return ['response-not-object'];
  const p = dataParser(JSON.parse(JSON.stringify(wire)));
  if (generators[kind]) {
    if (!Array.isArray(p.labels)) return ['missing-labels'];
    const source = kind === 'line' ? Object.values(p.datasetMap || {})
      : ['stacked','mixed'].includes(kind) ? (p.list || []).map(s => s.data) : [p.list];
    if (source.some(s => !Array.isArray(s))) return ['missing-series-data'];
    if (source.some(s => s.length !== p.labels.length)) issues.push('labels-series-length-mismatch');
    let generated;
    try { generated = generators[kind](p, name, true); }
    catch (e) { return [...issues, `adapter-throws:${e.message}`]; }
    if (!Array.isArray(generated.labels) || !Array.isArray(generated.datasets)) return [...issues, 'adapter-dropped-chart'];
    if (JSON.stringify(generated.labels) !== JSON.stringify(p.labels)) issues.push('adapter-changed-label-order');
    if (generated.datasets.length !== source.length) issues.push('adapter-dropped-series');
    if (generated.datasets.some(s => !Array.isArray(s.data) || s.data.some(v => !Number.isFinite(v)))) issues.push('non-finite-chart-value');
    if (generated.datasets.some(s => s.data.length !== p.labels.length)) issues.push('adapter-length-mismatch');
    return [...new Set(issues)].sort();
  }
  if (kind === 'object-table') {
    if (!Array.isArray(p.headers) || !Array.isArray(p.rows)) return ['missing-object-table-headers-or-rows'];
    return p.rows.every(r => r && typeof r === 'object' && !Array.isArray(r)) ? [] : ['object-table-row-not-object'];
  }
  if (kind === 'table' || kind === 'multi-table') {
    if (!Array.isArray(p.headers)) return ['missing-headers'];
    const sets = kind === 'multi-table' ? Object.values(p.rowSets || {}) : [p.rows];
    if (sets.some(s => !Array.isArray(s))) return ['missing-rows'];
    for (const rows of sets) {
      if (rows.some(row => !Array.isArray(row))) issues.push('table-row-not-array');
      const widths = [...new Set(rows.filter(Array.isArray).map(row => row.length))];
      // One-cell section labels are intentionally used in existing grouped reports.
      const wrong = widths.filter(n => n !== p.headers.length && n !== 1);
      if (wrong.length) issues.push(`table-width:${p.headers.length}:rows:${wrong.sort((a,b) => a-b).join(',')}`);
    }
    return [...new Set(issues)].sort();
  }
  if (kind === 'tracking-codes') {
    return Array.isArray(p) && p.every(a => Array.isArray(a) && a.every(v => typeof v === 'string')) ? [] : ['tracking-codes-not-nested-string-arrays'];
  }
  if (kind === 'insights') {
    const normalized = normalizeChartPayload(p);
    if (!normalized || typeof normalized !== 'object' || Array.isArray(normalized)) return ['insights-not-key-values'];
    const keys = Object.keys(p).filter(k => !k.startsWith('_report_'));
    if (!p.headers && !p.data && keys.some(k => !(k in normalized))) issues.push('insight-keys-dropped');
    return issues;
  }
  // Backend-only handlers still receive a structural check; do not infer intent
  // from an endpoint's English name when an actual consumer is unavailable.
  if ('headers' in p) return responseProblems(p, 'rowSets' in p ? 'multi-table' : 'table', name);
  if ('labels' in p) {
    const inferred = p.datasetMap ? 'line' : p.list?.some(x => x && typeof x === 'object') ? 'stacked' : 'bar';
    return responseProblems(p, inferred, name);
  }
  if (Array.isArray(p) && name !== 'Transaction Logger Recent Txns') return ['unexpected-top-level-array'];
  return [];
}
