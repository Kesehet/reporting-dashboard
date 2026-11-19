import React, { useEffect, useMemo, useState } from 'react';
import { Button } from 'primereact/button';
import { Column } from 'primereact/column';
import { DataTable } from 'primereact/datatable';
import { downloadOppiqReport, getOppiqReport } from '../Services/OppiqReportService';

const COLUMN_LABELS = {
    Banker_Name: 'Banker Name',
    Lead_Assigned_By: 'Lead Assigned By',
    Customer_Name: 'Customer Name',
    BRANCHID: 'Branch ID',
    CLIENTID: 'Client ID',
    LEADID: 'Lead ID',
    PRODUCT_NAME: 'Product Name',
    Lead_Assigned_On: 'Lead Assigned On',
    Lead_Status: 'Lead Status',
};

export default function OppiqReportTab() {
    const [page, setPage] = useState(0);
    const [pageSize, setPageSize] = useState(50);
    const [refreshKey, setRefreshKey] = useState(0);
    const [report, setReport] = useState({ headers: [], rows: [], total: 0 });
    const [loading, setLoading] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError('');

        getOppiqReport(page + 1, pageSize, controller.signal)
            .then((result) => {
                if (!Array.isArray(result.headers) || !Array.isArray(result.rows)) {
                    throw new Error('Invalid OPPIQ report response.');
                }
                setReport(result);
            })
            .catch((issue) => {
                if (issue.name !== 'AbortError') {
                    setReport({ headers: [], rows: [], total: 0 });
                    setError(issue.message || 'Unable to load OPPIQ report.');
                }
            })
            .finally(() => {
                if (!controller.signal.aborted) setLoading(false);
            });

        return () => controller.abort();
    }, [page, pageSize, refreshKey]);

    const rows = useMemo(
        () => report.rows.map((values, index) => {
            const item = { rowKey: page * pageSize + index };
            report.headers.forEach((field, column) => {
                item[field] = values[column] ?? '';
            });
            return item;
        }),
        [report, page, pageSize]
    );

    const refresh = () => {
        setPage(0);
        setRefreshKey((value) => value + 1);
    };

    const exportCsv = async () => {
        if (exporting) return;
        setExporting(true);
        setError('');
        try {
            await downloadOppiqReport();
        } catch (issue) {
            setError(issue.message || 'Unable to export OPPIQ report.');
        } finally {
            setExporting(false);
        }
    };

    return (
        <div className="w3-container w3-card-4" style={{ padding: '24px' }}>
            <h2 className="w3-center">OPPIQ Report</h2>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
                <span>{loading ? 'Loading leads...' : report.total.toLocaleString() + ' matching records'}</span>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <Button label="Refresh" icon="pi pi-refresh" outlined onClick={refresh} disabled={loading} />
                    <Button label={exporting ? 'Exporting...' : 'Export as CSV'} icon="pi pi-download" onClick={exportCsv} loading={exporting} disabled={loading} />
                </div>
            </div>
            {error && <p role="alert" style={{ color: '#b91c1c' }}>{error}</p>}
            <DataTable
                value={rows}
                dataKey="rowKey"
                className="p-datatable-striped"
                paginator
                lazy
                first={page * pageSize}
                rows={pageSize}
                totalRecords={report.total}
                rowsPerPageOptions={[25, 50, 100]}
                onPage={(event) => {
                    setPage(event.page);
                    setPageSize(event.rows);
                }}
                loading={loading}
                showGridlines
                scrollable
                scrollHeight="65vh"
                emptyMessage={error ? 'Report unavailable' : 'No matching leads found'}
            >
                {report.headers.map((field) => (
                    <Column key={field} field={field} header={COLUMN_LABELS[field] || field} style={{ minWidth: '150px' }} />
                ))}
            </DataTable>
        </div>
    );
}
