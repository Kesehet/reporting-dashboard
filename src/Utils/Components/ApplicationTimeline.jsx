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

function countComments(items = []) {
    return items.reduce((count, item) => count + 1 + countComments(item.replies), 0);
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

    return <section className="application-timeline" aria-label={'Application timeline for ' + trackingCode}>
        <h3>Application Timeline</h3>
        {error ? <div role="alert">{error} <button type="button" onClick={() => setAttempt(n => n + 1)}>Retry</button></div>
            : !data ? <p role="status">Loading application timeline...</p>
            : <>
                {data.job_reference && <p className="application-timeline__meta">Job: {data.job_reference} | {data.status || 'Status unavailable'}</p>}
                {!data.steps.length && <p>No workflow steps were returned for this tracking code. History may be unavailable or outside source retention.</p>}
                <ol className="application-timeline__steps">
                    {[...data.steps].reverse().map(step => {
                        const total = countComments(step.comments) + step.tasks.reduce((n, t) => n + countComments(t.comments), 0);
                        return <li key={step.sequence} className="application-timeline__step">
                            <details open={total > 0 ? true : undefined}>
                                <summary>
                                    <span className={'application-timeline__number' + (step.status?.toLowerCase() === 'completed' ? ' is-complete' : '')}>STEP {step.sequence}</span>
                                    <span className="application-timeline__heading"><strong>{step.name || 'Unnamed step'}</strong>
                                        <small>{[dateLabel(step.time), step.status, step.result || 'No result'].filter(Boolean).join(' | ')}</small></span>
                                    <small className="application-timeline__counts">{step.tasks.length} tasks | {total} comments</small>
                                </summary>
                                <Tasks tasks={step.tasks} />
                                <Comments items={step.comments} />
                            </details>
                        </li>;
                    })}
                </ol>
                {!!data.unassigned_tasks.length && <><h4>Transactions not linked to a step</h4><Tasks tasks={data.unassigned_tasks} /></>}
                {!!data.unassigned_comments.length && <><h4>Application-level / unassigned comments</h4><Comments items={data.unassigned_comments} /></>}
            </>}
    </section>;
}
