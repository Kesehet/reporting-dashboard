import React, { useEffect, useState } from 'react';
import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import apiBaseUrl from '../Services/apiBaseUrl';
import sessionHeaders from '../Services/sessionHeaders';

export function recordTabVisit(tab) {
    return fetch(apiBaseUrl() + '/usage-report/tab', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', ...sessionHeaders() },
        body: JSON.stringify({ tab }),
    }).catch(() => {});
}

const total = (rows, key = 'count') => rows.reduce((sum, row) => sum + (row[key] || 0), 0);

function ReportTable({ title, rows, tab = false, chart = false }) {
    return (
        <section style={{ marginTop: '24px' }}>
            <h3>{title}</h3>
            <DataTable value={rows} paginator rows={10} rowsPerPageOptions={[10, 25, 50]}
                sortField="count" sortOrder={-1} stripedRows showGridlines scrollable emptyMessage="No records">
                <Column field="name" header={tab ? 'Tab' : chart ? 'Chart' : 'API'} sortable />
                {!tab && !chart && <Column field="method" header="Method" sortable />}
                <Column field="count" header={tab ? 'Visits' : 'Requests'} sortable />
                {!tab && <Column field="avg_ms" header="Average (ms)" sortable />}
                {!tab && <Column field="max_ms" header="Maximum (ms)" sortable />}
                {!tab && <Column field="errors" header="Errors" sortable />}
                {chart && <Column field="cache_hits" header="Cache hits" sortable />}
                {chart && <Column field="cache_misses" header="Cache misses" sortable />}
            </DataTable>
        </section>
    );
}

export default function UsageReportTab() {
    const [report, setReport] = useState({ api: [], chart: [], tab: [], hourly: [], cache_warm_requests: 0 });
    const [refresh, setRefresh] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError('');
        fetch(apiBaseUrl() + '/usage-report', {
            credentials: 'same-origin', headers: sessionHeaders(), signal: controller.signal,
        }).then(response => {
            if (!response.ok) throw new Error('Report unavailable');
            return response.json();
        }).then(data => {
            if (!controller.signal.aborted) setReport(data);
        }).catch(issue => {
            if (!controller.signal.aborted) setError(issue.message);
        }).finally(() => {
            if (!controller.signal.aborted) setLoading(false);
        });
        return () => controller.abort();
    }, [refresh]);

    const cards = [
        ['API requests', total(report.api)],
        ['Chart requests', total(report.chart)],
        ['Tab visits', total(report.tab)],
        ['Errors', total(report.api, 'errors')],
        ['Cache hits', total(report.chart, 'cache_hits')],
        ['Cache warming requests', report.cache_warm_requests],
    ];
    const slowest = [...report.chart].sort((a, b) => b.avg_ms - a.avg_ms).slice(0, 10);
    const hourly = Object.values(report.hourly.reduce((hours, row) => {
        if (!hours[row.hour]) hours[row.hour] = { hour: row.hour, api: 0, chart: 0, tab: 0 };
        hours[row.hour][row.kind] = row.count;
        return hours;
    }, {})).sort((a, b) => b.hour - a.hour);
    return (
        <div className="w3-container w3-card-4" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2>Usage Report — Last 24 Hours</h2>
                <Button label="Refresh" icon="pi pi-refresh" outlined disabled={loading}
                    onClick={() => setRefresh(value => value + 1)} />
            </div>
            {loading && <span role="status">Loading…</span>}
            {error && <span role="alert">{error}</span>}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: '12px' }}>
                {cards.map(([label, value]) => (
                    <div className="w3-card" key={label} style={{ padding: '16px' }}>
                        <div>{label}</div><h2>{value.toLocaleString()}</h2>
                    </div>
                ))}
            </div>
            <ReportTable title="Tabs" rows={report.tab} tab />
            <ReportTable title="Charts" rows={report.chart} chart />
            <section style={{ marginTop: '24px' }}>
                <h3>Slowest charts</h3>
                <DataTable value={slowest} sortField="avg_ms" sortOrder={-1} stripedRows showGridlines emptyMessage="No records">
                    <Column field="name" header="Chart" sortable />
                    <Column field="avg_ms" header="Average (ms)" sortable />
                    <Column field="max_ms" header="Maximum (ms)" sortable />
                    <Column field="count" header="Requests" sortable />
                </DataTable>
            </section>
            <ReportTable title="APIs" rows={report.api} />
            <section style={{ marginTop: '24px' }}>
                <h3>Hourly activity</h3>
                <DataTable value={hourly} paginator rows={12} stripedRows showGridlines emptyMessage="No records">
                    <Column field="hour" header="Hour" body={row => new Date(row.hour * 1000).toLocaleString()} sortable />
                    <Column field="api" header="API requests" sortable />
                    <Column field="chart" header="Chart requests" sortable />
                    <Column field="tab" header="Tab visits" sortable />
                </DataTable>
            </section>
        </div>
    );
}
