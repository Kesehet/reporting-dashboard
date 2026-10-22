import apiBaseUrl from './apiBaseUrl';
import sessionHeaders from './sessionHeaders';
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

            // Keep API credentials out of query strings and chart filter payloads.
            const requestParams = Object.fromEntries(
                Object.entries(this.extraParams).filter(([key]) => key.toLowerCase() !== 'api_key')
            );

            // if this.extraParams.requestMethod is set to GET, use GET method else use POST
            if(this.extraParams.requestMethod && this.extraParams.requestMethod.toUpperCase() === "POST"){
                let extraPostParams = Object.entries(requestParams).reduce((obj, [key, value]) => {
                    obj[key] = value;
                    return obj;
                }, {});
                
                const fullUrl = `${this.url}`;

                const response = await fetch(fullUrl, {
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        ...sessionHeaders(),
                    },
                    method: 'POST',
                    body: JSON.stringify(extraPostParams)
                });
                let data = await response.json();
                return data;
                
            }            
            else{
                let extraGetParams = Object.entries(requestParams).map(([key, value]) => `${key}=${value}`).join('&');
                const fullUrl = `${this.url}?${extraGetParams}`;
                const response = await fetch(fullUrl, {
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        ...sessionHeaders(),
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
