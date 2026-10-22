import fs from 'fs';
import path from 'path';
import zlib from 'zlib';
import fetchMock from 'jest-fetch-mock';
import { inventory as sourceConsumers } from '../../../scripts/chart-consumers.cjs';
import ChartDataService from '../../Services/ChartDataService';
import getCellData, { generateBarChartData } from '../../Utils/Components/Utils';
import { responseProblems } from './responseChecks';

const root = path.resolve(__dirname, '../../..');
const out = path.join(root, 'contract-results');
const inventoryFile = path.join(out, 'inventory.json');

// The ordinary UI suite must run on a clean checkout without generated Python
// artifacts. The dedicated chart-contract command separately checks that the
// inventory and cases exist before running this suite.
if (!fs.existsSync(inventoryFile)) {
  test.skip('Chart contract fixtures not generated; run npm run test:charts to validate chart responses', () => {});
} else {
const manifest = JSON.parse(fs.readFileSync(inventoryFile));
const allowancePath = path.join(root, 'tests/contracts/frontend-known-issues.json');
const known = process.env.ACCEPT_CHART_BASELINE === '1' ? {} : JSON.parse(fs.readFileSync(allowancePath));
const observed = {};
const issueRows = [];
const read = entry => JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(out, 'cases', entry.file))));

beforeEach(() => {
  fetchMock.enableMocks();
  fetchMock.resetMocks();
  localStorage.clear();
  localStorage.setItem('start_date', '2026-01-01');
  localStorage.setItem('end_date', '2026-03-31');
  localStorage.setItem('CorBFilter', 'C');
});

test('JSX/service endpoint inventory agrees with generated backend cases', () => {
  expect(sourceConsumers()).toEqual(manifest.consumers);
  const available = new Set(manifest.backend_handlers);
  manifest.consumers.forEach(c => expect(available.has(c.name)).toBe(true));
  expect(new Set(manifest.cases.map(c => c.name))).toEqual(available);
});

for (const entry of manifest.cases) {
  test(entry.id, async () => {
    const c = read(entry);
    if (c.response.status !== 200) {
      // Python checks each known 500 by exact name/scenario/message. This is a
      // tested known defect, not a payload falsely claimed consumable by the FE.
      issueRows.push({case: c.id, kind: 'backend-error', detail: c.response.payload.error});
      expect(c.response.status).toBe(500);
      return;
    }
    const matched = manifest.consumers.filter(v => v.name === c.name && Object.entries(v.params).every(([k,vv]) => c.params[k] === vv));
    const kinds = [...new Set(matched.map(c => c.kind))];
    if (!kinds.length) kinds.push('unreferenced');
    const problems = [];
    for (const kind of kinds) {
      // Validate raw numbers AND the comma-formatted production wire response.
      for (const mode of ['response', 'rawResponse']) {
        const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
        try { problems.push(...responseProblems(c[mode].payload, kind, c.name).map(p => `${kind}:${mode}:${p}`)); }
        finally { spy.mockRestore(); }
      }
    }
    const actual = [...new Set(problems)].sort();
    observed[c.id] = actual;
    if (actual.length) issueRows.push({case: c.id, kind: 'frontend-contract', detail: actual});
    if (process.env.ACCEPT_CHART_BASELINE !== '1') expect(actual).toEqual(known[c.id] || []);

    // Run the real FE request serializer against these real backend route bytes.
    // This proves the service retains the payload; it is not a live HTTP integration.
    for (const method of ['GET', 'POST']) {
      fetch.mockResponseOnce(JSON.stringify(c.response.payload));
      const service = new ChartDataService(c.name, {...c.params, requestMethod: method});
      expect(await service.getChart()).toEqual(c.response.payload);
      const [url, opts] = fetch.mock.calls[fetch.mock.calls.length - 1];
      expect(opts.method).toBe(method);
      expect(decodeURI(url)).toContain('/charts/' + c.name);
      if (method === 'POST') {
        const body = JSON.parse(opts.body);
        expect(body.start_date).toBe('2026-01-01');
        expect(body.eCATrackingCode).toBe('C');
      } else {
        expect(new URL(url).searchParams.get('start_date')).toBe('2026-01-01');
      }
    }
    // Deferred SQL is sent by the existing table resolver to the real /query
    // response captured in Python, including currency/comma formatting.
    for (const [sql, r] of Object.entries(c.deferred)) {
      expect(r.status).toBe(200);
      fetch.mockResponseOnce(typeof r.value === 'string' ? r.value : JSON.stringify(r.value));
      const value = await getCellData(sql);
      expect(value).toEqual(typeof r.value === 'string' ? r.value : JSON.stringify(r.value));
      const [, opts] = fetch.mock.calls[fetch.mock.calls.length - 1];
      expect(JSON.parse(opts.body)).toEqual({query: sql});
    }
  });
}

test('contract oracle detects malformed data instead of accepting every response', () => {
  expect(responseProblems({labels: ['Jan'], list: [3,4]}, 'bar', 'mutation')).toContain('labels-series-length-mismatch');
  expect(responseProblems({labels: ['Jan'], datasetMap: {Apps: ['SELECT bad']}}, 'line', 'mutation')).toContain('non-finite-chart-value');
  expect(responseProblems({headers:['a','b'],rows:[[1,2,3]]},'table','mutation')).toContain('table-width:2:rows:3');
  expect(responseProblems({labels:['Jan'],list:[1234]},'bar','valid')).toEqual([]);
  expect(generateBarChartData({labels:['Jan','Feb'],list:['1,234.50','-12.25']},'format',true).datasets[0].data).toEqual([1234.5,-12.25]);
});

afterAll(() => {
  const mismatches = Object.fromEntries(Object.entries(observed).filter(([,issues]) => issues.length));
  fs.writeFileSync(path.join(out, 'frontend-observed.json'), JSON.stringify(mismatches, null, 2) + '\n');
  fs.writeFileSync(path.join(out, 'frontend-issues.json'), JSON.stringify(issueRows, null, 2) + '\n');
  if (process.env.ACCEPT_CHART_BASELINE === '1') fs.writeFileSync(allowancePath, JSON.stringify(mismatches, null, 2) + '\n');
  else expect(Object.keys(known).sort()).toEqual(Object.keys(mismatches).sort());
});
}
