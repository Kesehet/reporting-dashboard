import apiBaseUrl from './apiBaseUrl';
class ChartDataService {
    constructor(name, extraParams = {}) {
        let base = apiBaseUrl();
        this.url = base + "/charts/" + name;
        this.extraParams = extraParams;
    }

    async getChart() {
        try {
            const startDate = localStorage.getItem("start_date");
            const endDate = localStorage.getItem("end_date");
            const CorBFilter = localStorage.getItem("CorBFilter") || "%25";
            
            if(!this.extraParams.start_date) {this.extraParams.start_date = startDate;}
            if(!this.extraParams.end_date) {this.extraParams.end_date = endDate;}
            this.extraParams.eCATrackingCode = CorBFilter;
            this.extraParams.eCATrackingCode = this.extraParams.eCATrackingCode === "All" ? "%25" : this.extraParams.eCATrackingCode;

            // if this.extraParams.requestMethod is set to GET, use GET method else use POST
            if(this.extraParams.requestMethod && this.extraParams.requestMethod.toUpperCase() === "POST"){
                let extraPostParams = Object.entries(this.extraParams).reduce((obj, [key, value]) => {
                    obj[key] = value;
                    return obj;
                }, {});
                
                const fullUrl = `${this.url}`;

                const response = await fetch(fullUrl, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...(localStorage.getItem('token') ? { Authorization: localStorage.getItem('token') } : {}),
                    },
                    method: 'POST',
                    body: JSON.stringify(extraPostParams)
                });
                let data = await response.json();
                return data;
                
            }            
            else{
                let extraGetParams = Object.entries(this.extraParams).map(([key, value]) => `${key}=${value}`).join('&');
                const fullUrl = `${this.url}?${extraGetParams}`;
                const response = await fetch(fullUrl, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...(localStorage.getItem('token') ? { Authorization: localStorage.getItem('token') } : {}),
                    },
                    method: 'GET',
                });
                let data = await response.json();
                return data;
            }
            
            
        } catch (error) {
            console.error(error);
            return "Unknown Error Occurred.";
        }
    }
}

export default ChartDataService;
