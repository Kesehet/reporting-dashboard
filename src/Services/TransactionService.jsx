import { isArray } from 'chart.js/helpers';
import XMLParser from 'react-xml-parser';

class TransactionService {
  constructor(onload = null, startDate = "2024-04-09", endDate = "2024-04-11", requestedTransactions = []) {
    this.onload = onload;
    let base = process.env.NODE_ENV === 'production' ? (window.location.href + "api") : "http://localhost:5000";

    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      txns: Array.isArray(requestedTransactions)
        ? requestedTransactions.join(',')
        : (requestedTransactions || '')
    });

    this.url = `${base}/?${params.toString()}`;
  }

  async fetchData() {



    try {
      const response = await fetch(this.url);
      if (response.status !== 200) {
        throw new Error(`Failed to fetch data: Error code ${response.status}`);

      }
      this.json = await response.json();

      this.json.forEach(element => {
        element.AppStartDate = this.timeNow(element.AppStartDate);
        element.AppSubmitDate = this.timeNow(element.AppSubmitDate);
        element.AppUpdateDate = this.timeNow(element.AppUpdateDate);

        // if(element.coApplicantsNames.length > 0){
        //   let count = element.coApplicantsNames.length;
        //   for(let i = 0 ; i< count; i++){
        //     element["coApplicantName_"+(i+1)] = element.coApplicantsNames[i];
        //     element["coApplicantSSN_"+(i+1)] = element.coApplicantsSSNs[i];
        //   }          
        // }

      });



      if (this.onload) {
        this.onload(this.json);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  }


  timeNow(isoDate) {
    const date = new Date(isoDate);

    const etOffset = -2 * 60;

    date.setMinutes(date.getMinutes() + etOffset);

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    let hours = parseInt(String(date.getHours()).padStart(2, "0"));
    let amPm;
    if (hours > 12) {
      hours = hours - 12;
      hours = String(hours).padStart(2, "0");
      amPm = 'PM';
    } else {
      amPm = 'AM';
    }
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    return `${month}/${day}/${year} ${hours}:${minutes}:${seconds} ${amPm}`;
  }

}

export default TransactionService;