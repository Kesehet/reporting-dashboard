import React, { useEffect, useState } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import sessionHeaders from '../Services/sessionHeaders';

const endpoint = process.env.REACT_APP_API_SERVER_BASE_URL?.replace(/\/$/, '') ||
    (process.env.NODE_ENV === 'production'
        ? new URL('api', new URL('.', window.location.href)).href
        : 'http://localhost:5000');

function localDate(date) {
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
}

function duration(row) {
    if (row.duration_seconds == null) return 'Unavailable';
    const minutes = Math.floor(row.duration_seconds / 60);
    const elapsed = minutes === 0 ? '<1 min' : [
        Math.floor(minutes / 60) ? `${Math.floor(minutes / 60)} hr` : '',
        `${minutes % 60} min`,
    ].filter(Boolean).join(' ');
    return row.in_review ? `${elapsed} (ongoing)` : elapsed;
}

export default function ManualReviewReport() {
    const [end, setEnd] = useState(() => localDate(new Date()));
    const [start, setStart] = useState(() => {
        const date = new Date();
        date.setDate(date.getDate() - 6);
        return localDate(date);
    });
    const [query, setQuery] = useState(null);
    const [rows, setRows] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [type, setType] = useState('');
    const [channel, setChannel] = useState('');

    useEffect(() => {
        if (!query) return undefined;
        const controller = new AbortController();
        const params = new URLSearchParams({ start_date: query.start, end_date: query.end });
        async function load() {
            try {
                const response = await fetch(`${endpoint}/reports/manual-review?${params}`, {
                    headers: sessionHeaders(),
                    cache: 'no-store',
                    signal: controller.signal,
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.error || 'Unable to load Manual Review.');
                if (!controller.signal.aborted) setRows(result.rows);
            } catch (failure) {
                if (!controller.signal.aborted) setError(failure.message);
            } finally {
                if (!controller.signal.aborted) setLoading(false);
            }
        }
        load();
        return () => controller.abort();
    }, [query]);

    const filtered = (rows || []).filter(row =>
        (!type || row.application_type === type) && (!channel || row.channel === channel));
    const completed = filtered.filter(row => row.completed).length;

    function run(event) {
        event.preventDefault();
        setRows(null);
        setError('');
        setLoading(true);
        setQuery({ start, end });
    }

    return (
        <section className="w3-container" aria-labelledby="manual-review-title">
            <h1 id="manual-review-title">Manual Review Report</h1>
            <p>Choose up to 31 days by application creation date. Results depend on Journey Manager retention.</p>
            <form onSubmit={run} className="flex flex-wrap align-items-end gap-3">
                <label>Created from <input type="date" required value={start} max={end}
                    onChange={event => setStart(event.target.value)} /></label>
                <label>Created through <input type="date" required value={end} min={start}
                    onChange={event => setEnd(event.target.value)} /></label>
                <button type="submit" className="p-button" disabled={loading}>Run report</button>
            </form>
            {loading && <p role="status">Loading Manual Review history…</p>}
            {error && <p role="alert">{error}</p>}
            {rows && <>
                <p>Applications created {query.start} through {query.end}</p>
                <div className="flex flex-wrap gap-3">
                    <label>Application type <select value={type} onChange={event => setType(event.target.value)}>
                        <option value="">All</option><option>Business</option><option>Consumer</option>
                    </select></label>
                    <label>Channel <select value={channel} onChange={event => setChannel(event.target.value)}>
                        <option value="">All</option><option>In-Branch</option><option>Online</option><option>Unknown</option>
                    </select></label>
                </div>
                <dl className="flex flex-wrap gap-4" aria-live="polite">
                    <div><dt>Sent to Manual Review</dt><dd>{filtered.length}</dd></div>
                    <div><dt>Completed after Manual Review</dt><dd>{completed}</dd></div>
                    <div><dt>Not completed after Manual Review</dt><dd>{filtered.length - completed}</dd></div>
                </dl>
                <DataTable value={filtered} dataKey="application_id" paginator rows={25} scrollable
                    emptyMessage="No applications match these filters.">
                    <Column field="application_id" header="Application ID" sortable />
                    <Column field="application_type" header="Application type" sortable />
                    <Column field="channel" header="Channel" sortable />
                    <Column field="outcome" header="Outcome" body={row => row.outcome || 'Unavailable'} />
                    <Column field="reviewer" header="Reviewer" body={row => row.reviewer || 'Unavailable'} />
                    <Column field="duration_seconds" header="Time in Manual Review" body={duration} sortable />
                    <Column field="completed" header="Application completion" sortable
                        body={row => row.completed ? 'Completed' : 'Not completed'} />
                    <Column header="Manual Review notes" style={{ minWidth: '14rem' }}
                        body={row => row.notes.length ? <ul>{row.notes.map(note =>
                            <li key={note} style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{note}</li>
                        )}</ul> : '—'} />
                </DataTable>
            </>}
        </section>
    );
}
