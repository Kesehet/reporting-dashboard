import React, { useEffect, useState } from 'react';
import apiBaseUrl from '../../Services/apiBaseUrl';
import sessionHeaders from '../../Services/sessionHeaders';

function dateLabel(value) {
    if (!value) return '';
    if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(value)) return value;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-US', {
        dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/New_York'
    }).format(date) + ' ET';
}

function Comments({ items = [] }) {
    return items.map((comment, index) => (
        <div className="application-timeline__comment" key={index}>
            <small>{[comment.author, dateLabel(comment.time)].filter(Boolean).join(' | ')}</small>
            {comment.header && <strong>{comment.header}</strong>}
            <div>{comment.message}</div>
            <Comments items={comment.replies} />
        </div>
    ));
}

function Tasks({ tasks = [] }) {
    return tasks.map((task, index) => (
        <div className="application-timeline__task" key={task.tracking_code || index}>
            {task.tracking_code && <strong className="application-timeline__code">{task.tracking_code}</strong>}
            <strong>{[task.name, task.status].filter(Boolean).join(' - ')}</strong>
            <small>{[task.group, task.user, dateLabel(task.created),
                task.updated && 'Updated ' + dateLabel(task.updated)].filter(Boolean).join(' | ')}</small>
            <Comments items={task.comments} />
        </div>
    ));
}

function timeValue(value) {
    if (!value || !/(Z|[+-]\d{2}:?\d{2})$/i.test(value)) return -Infinity;
    const parsed = Date.parse(value);
    return Number.isFinite(parsed) ? parsed : -Infinity;
}

function historyEntries(data) {
    // Compatible with the previous serve.exe while deployments are being updated.
    const steps = data.steps || [];
    const transactions = data.transactions || [
        ...steps.flatMap(step => step.tasks || []), ...(data.unassigned_tasks || []),
    ];
    const notes = data.application_comments || [
        ...steps.flatMap(step => step.comments || []), ...(data.unassigned_comments || []),
    ];
    return [
        ...transactions.map(task => ({ task, time: task.created || task.updated })),
        ...notes.map(note => ({ note, time: note.time })),
    ].sort((a, b) => timeValue(b.time) - timeValue(a.time));
}

export default function ApplicationTimeline({ trackingCode }) {
    const [data, setData] = useState(null);
    const [error, setError] = useState('');
    const [attempt, setAttempt] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        setError('');
        setData(null);
        const params = new URLSearchParams({ tracking_code: trackingCode });
        fetch(apiBaseUrl() + '/reports/transaction-timeline?' + params, {
            credentials: 'same-origin', headers: sessionHeaders(), signal: controller.signal,
            cache: 'no-store',
        }).then(async response => {
            const body = await response.json();
            if (!response.ok) throw new Error(body.error || 'Timeline request failed.');
            return body;
        }).then(body => {
            if (!controller.signal.aborted) setData(body);
        }).catch(err => {
            if (!controller.signal.aborted) setError(err.message || 'Timeline request failed.');
        });
        return () => controller.abort();
    }, [trackingCode, attempt]);

    const entries = data ? historyEntries(data) : [];

    return <section className="application-timeline" aria-label={'Application timeline for ' + trackingCode}>
        <h3>Application Timeline</h3>
        {error ? <div role="alert">{error} <button type="button" onClick={() => setAttempt(n => n + 1)}>Retry</button></div>
            : !data ? <p role="status">Loading application timeline...</p>
            : <>
                {data.job_reference && <p className="application-timeline__meta">Job: {data.job_reference} | {data.status || 'Status unavailable'}</p>}
                {!entries.length && <p>No related transactions or comments were returned.</p>}
                <div className="application-timeline__history">
                    {entries.map((entry, index) => entry.task
                        ? <Tasks key={entry.task.tracking_code || index} tasks={[entry.task]} />
                        : <div className="application-timeline__task" key={'note-' + index}>
                            <strong>Application comment</strong>
                            <Comments items={[entry.note]} />
                        </div>
                    )}
                </div>
            </>}
    </section>;
}
