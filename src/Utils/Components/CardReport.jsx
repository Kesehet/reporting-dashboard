// CardReport.jsx
import React, { useEffect, useState } from 'react';
import ChartDataService from '../../Services/ChartDataService';
import CellDataService from '../../Services/CellDataService';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { DataTable } from 'primereact/datatable';
// If a project-level helper exists to resolve table queries, reuse it:
import getCellData from './Utils';
import FNBDataTable from './FNBDataTable';

export default function CardReport({
  CHART_NAME,
  params = {},                 // optional params passed to ChartDataService
  title = CHART_NAME || 'Report',
  renderOrder = [],            // optional: specify key ordering
  cardWidth = 260              // optional: tune card width
}) {
  const [kv, setKv] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dialogVisible, setDialogVisible] = useState(false);
  const [dialogData, setDialogData] = useState(null);
  const [dialogHeader, setDialogHeader] = useState('Data');

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

  const openDialogFor = async (reportKey, label) => {
    try {
      const spec = kv[reportKey]; // could be a query spec or already a dataset
      const rows = await getCellData(spec); // resolves to an array of objects for table rendering
      setDialogData(rows);
      setDialogHeader(label);
      setDialogVisible(true);
    } catch (e) {
      console.error('Failed to load dialog data:', e);
      setDialogData([]);
      setDialogHeader(label);
      setDialogVisible(true);
    }
  };

  const exportCsvFor = async (reportKey, filename = 'report.csv') => {
    const spec = kv[reportKey];
    const rows = await getCellData(spec);
    if (!rows || rows.length === 0) {
      triggerDownload('data:text/csv;charset=utf-8,', filename);
      return;
    }
    const headers = Object.keys(rows[0]);
    const csvRows = [
      headers.join(','),
      ...rows.map(r => headers.map(h => `"${(r[h] ?? '').toString().replace(/"/g, '""')}"`).join(','))
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    triggerDownload(url, filename);
    URL.revokeObjectURL(url);
  };

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
              setDialogVisible(false);
              setDialogData(null);
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
        <div className="flex flex-wrap gap-3">
          {keys.map((key) => {
            const reportSiblingKey = `_report_${key}`;
            const hasReport = Object.prototype.hasOwnProperty.call(kv, reportSiblingKey);
            return (
              <div
                key={key}
                className="p-card p-component p-2"
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
                  <div style={{ fontSize: '.95rem', color: '#555' }}>
                    <CellDataService query={kv[key]} />
                  </div>
                </div>

                {hasReport && (
                  <div className="pt-2 flex gap-2">
                    <Button
                      icon="pi pi-file"
                      label="Export"
                      className="p-button-text"
                      onClick={() => exportCsvFor(reportSiblingKey, `${sanitize(title)} - ${sanitize(key)}.csv`)}
                    />
                    <Button
                      icon="pi pi-eye"
                      label="View"
                      className="p-button-text"
                      onClick={() => openDialogFor(reportSiblingKey, `${key} • Details`)}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <Dialog
        header={dialogHeader}
        visible={dialogVisible}
        style={{ width: '100vw', height: '100vh', margin: '0 auto' }}
        onHide={() => setDialogVisible(false)}
        maximizable
      >
        {Array.isArray(dialogData) && dialogData.length > 0 ? (
            <>
          <DataTable value={dialogData} 
            paginator 
            rows={10} 
            className="p-datatable-responsive p-datatable-sm"
            responsiveLayout="scroll"
            showGridlines
            style={{ width: '100%' }}
            sortMode="multiple"
            filterDisplay="menu"
            globalFilterFields={Object.keys(dialogData[0])}
          >
            {/* First column ordering preserved as given by object keys */}
            <DataTable.Column field="Date" header="Date" sortable />
            {Object.keys(dialogData[0]).map((k) => k === 'Date' ? null : (
              <DataTable.Column key={k} field={k} header={k} sortable />
            ))}
          </DataTable>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <p>No data to display</p>
          </div>
        )}
      </Dialog>
    </div>
  );
}

/* ----------------- helpers ----------------- */

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

function triggerDownload(href, filename) {
  const link = document.createElement('a');
  link.href = href;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
