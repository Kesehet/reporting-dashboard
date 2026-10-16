class CsvReportService {
    constructor() {
        this.baseUrl = process.env.NODE_ENV === 'production' ? (window.location.href + 'api') : 'http://localhost:5000';
    }

    async getReportStatus(filters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params.append(key, value);
            }
        });

        const response = await fetch(`${this.baseUrl}/csv_report_status?${params.toString()}`, {
            headers: {
                'Content-Type': 'application/json',
            },
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error('Unable to load report status.');
        }

        return response.json();
    }

    async checkTrackingCodes(fileName) {
        const response = await fetch(`${this.baseUrl}/csv_report_tracking_status`, {
            headers: {
                'Content-Type': 'application/json',
            },
            method: 'POST',
            body: JSON.stringify({ file_name: fileName }),
        });

        if (!response.ok) {
            throw new Error('Unable to verify tracking codes.');
        }

        return response.json();
    }

    async loadReportFile(fileName) {
        const response = await fetch(`${this.baseUrl}/csv_report_load_file`, {
            headers: {
                'Content-Type': 'application/json',
            },
            method: 'POST',
            body: JSON.stringify({ file_name: fileName }),
        });

        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.message || 'Unable to load file into the database.');
        }

        return payload;
    }
}

export default CsvReportService;
