class MetricsDataService {
    constructor(extraParams = {}) {
        let base = process.env.NODE_ENV === 'production' ? (window.location.href + "api") : "http://localhost:5000";
        this.url = base + "/show_metrics";
        this.extraParams = extraParams;
    }

    async getMetrics() {
        try {
            const startDate = localStorage.getItem("start_date");
            const endDate = localStorage.getItem("end_date");
            const CorBFilter = localStorage.getItem("CorBFilter") || "%25";

            this.extraParams.start_date = startDate;
            this.extraParams.end_date = endDate;
            this.extraParams.eCATrackingCode = CorBFilter === "All" ? "%25" : CorBFilter;

            let extraGetParams = Object.entries(this.extraParams)
                .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
                .join('&');

            const fullUrl = `${this.url}?${extraGetParams}`;

            const response = await fetch(fullUrl, {
                headers: {
                    'Authorization': localStorage.getItem('token'),
                }
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error(error);
            return "Unknown Error Occurred.";
        }
    }
}

export default MetricsDataService;
