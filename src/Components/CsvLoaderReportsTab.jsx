import React, { useEffect, useState } from 'react';
import CsvReportService from '../Services/CsvReportService';

function CsvLoaderReportsTab() {
    const [reports, setReports] = useState([]);
    const [search, setSearch] = useState('');
    const [statusFilter, setStatusFilter] = useState('pending');
    const [dateFilter, setDateFilter] = useState('7');
    const [rowCountFilter, setRowCountFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [checkingFile, setCheckingFile] = useState(null);
    const [loadingFile, setLoadingFile] = useState(null);
    const [batchProgress, setBatchProgress] = useState(null);
    const [trackingResults, setTrackingResults] = useState({});
    const csvReportService = new CsvReportService();

    const loadReports = async () => {
        setLoading(true);
        try {
            const data = await csvReportService.getReportStatus({
                status: statusFilter,
                date_filter: dateFilter,
            });
            setReports(data.files || []);
        } catch (error) {
            console.error(error);
            setReports([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadReports();
    }, [statusFilter, dateFilter]);

    const filteredReports = reports.filter((report) => {
        const rowCount = Number(report.row_count) || 0;
        const matchesSearch = report.name.toLowerCase().includes(search.toLowerCase());
        const matchesRowCount = rowCountFilter === 'all'
            || (rowCountFilter === 'zero' && rowCount === 0)
            || (rowCountFilter === 'under100' && rowCount > 0 && rowCount < 100)
            || (rowCountFilter === 'over100' && rowCount > 100);

        return matchesSearch && matchesRowCount;
    });
    const pendingReports = filteredReports.filter((report) => !report.processed);

    const handleTrackingCheck = async (report) => {
        setCheckingFile(report.name);
        try {
            const result = await csvReportService.checkTrackingCodes(report.name);
            setTrackingResults((prev) => ({ ...prev, [report.name]: result }));
        } catch (error) {
            console.error(error);
            setTrackingResults((prev) => ({
                ...prev,
                [report.name]: {
                    file_name: report.name,
                    tracking_codes: [],
                    present_count: 0,
                    missing_count: 0,
                    error: 'Unable to verify tracking codes.'
                }
            }));
        } finally {
            setCheckingFile(null);
        }
    };

    const handleLoadReport = async (report) => {
        setLoadingFile(report.name);
        try {
            await csvReportService.loadReportFile(report.name);
            setTrackingResults((prev) => ({ ...prev, [report.name]: null }));
            return { name: report.name, success: true };
        } catch (error) {
            console.error(error);
            setTrackingResults((prev) => ({
                ...prev,
                [report.name]: {
                    file_name: report.name,
                    tracking_codes: [],
                    present_count: 0,
                    missing_count: 0,
                    error: error.message || 'Unable to load the file into the database.'
                }
            }));
            return { name: report.name, success: false, error: error.message };
        } finally {
            setLoadingFile(null);
        }
    };

    const handleLoadPendingReports = async () => {
        if (pendingReports.length === 0 || batchProgress?.active) {
            return;
        }

        const reportsToLoad = [...pendingReports];
        setBatchProgress({ active: true, total: reportsToLoad.length, completed: 0, current: reportsToLoad[0].name, failed: [] });

        const failed = [];
        for (let index = 0; index < reportsToLoad.length; index += 1) {
            const report = reportsToLoad[index];
            setBatchProgress((prev) => ({ ...prev, current: report.name }));
            const result = await handleLoadReport(report);
            if (!result.success) {
                failed.push(result.name);
            }
            setBatchProgress((prev) => ({
                ...prev,
                completed: index + 1,
                failed: [...failed],
            }));
            await loadReports();
        }

        setBatchProgress((prev) => ({ ...prev, active: false, current: null, failed }));
    };

    const batchPercent = batchProgress && batchProgress.total > 0
        ? Math.round((batchProgress.completed / batchProgress.total) * 100)
        : 0;

    return (
        <div className="w3-container w3-card-4" style={{ padding: '24px' }}>
            <h2 className="w3-center">CSV Loader Reports</h2>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <input
                    type="text"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Search reports"
                    style={{ width: '260px', padding: '10px 12px', borderRadius: '6px', border: '1px solid #d9d9d9' }}
                />

                <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d9d9d9' }}>
                    <option value="all">All statuses</option>
                    <option value="loaded">Loaded</option>
                    <option value="pending">Pending</option>
                </select>

                <select value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d9d9d9' }}>
                    <option value="all">All dates</option>
                    <option value="7">Last 7 days</option>
                    <option value="30">Last 30 days</option>
                    <option value="90">Last 90 days</option>
                </select>

                <select value={rowCountFilter} onChange={(event) => setRowCountFilter(event.target.value)} style={{ padding: '10px 12px', borderRadius: '6px', border: '1px solid #d9d9d9' }}>
                    <option value="all">All row counts</option>
                    <option value="zero">0 rows</option>
                    <option value="under100">1-99 rows</option>
                    <option value="over100">More than 100 rows</option>
                </select>

                <div style={{ fontWeight: 600 }}>
                    {reports.filter((report) => report.processed).length} loaded / {reports.length} files
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
                <button
                    type="button"
                    onClick={handleLoadPendingReports}
                    disabled={pendingReports.length === 0 || batchProgress?.active || loading}
                    style={{
                        padding: '10px 14px',
                        background: pendingReports.length === 0 || batchProgress?.active ? '#6c757d' : '#198754',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: pendingReports.length === 0 || batchProgress?.active ? 'not-allowed' : 'pointer',
                        fontWeight: 600
                    }}
                >
                    {batchProgress?.active ? 'Loading pending reports...' : `Load ${pendingReports.length} pending report${pendingReports.length === 1 ? '' : 's'}`}
                </button>
                {batchProgress && (
                    <span style={{ fontSize: '13px' }}>
                        {batchProgress.active ? `Processing ${batchProgress.current}` : `${batchProgress.completed} report${batchProgress.completed === 1 ? '' : 's'} processed`}
                        {batchProgress.failed.length > 0 ? `; ${batchProgress.failed.length} failed` : ''}
                    </span>
                )}
            </div>

            {batchProgress && (
                <div style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '5px' }}>
                        <span>{batchProgress.completed} of {batchProgress.total} reports</span>
                        <strong>{batchPercent}%</strong>
                    </div>
                    <div role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={batchPercent} style={{ height: '10px', background: '#e9ecef', borderRadius: '5px', overflow: 'hidden' }}>
                        <div style={{ width: `${batchPercent}%`, height: '100%', background: batchProgress.failed.length > 0 ? '#dc3545' : '#198754', transition: 'width 250ms ease' }} />
                    </div>
                </div>
            )}

            {loading ? (
                <div className="p-d-flex p-jc-center p-ai-center" style={{ minHeight: '200px' }}>
                    <p>Loading report files...</p>
                </div>
            ) : filteredReports.length === 0 ? (
                <div className="w3-panel w3-light-gray" style={{ padding: '16px' }}>
                    No report files found for the selected filters.
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                    {filteredReports.map((report) => {
                        const result = trackingResults[report.name];
                        return (
                            <div key={report.name} className="w3-card" style={{ padding: '16px', borderRadius: '10px', background: '#fff' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', alignItems: 'center' }}>
                                    <h4 style={{ margin: 0, wordBreak: 'break-word' }}>{report.name}</h4>
                                    <span className="w3-tag" style={{ background: report.processed ? '#dff5e1' : '#fff4d6', color: report.processed ? '#1a7f2e' : '#9c6b00', fontWeight: 700, padding: '4px 8px', borderRadius: '999px' }}>
                                        {report.status}
                                    </span>
                                </div>

                                <div style={{ marginTop: '12px', fontSize: '14px', color: '#4a4a4a' }}>
                                    <div>Rows: <strong>{report.row_count}</strong></div>
                                    <div>Loaded in DB: <strong>{report.processed ? 'Yes' : 'No'}</strong></div>
                                    <div>Last modified: <strong>{report.modified_date || 'N/A'}</strong></div>
                                </div>

                                <div style={{ display: 'grid', gap: '8px', marginTop: '16px' }}>
                                    <button type="button" onClick={() => handleTrackingCheck(report)} disabled={checkingFile === report.name} style={{ width: '100%', padding: '10px 12px', background: '#0d6efd', color: '#fff', border: 'none', borderRadius: '6px', cursor: checkingFile === report.name ? 'not-allowed' : 'pointer', opacity: checkingFile === report.name ? 0.7 : 1, fontWeight: 600 }}>
                                        {checkingFile === report.name ? 'Checking tracking codes...' : 'Check tracking codes'}
                                    </button>
                                    <button type="button" onClick={() => handleLoadReport(report)} disabled={loadingFile === report.name || report.processed || batchProgress?.active} style={{ width: '100%', padding: '10px 12px', background: report.processed ? '#6c757d' : '#198754', color: '#fff', border: 'none', borderRadius: '6px', cursor: loadingFile === report.name || report.processed || batchProgress?.active ? 'not-allowed' : 'pointer', opacity: loadingFile === report.name ? 0.7 : 1, fontWeight: 600 }}>
                                        {loadingFile === report.name ? 'Loading file...' : report.processed ? 'Already loaded' : 'Load file into DB'}
                                    </button>
                                </div>

                                {result && (
                                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #efefef' }}>
                                        {result.error ? (
                                            <div style={{ color: '#b42318', fontSize: '13px' }}>{result.error}</div>
                                        ) : (
                                            <>
                                                <div style={{ fontSize: '13px', marginBottom: '8px' }}>Present: <strong>{result.present_count ?? 0}</strong> | Missing: <strong>{result.missing_count ?? 0}</strong></div>
                                                <div style={{ maxHeight: '220px', overflowY: 'auto', fontSize: '12px' }}>
                                                    {result.tracking_codes && result.tracking_codes.length > 0 ? result.tracking_codes.map((item) => (
                                                        <div key={item.tracking_code} style={{ padding: '6px 0', borderBottom: '1px solid #f2f2f2' }}>
                                                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                                                                <span style={{ wordBreak: 'break-all' }}>{item.tracking_code}</span>
                                                                <span style={{ color: item.present_in_db ? '#198754' : '#b42318', fontWeight: 700 }}>{item.present_in_db ? 'Found' : 'Missing'}</span>
                                                            </div>
                                                            {item.reason && <div style={{ color: '#666', marginTop: '4px' }}>{item.reason}</div>}
                                                        </div>
                                                    )) : <div style={{ color: '#666' }}>No tracking codes found in this file.</div>}
                                                </div>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default CsvLoaderReportsTab;
