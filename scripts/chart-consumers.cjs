// Static inventory comes from JSX and service calls, not a duplicate endpoint list.
const fs = require('fs');
const path = require('path');
const parser = require('@babel/parser');
const root = path.resolve(__dirname, '..');
const kinds = {
  FNBPieChart: 'pie', FNBBarChart: 'bar', FNBLineChart: 'line',
  FNBStackedBarChart: 'stacked', FNBBarWithLineChart: 'mixed',
  FNBTable: 'table', FNBDataTable: 'table', FNBMultiTable: 'multi-table',
  FNBReport: 'object-table', BOR: 'object-table', BORAsync: 'object-table', FNBTileSet: 'object-table',
  CardReport: 'insights', OneShotChart: 'table', MultiFilterChart: 'table',
  MultiFilterTable: 'table'
};
function literal(n) {
  if (!n) return undefined;
  if (n.type === 'JSXExpressionContainer') return literal(n.expression);
  if (['StringLiteral', 'BooleanLiteral', 'NumericLiteral'].includes(n.type)) return n.value;
  if (n.type === 'ObjectExpression') {
    const out = {};
    for (const p of n.properties) {
      const value = literal(p.value);
      if (value !== undefined) out[p.key.name || p.key.value] = value;
    }
    return out;
  }
}
function inventory() {
  const out = [];
  function add(name, component, file, line, params = {}) {
    if (typeof name === 'string') out.push({name, component, kind: kinds[component] || 'service', file, line, params});
  }
  function scan(dir) {
    for (const item of fs.readdirSync(dir, {withFileTypes: true})) {
      if (item.name === '__test__') continue;
      const file = path.join(dir, item.name);
      if (item.isDirectory()) { scan(file); continue; }
      if (!/\.[jt]sx?$/.test(file)) continue;
      const rel = path.relative(root, file).split(path.sep).join('/');
      const ast = parser.parse(fs.readFileSync(file, 'utf8'), {sourceType: 'module', plugins: ['jsx']});
      function walk(n) {
        if (!n || typeof n !== 'object') return;
        if (n.type === 'JSXOpeningElement' && kinds[n.name.name]) {
          const attrs = Object.fromEntries(n.attributes.filter(a => a.type === 'JSXAttribute').map(a => [a.name.name, literal(a.value)]));
          add(attrs.data || attrs.chartName || attrs.CHART_NAME, n.name.name, rel, n.loc.start.line,
            attrs.chartAPIParams || attrs.extraParams || attrs.params || {});
        }
        if (n.type === 'NewExpression' && n.callee.name === 'ChartDataService') {
          const name = literal(n.arguments[0]);
          add(name, 'ChartDataService', rel, n.loc.start.line, literal(n.arguments[1]) || {});
          // TransactionLogger reads the first nested list from this service.
          if (name === 'Transaction Logger Recent Txns') out[out.length - 1].kind = 'tracking-codes';
        }
        // Default endpoint props in reusable report components.
        if (n.type === 'AssignmentPattern' && ['chartName','CHART_NAME'].includes(n.left.name)) {
          const component = path.basename(file).replace(/\.[^.]+$/, '');
          if (kinds[component]) add(literal(n.right), component, rel, n.loc.start.line);
        }
        for (const v of Object.values(n)) {
          if (Array.isArray(v)) v.forEach(walk);
          else if (v && typeof v === 'object') walk(v);
        }
      }
      walk(ast);
    }
  }
  scan(path.join(root, 'src'));
  return out;
}
module.exports = {inventory};
if (require.main === module) process.stdout.write(JSON.stringify(inventory(), null, 2) + '\n');
