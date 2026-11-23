import React, { useEffect, useState } from 'react';
import apiBaseUrl from '../Services/apiBaseUrl';
import sessionHeaders from '../Services/sessionHeaders';

const tasks = {
    'dds-amount': 'DDS Amount',
    'jm-extract': 'JM Extract Table',
};

const statuses = {
    running: 'Running',
    completed: 'Completed',
    completed_with_errors: 'Completed with errors',
    failed: 'Failed',
    interrupted: 'Interrupted',
};

async function request(path, method = 'GET', signal) {
    const response = await fetch(apiBaseUrl() + '/post-processing' + path, {
        method, signal, headers: sessionHeaders(), cache: 'no-store',
    });
    if (response.status === 401) throw new Error('Sign in again to access post-processing.');
    if (response.status === 409) throw new Error('A manual post-processing task is already running.');
    if (!response.ok) throw new Error('The post-processing service could not complete the request.');
    return response.json();
}

export default function PostProcessingTab() {
    const [runs, setRuns] = useState(null);
    const [loadingError, setLoadingError] = useState('');
    const [startError, setStartError] = useState('');
    const [starting, setStarting] = useState(false);
    const [refresh, setRefresh] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        let nextPoll;
        async function load() {
            try {
                const result = await request('/runs', 'GET', controller.signal);
                if (!controller.signal.aborted) {
                    setRuns(result.runs);
                    setLoadingError('');
                }
            } catch (error) {
                if (!controller.signal.aborted) setLoadingError(error.message);
            } finally {
                if (!controller.signal.aborted) nextPoll = setTimeout(load, 3000);
            }
        }
        load();
        return () => {
            controller.abort();
            clearTimeout(nextPoll);
        };
    }, [refresh]);

    async function start(task) {
        setStarting(true);
        setStartError('');
        try {
            await request('/tasks/' + task + '/runs', 'POST');
            const result = await request('/runs');
            setRuns(result.runs);
        } catch (error) {
            setStartError(error.message);
        } finally {
            setStarting(false);
            setRefresh(value => value + 1);
        }
    }

    const busy = starting || runs?.some(run => run.status === 'running');
    return (
        <section className="w3-container">
            <h2>Post Processing</h2>
            <div className="flex flex-wrap gap-2">
                {Object.entries(tasks).map(([task, label]) => (
                    <button key={task} type="button" className="p-button p-component"
                        disabled={!runs || Boolean(loadingError) || busy} onClick={() => start(task)}>
                        Run {label}
                    </button>
                ))}
            </div>
            <p>DDS Amount uses the existing DDS eligibility rules. JM Extract Table fills missing extracts within the Journey Manager retention window. These jobs use their own scope.</p>
            {loadingError && <p role="alert">{loadingError}</p>}
            {startError && <p role="alert">{startError}</p>}
            <h3>Recent runs</h3>
            {!runs && !loadingError && <p role="status">Loading run history…</p>}
            {runs?.length === 0 && <p>No manual runs yet.</p>}
            {runs?.length > 0 && (
                <div className="w3-responsive">
                    <table className="w3-table w3-bordered">
                        <thead><tr><th>Run</th><th>Task</th><th>Status</th><th>Started</th><th>Finished</th><th>Errors</th></tr></thead>
                        <tbody>
                            {runs.map(run => (
                                <tr key={run.id}>
                                    <td>{run.id}</td><td>{tasks[run.task]}</td><td>{statuses[run.status]}</td>
                                    <td>{new Date(run.started_at).toLocaleString()}</td>
                                    <td>{run.finished_at ? new Date(run.finished_at).toLocaleString() : '—'}</td>
                                    <td>{Object.keys(run.errors).length ? (
                                        <ul>{Object.entries(run.errors).map(([message, count]) => (
                                            <li key={message}>{message} ({count})</li>
                                        ))}</ul>
                                    ) : '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </section>
    );
}
