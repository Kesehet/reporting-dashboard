// CardReport.jsx
import React, { useEffect, useState } from 'react';
import ChartDataService from '../../Services/ChartDataService';
import CellDataService from '../../Services/CellDataService';
import { Button } from 'primereact/button';
import ReportActions from './ReportActions';

export default function CardReport({
  CHART_NAME,
  params = {},                 // optional params passed to ChartDataService
  title = CHART_NAME || 'Report',
  renderOrder = [],            // optional: specify key ordering
  cardWidth = 260              // optional: tune card width
}) {
  const [kv, setKv] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    const fetchData = async () => {
      setLoading(true);
      try {
        const svc = new ChartDataService(CHART_NAME, params);
        const payload = await svc.getChart();

        // Normalize payload into a simple key-value object:
        const normalized = normalizeChartPayload(payload);
        if (active) setKv(normalized);
      } catch (e) {
        console.error('CardReport fetch error:', e);
        if (active) setKv({});
      } finally {
        if (active) setLoading(false);
      }
    };

    fetchData();
    return () => { active = false; };
  }, [CHART_NAME, JSON.stringify(params)]);

  const keys = kv
    ? (() => {
        const raw = Object.keys(kv).filter(k => !k.startsWith('_report_'));
        const ordered = renderOrder.concat(raw.filter(k => !renderOrder.includes(k)));
        return ordered;
      })()
    : [];

  return (
    <div className="p-3">
      <div className="flex align-items-center justify-content-between mb-3">
        <h3 className="m-0">{title}</h3>
        <div className="flex gap-2">
          <Button
            icon="pi pi-refresh"
            label="Refresh"
            onClick={() => {
              setKv(null);
              // re-trigger effect by changing params shallowly
              // (parent can also pass a new key to force refresh)
              const svc = new ChartDataService(CHART_NAME, params);
              setLoading(true);
              svc.getChart()
                .then(p => setKv(normalizeChartPayload(p)))
                .catch(e => { console.error(e); setKv({}); })
                .finally(() => setLoading(false));
            }}
            text
          />
        </div>
      </div>

      {loading && (
        <div className="flex gap-2 align-items-center">
          <i className="pi pi-spin pi-spinner" style={{ fontSize: '1.25rem' }} />
          <span>Loading…</span>
        </div>
      )}

      {!loading && kv && keys.length === 0 && (
        <div className="text-500">No data.</div>
      )}

      {!loading && kv && keys.length > 0 && (
        <div className="report-cards report-cards-centered">
              {getBox(keys, kv, cardWidth, title)}
        </div>
      )}
    </div>
  );
}

/* ----------------- helpers ----------------- */

function getBox(keys, kv, cardWidth, title) {
  return keys.map((key) => {
            const reportSiblingKey = `_report_${key}`;
            const hasReport = Object.prototype.hasOwnProperty.call(kv, reportSiblingKey);
            return (
              <div
                key={key}
                className="report-card p-card p-component p-2"
                style={{
                  width: cardWidth,
                  boxShadow: '0 2px 4px rgba(0,0,0,.08)',
                  borderRadius: 8,
                  background: '#f9f9f9'
                }}
              >
                <div className="p-card-header" style={{ marginBottom: '.35rem' }}>
                  <h4 style={{ margin: 0, fontSize: '1.05rem', color: '#333' }}>{key}</h4>
                </div>
                <div className="p-card-body">
                  {/* Use CellDataService to render cell/value */}
                  {/* If the value is a query spec, CellDataService resolves it; otherwise it should render the primitive */}
                  {/* If the value is a json object we can render it as key value pair with bold keys and normal values */}
                  {typeof kv[key] === 'object' && kv[key] !== null ? (
                    <div style={{ fontSize: '.95rem', color: '#555' }}>
                      {Object.entries(kv[key]).map(([k, v]) => (
                        <div key={k}>
                          <strong>{k}:</strong> <CellDataService query={v}/>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '.95rem', color: '#555' }}>
                      <CellDataService query={kv[key]}/>
                    </div>
                  )}


                </div>

                {hasReport && (
                  <div className="pt-2 flex gap-2">
                    <ReportActions
                      report={kv[reportSiblingKey]}
                      filename={`${sanitize(title)} - ${sanitize(key)}.csv`}
                      dialogHeader={`${key} Details`}
                    />
                  </div>
                )}
              </div>
            );
          })
}





function normalizeChartPayload(payload) {
  // Accepts a variety of shapes and returns a flat key-value object.
  if (!payload) return {};
  // If payload is already a plain object of kv pairs:
  if (!Array.isArray(payload) && typeof payload === 'object' && !payload.headers && !payload.rows && !payload.data) {
    return payload;
  }
  // If payload.data is the kv object:
  if (payload && payload.data && typeof payload.data === 'object' && !Array.isArray(payload.data)) {
    return payload.data;
  }
  // If headers/rows (e.g., single row): map headers -> first row.
  if (payload.headers && payload.rows) {
    if (Array.isArray(payload.rows) && payload.rows.length > 0) {
      const first = payload.rows[0];
      // rows may be already objects or arrays; handle both:
      if (typeof first === 'object' && !Array.isArray(first)) {
        return first;
      }
      if (Array.isArray(first)) {
        const out = {};
        payload.headers.forEach((h, idx) => { out[h] = first[idx]; });
        return out;
      }
    }
    return {};
  }
  return {};
}

function sanitize(name = '') {
  return String(name).replace(/[\\/:*?"<>|]+/g, ' ').trim();
}


// Share the existing adapter with response-contract tests; no rendering behavior changes.
export { normalizeChartPayload };
