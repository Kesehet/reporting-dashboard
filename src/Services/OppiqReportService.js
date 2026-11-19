import apiBaseUrl from './apiBaseUrl';
import sessionHeaders from './sessionHeaders';

async function requestReport(path, options = {}) {
    const response = await fetch(apiBaseUrl() + path, {
        credentials: 'same-origin',
        headers: { ...sessionHeaders() },
        ...options,
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.error || 'OPPIQ report request failed.');
    }

    return response;
}

export async function getOppiqReport(page = 1, pageSize = 50, signal) {
    const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
    });
    const response = await requestReport('/oppiq-report?' + params, { signal });
    return response.json();
}

export async function downloadOppiqReport() {
    const response = await requestReport('/oppiq-report/export');
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : 'OPPIQ_Report.csv';
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    try {
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
    } finally {
        link.remove();
        URL.revokeObjectURL(url);
    }
}
