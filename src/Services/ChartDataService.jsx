class ChartDataService {
    constructor(name, extraParams = {}) {
        let base = process.env.NODE_ENV === 'production' ? (window.location.href + "api") : "http://localhost:5000";
        this.url = base + "/charts/" + name;
        this.extraParams = extraParams;
    }

    async getChart() {
        if (!localStorage.getItem('token')) {
            // console.log("Token not set in local storage.");
        }
        if (!localStorage.getItem('start_date') || !localStorage.getItem('end_date')) {
            // console.log("Start date or end date not set in local storage.");
        }
        try {
            const startDate = localStorage.getItem("start_date");
            const endDate = localStorage.getItem("end_date");
            const CorBFilter = localStorage.getItem("CorBFilter") || "%25";
            
            if(!this.extraParams.start_date) {this.extraParams.start_date = startDate;}
            if(!this.extraParams.end_date) {this.extraParams.end_date = endDate;}
            this.extraParams.eCATrackingCode = CorBFilter;
            this.extraParams.eCATrackingCode = this.extraParams.eCATrackingCode === "All" ? "%25" : this.extraParams.eCATrackingCode;
            

            let extraGetParams = Object.entries(this.extraParams).map(([key, value]) => `${key}=${value}`).join('&');
            
            const fullUrl = `${this.url}?${extraGetParams}`;

            const response = await fetch(fullUrl, {
                headers: {
                    'Authorization': localStorage.getItem('token'),
                }
            });
            let data = await response.json();

            return data;
        } catch (error) {
            console.error(error);
            return "Unknown Error Occurred.";
        }
    }
}

export default ChartDataService;
