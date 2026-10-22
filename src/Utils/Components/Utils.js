import { Column } from "primereact/column";
import { ColumnGroup } from "primereact/columngroup";
import { Row } from "primereact/row";
import React from 'react';


export const FNB_PIE_PRIMARY_COLOURS = ['#bd2c1e','#19437d','#9d9d9d','#8a0c00','#002048','#f04d3d','#3366b3'];
export const FNB_PIE_SECONDARY_COLOURS = ['#bd2c1e','#19437d','#9d9d9d','#8a0c00','#002048','#f04d3d','#3366b3'];
export const BASIC_TRANSACTION_TYPES = ["Loan Only Apps", "Deposit Only Apps", "Mixed Apps(Loan + Deposit)", "Multi-Product Apps"];

/* We need to pass Data in the format 
    {
        labels : ["a", "b", "c"]
        list : [1,2,5]
    }

*/

export function generateBarChartData(chartData, name = "", barColors = false) {
    if (!chartData || !chartData.labels || !chartData.list) {
        console.error("Incorrect data structure for the bar chart.", chartData, name);
        return {};
    }
    let barLabels = chartData.labels ?? chartData.data.labels;
    let barDataSets = chartData.list ?? chartData.data.list;

    barDataSets = barDataSets.map(value => parseFloatOrInt(value));

    // Generate dynamic colors if the number of data types exceeds predefined colors
    const generateDynamicColors = (count) => {
        let colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(getRandomColor());
        }
        return colors;
    };

    const backgroundColors = [];
    const borderColors = [];
    if (barColors) {
        for (let i = 0; i < barLabels.length; i++) {
            backgroundColors.push(FNB_PIE_PRIMARY_COLOURS[i % FNB_PIE_PRIMARY_COLOURS.length]);
            borderColors.push(FNB_PIE_SECONDARY_COLOURS[i % FNB_PIE_SECONDARY_COLOURS.length]);
        }
    } else {
        backgroundColors = barLabels.length > FNB_PIE_PRIMARY_COLOURS.length
            ? generateDynamicColors(barLabels.length)
            : FNB_PIE_PRIMARY_COLOURS;

        borderColors = barLabels.length > FNB_PIE_SECONDARY_COLOURS.length
            ? generateDynamicColors(barLabels.length)
            : FNB_PIE_SECONDARY_COLOURS;
    }

    return {
        labels: barLabels,
        datasets: [
            {
                label: name,
                data: barDataSets,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1,
            },
        ],
    };
}

export function generateStackedBarChartData(chartData, name, barColors = false) {
    if (!chartData || !chartData.labels || !chartData.list) {
        console.error("Incorrect data structure for the stacked bar chart.", name);
        return {};
    }

    const barLabels = chartData.labels;
    const barDataSets = chartData.list;

    const generateDynamicColors = (count) => {
        let colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(getRandomColor());
        }
        return colors;
    };

    const datasets = barDataSets.map((dataSet, index) => {
        dataSet.data = checkListForParseFloatOrInt(dataSet.data);
        const backgroundColor = barColors
            ? FNB_PIE_PRIMARY_COLOURS[index % FNB_PIE_PRIMARY_COLOURS.length]
            : (barDataSets.length > FNB_PIE_PRIMARY_COLOURS.length
                ? generateDynamicColors(barDataSets.length)[index]
                : FNB_PIE_PRIMARY_COLOURS[index]);

        const borderColor = barColors
            ? FNB_PIE_SECONDARY_COLOURS[index % FNB_PIE_SECONDARY_COLOURS.length]
            : (barDataSets.length > FNB_PIE_SECONDARY_COLOURS.length
                ? generateDynamicColors(barDataSets.length)[index]
                : FNB_PIE_SECONDARY_COLOURS[index]);

        return {
            label: dataSet.name || `Series ${index + 1}`,
            data: dataSet.data,
            backgroundColor,
            borderColor,
            borderWidth: 1,
        };
    });

    return {
        labels: barLabels,
        datasets: datasets,
    };
}





export function generateBarWithLineChartData(chartData, name, barColors = false) {
    if (!chartData || !chartData.labels || !chartData.list || chartData.list.length < 2) {
        console.error("Incorrect data structure for bar + line chart.", name);
        return {};
    }

    const barLabels = chartData.labels;
    const barDataSets = chartData.list;

    const generateDynamicColors = (count) => {
        let colors = [];
        for (let i = 0; i < count; i++) {
            colors.push(getRandomColor());
        }
        return colors;
    };

    const datasets = barDataSets
        .map((dataSet, index) => {
            const isLine = dataSet.type === 'line';
            dataSet.data = checkListForParseFloatOrInt(dataSet.data);

            if (!isLine && !Array.isArray(dataSet.data)) return null;

            const backgroundColor = isLine ? undefined : (
                barColors
                    ? FNB_PIE_PRIMARY_COLOURS[index % FNB_PIE_PRIMARY_COLOURS.length]
                    : (barDataSets.length > FNB_PIE_PRIMARY_COLOURS.length
                        ? generateDynamicColors(barDataSets.length)[index]
                        : FNB_PIE_PRIMARY_COLOURS[index])
            );

            const borderColor = barColors
                ? FNB_PIE_SECONDARY_COLOURS[index % FNB_PIE_SECONDARY_COLOURS.length]
                : (barDataSets.length > FNB_PIE_SECONDARY_COLOURS.length
                    ? generateDynamicColors(barDataSets.length)[index]
                    : FNB_PIE_SECONDARY_COLOURS[index]);

            return {
                type: isLine ? 'line' : 'bar',
                label: dataSet.name || `Series ${index + 1}`,
                data: dataSet.data,
                backgroundColor,
                borderColor,
                borderWidth: isLine ? 2 : 1,
                fill: false,
                tension: isLine ? 0.4 : undefined,
                order: isLine ? 1 : 2,
                yAxisID: isLine ? 'y1' : 'y'
            };
        })
        .filter(Boolean); // Remove nulls

    return {
        labels: barLabels,
        datasets: datasets,
    };
}






export function generatePieChartData(chartData, name = "", pieColors = false) {
    if (!chartData || !chartData.labels || !chartData.list) {
        console.error("Incorrect data structure for the pie chart.", chartData, name);
        return {};
    }
    let pieLabels = chartData.labels ?? chartData.data.labels;
    let pieDataSets = chartData.list ?? chartData.data.list;
    pieDataSets = pieDataSets.map(value => parseFloatOrInt(value));

    let backgroundColors = pieLabels.map(label => getColorforTransactionType(label));
    let hoverBackgroundColors = pieLabels.map(label => getColorforTransactionType(label));

    return {
        labels: pieLabels,
        datasets: [
            {
                data: pieDataSets,
                backgroundColor: backgroundColors,
                hoverBackgroundColor: hoverBackgroundColors,
            },
        ],
    };
}

export function generateLineChartData (data) {
    data = data && typeof data === 'object' ? dataParser(data) : {};
    const pointers = Array.isArray(data.labels) ? data.labels : [];
    const datasetMap = data.datasetMap && typeof data.datasetMap === 'object' && !Array.isArray(data.datasetMap)
        ? data.datasetMap : {};
    let labels = Object.keys(datasetMap);
    let values = Object.values(datasetMap);
    var dataset = [];
    for(let i=0; i < values.length; i++){
        dataset.push({
            "label": labels[i],
            "data": Array.isArray(values[i]) ? checkListForParseFloatOrInt(values[i]) : [],
            "borderColor": getColorforTransactionType(labels[i]),
            "backgroundColor": getColorforTransactionType(labels[i]),
            "fill": false
        });
    }
    return {
        "labels": pointers,
        "datasets": dataset
    }
};


// Function to return float from string or int with or without commas, and keep it as int if it has no decimal part
export function parseFloatOrInt(value) {
    if (typeof value === 'string') {
        value = value.replace(/[^\d.-]/g, ''); // Remove commas
    }
    return parseFloat(value);
}

export function checkListForParseFloatOrInt(list){
    return list.map(item => parseFloatOrInt(item));
}

 // Get Quarter based on timestamp
 export function getQuarter (date){
    const newDate = new Date(date);
    const month = newDate.getMonth();
    const year = newDate.getFullYear();
    
    if (month >= 0 && month <=2){
        return { quarter: 'Q1', year};
    }else if ( month >= 3 && month <= 5 )
    {
        return { quarter: 'Q2', year};
    }else if ( month >= 6 && month <= 8 )
    {
        return { quarter: 'Q3' , year};
    }else if ( month >= 9 && month <= 11 )
    {
        return { quarter: 'Q4' , year};
    }

}

export function monthListByQuarter(q){
    var monthlyList = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    for(var i = 0; i<4; i++){
        if(q === "Q"+(i+1)){
            let mul = (monthlyList.length/4);
            return monthlyList.slice(mul*i , mul*(i+1));
        }
    }
}

export function getListOfAvailableMonthsFromListOfQuarters(inputQuarters){
    if(!inputQuarters) return [];
    var availableQuarters = null;
    if(inputQuarters instanceof Array){
        
        availableQuarters = inputQuarters;
    } else{
        availableQuarters = Object.keys(inputQuarters);
    }


     
    var ret = {}
    for(var i = 0 ; i < availableQuarters.length; i++){
        let qnow = availableQuarters[i];
        
        let q = qnow.split("-")[0];
        let y = qnow.split("-")[1];
        let avM = monthListByQuarter(q);
        for(var j = 0 ; j < avM?.length; j++){
            avM[j] = avM[j]+y;
            if(!ret[avM[j]]) {ret[avM[j]] = null;}
        }
    }
    return Object.keys(ret);
}


export function getIsStarted(transactionObject){
    return transactionObject.AppStartDate !== null;
}

export function getIsSubmitted(transactionObject){
    return transactionObject.AppStartDate !== null;
}

export function getTransactionCategory(transactionObject){
    let category = "";
                if (transactionObject.NumDepositProducts >=1 && transactionObject.NumLendingProducts >=1){
                   category = "mixed" 
                }
                else if (transactionObject.NumLendingProducts ==1 && transactionObject.NumDepositProducts === 0){
                    category = "loanOnly"
                }
                else if (transactionObject.NumDepositProducts ==1 && transactionObject.NumLendingProducts === 0){
                    category = "depositOnly"
                }       
                else if ((transactionObject.NumDepositProducts >1 && transactionObject.NumLendingProducts ==0) || (transactionObject.NumDepositProducts ==0 && transactionObject.NumLendingProducts >1)) { 
                    category = "multiProduct"
                };

                return category
}

export function getTransactionQuarterByDate(theDate){
    return getQuarter(theDate).quarter + "-" + new Date(theDate).getFullYear()
}



// _________________________________ Date - Time Related Functions _________________________________
export function dateToMonth(date){
    let dateObject = new Date(date)
    return date ? dateObject.toLocaleString('default', { month: 'short' }) : null
}

export function dateToYear(date){
    let dateObject = new Date(date)
    return date ?  dateObject.getFullYear() : null
}


export function dataParser(data){
    if(!data.data){
        return data
    }

    return dataParser(data.data)
}

// _________________________________ Querying and Data Functions _________________________________



const getCellData = async (query, extraParams = {}) => {
    let base = process.env.NODE_ENV === 'production'
        ? (window.location.href + "api")
        : "http://localhost:5000";
    

    const url = `${base}/query`;

    if (!String(query).toLowerCase().includes("select")) {
        return query;
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, ...extraParams })
        });

        const data = await response.text();
        return data;
    } catch (error) {
        console.error(error);
        return "0.0";
    }
};

export async function resolveReportRows(report, extraParams = {}) {
    const resolvedData = await getCellData(report, extraParams);
    if (Array.isArray(resolvedData)) {
        return resolvedData;
    }
    if (typeof resolvedData !== 'string') {
        return [];
    }
    try {
        const parsedData = JSON.parse(resolvedData);
        return Array.isArray(parsedData) ? parsedData : [];
    } catch {
        return [];
    }
}

export async function exportReportAsCSV(report, filename = 'exported_data.csv', extraParams = {}) {
    const rows = await resolveReportRows(report, extraParams);
    if (rows.length === 0) {
        return;
    }

    const headers = Object.keys(rows[0]);
    const csvRows = [
        headers.join(','),
        ...rows.map(row => headers.map(header => {
            const value = row[header] ?? '';
            return `"${String(value).replace(/"/g, '""')}"`;
        }).join(','))
    ];
    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}




export default getCellData;

// _________________________________ General Functions _________________________________




export function randomInt(min,max){
    return Math.floor(Math.random() * (max-min + 1)) + min;
}

export function getRandomItemFromList(list){
    return list[randomInt(0,list.length)]
}

export function getRandomColor(){
    let hex_vals = ['a','b','c','d','e','f','1','2','3','4','5','6','7','8','9','0']
    let color = `#${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}`
    return color
}

export function getColorforTransactionType(type) {
    var typeColorMap = {
        "loan product applications": FNB_PIE_PRIMARY_COLOURS[1],
        "mixed product applications": FNB_PIE_PRIMARY_COLOURS[4],
        "deposit product applications": FNB_PIE_PRIMARY_COLOURS[0],
        "multi product applications": FNB_PIE_PRIMARY_COLOURS[3],
        "loan product apps": FNB_PIE_PRIMARY_COLOURS[1],
        "mixed product apps": FNB_PIE_PRIMARY_COLOURS[2],
        "deposit product apps": FNB_PIE_PRIMARY_COLOURS[0],
        "multi product apps": FNB_PIE_PRIMARY_COLOURS[3],
        "is null": FNB_PIE_PRIMARY_COLOURS[1],
        "ach": FNB_PIE_PRIMARY_COLOURS[3],
        "credit_or_debit": FNB_PIE_PRIMARY_COLOURS[0],
        "internal": FNB_PIE_PRIMARY_COLOURS[1],
        "applications in progress (abandoned)": FNB_PIE_PRIMARY_COLOURS[7],
        "applications submitted (error)": FNB_PIE_PRIMARY_COLOURS[6],
        "applications declined": FNB_PIE_PRIMARY_COLOURS[7],
        "applications expired": FNB_PIE_PRIMARY_COLOURS[0],
        "total unsuccessful applications": FNB_PIE_PRIMARY_COLOURS[1],
        "applications in progress (started)": FNB_PIE_PRIMARY_COLOURS[7],
        "applications in progress (saved)": FNB_PIE_PRIMARY_COLOURS[3],
        "applications submitted(under review)": FNB_PIE_PRIMARY_COLOURS[4],
        "applications approved(awaiting entry)": FNB_PIE_PRIMARY_COLOURS[5],
        "applications approved(in underwriting)": FNB_PIE_PRIMARY_COLOURS[6],
        "applications approved(funding ongoing)": FNB_PIE_PRIMARY_COLOURS[7],
        "applications approved(onboarded)": FNB_PIE_PRIMARY_COLOURS[0],
        "total successful applications": FNB_PIE_PRIMARY_COLOURS[1],
        "applications missing": FNB_PIE_PRIMARY_COLOURS[5],
        "total applications started": FNB_PIE_PRIMARY_COLOURS[3],
        "change in applicatins started": FNB_PIE_PRIMARY_COLOURS[4],
        "multi product applications (started)": FNB_PIE_PRIMARY_COLOURS[5],
        "single product applications (started)": FNB_PIE_PRIMARY_COLOURS[6],
        "total applications submitted": FNB_PIE_PRIMARY_COLOURS[7],
        "change in applications submitted": FNB_PIE_PRIMARY_COLOURS[0],
        "multi product applications (submitted)": FNB_PIE_PRIMARY_COLOURS[1],
        "single product applications (submitted)": FNB_PIE_PRIMARY_COLOURS[5],
        "Period Totals": FNB_PIE_PRIMARY_COLOURS[0],
        "Grand Totals": FNB_PIE_PRIMARY_COLOURS[1],
        "Products per Application": FNB_PIE_PRIMARY_COLOURS[3],
        "Apps": FNB_PIE_PRIMARY_COLOURS[4],
        "Prods": FNB_PIE_PRIMARY_COLOURS[5],
        "Apps     /     Prods": FNB_PIE_PRIMARY_COLOURS[6],
        "total applications": FNB_PIE_PRIMARY_COLOURS[1],
        "totals": FNB_PIE_PRIMARY_COLOURS[1],
        "total": FNB_PIE_PRIMARY_COLOURS[1],
        "Consumer deposit applications": FNB_PIE_PRIMARY_COLOURS[0],
        "Consumer deposit Products": FNB_PIE_PRIMARY_COLOURS[0],
        "Consumer loan applications": FNB_PIE_PRIMARY_COLOURS[3],    
        "Consumer loan Products": FNB_PIE_PRIMARY_COLOURS[3],
        "Consumer mixed applications": FNB_PIE_PRIMARY_COLOURS[1],
        "Consumer mixed products": FNB_PIE_PRIMARY_COLOURS[1],
        "CrossSell Accepted": FNB_PIE_PRIMARY_COLOURS[1],
        "CrossSell Presented": FNB_PIE_PRIMARY_COLOURS[0],
        "Acceptance %age": FNB_PIE_PRIMARY_COLOURS[2],
        "Total-Started-[Mixed]": FNB_PIE_PRIMARY_COLOURS[6],
        "Total-Started-[Lending]": FNB_PIE_PRIMARY_COLOURS[1],
        "Total-Started-[Deposit]": FNB_PIE_PRIMARY_COLOURS[0],
        "Total-Started-[Multi]": FNB_PIE_PRIMARY_COLOURS[3],        
        "Total-Opened/Approved-[Mixed]": FNB_PIE_PRIMARY_COLOURS[6],
        "Total-Opened/Approved-[Lending]": FNB_PIE_PRIMARY_COLOURS[1],
        "Total-Opened/Approved-[Deposit]": FNB_PIE_PRIMARY_COLOURS[0],
        "Total-Opened/Approved-[Multi]": FNB_PIE_PRIMARY_COLOURS[3],        
        "Total-Submitted-[Mixed]": FNB_PIE_PRIMARY_COLOURS[6],
        "Total-Submitted-[Lending]": FNB_PIE_PRIMARY_COLOURS[1],
        "Total-Submitted-[Deposit]": FNB_PIE_PRIMARY_COLOURS[0],
        "Total-Submitted-[Multi]": FNB_PIE_PRIMARY_COLOURS[3],
        "Started": FNB_PIE_PRIMARY_COLOURS[0],
        "Submitted": FNB_PIE_PRIMARY_COLOURS[1],
        "Opened/Approved": FNB_PIE_PRIMARY_COLOURS[2],
        
    };

    Object.keys(typeColorMap).forEach(key => {
        const trimmedKey = key.toLowerCase().trim();
        if (trimmedKey !== key) {
            typeColorMap[trimmedKey] = typeColorMap[key];
            delete typeColorMap[key];
        }
    });

    type = type?.toLowerCase().trim();
    return typeColorMap[type] || 'black'; // Default color if type not found
}


export function showPointValuesInLineChart(dont_show_for_index=[]){
    return {
        id : 'pointValue',
        afterDatasetsDraw: (chart) => {
            const { ctx } = chart;
            chart.data.datasets.forEach((dataset, datasetIndex) => {
                if(dont_show_for_index.includes(datasetIndex)){
                    return;
                }
                const meta = chart.getDatasetMeta(datasetIndex);
                

                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';

                meta.data.forEach((point, index) => {

                    
                    const value = dataset.data[index];
                    if (value === null || value === 0) return; // Skip null values
                    const x = point.x;
                    const y = point.y;

                    
                    
                    ctx.save();
                    ctx.fillStyle = getColorforTransactionType(meta.label) // Text color
                    let gap = 10;
                    ctx.fillText(value, x, y-gap); // Adjust the position as needed
                });
            });
            
            ctx.restore();

        }
    }
}

export function showQuarterMarkersInLineChart() {
    return {
        id: 'quarterMarkers',
        afterDraw: (chart) => {
            const { ctx, chartArea: { top, bottom }, scales: { x } } = chart;
            const labels = x.getLabels();

            const quarterStartMonths = ['Jan', 'Apr', 'Jul', 'Oct'];

            labels.forEach((label, index) => {
                const month = label.split(' ')[0]; // Assumes format like "Jan 2025"
                if (quarterStartMonths.includes(month)) {
                    const xPos = x.getPixelForTick(index);
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(xPos, top);
                    ctx.lineTo(xPos, bottom);
                    ctx.strokeStyle = '#888'; // Customize color
                    ctx.lineWidth = 1;
                    ctx.setLineDash([4, 4]); // Dashed line
                    ctx.stroke();
                    ctx.restore();
                }
            });
        }
    };
}




export function getQuarterlyTableHeader(list,subColumnRows = null) {
    // remove duplicates
    const uniqueList = [...new Set(list)];
    return (
        <ColumnGroup>
            <Row>
                {uniqueList.map((item, index) => (
                    <Column 
                        key={index} 
                        header={item} 
                        colSpan={list.filter(x => x === item).length} 
                    />
                ))}
            </Row>
            {subColumnRows}
        </ColumnGroup>
    );
}

export const APP_PRODS_SUB_HEADER = (count) => {

    
    return (
        <Row>
            <Column header="" colSpan={1} />
                 <Column key={`app-1`} header={"Apps"} colSpan={1} />
                    <Column key={`prod-2`} header={"Prods"} colSpan={1} />
                    <Column key={`app-3`} header={"Apps"} colSpan={1} />
                    <Column key={`prod-4`} header={"Prods"} colSpan={1} />
            <Column header="" colSpan={1} />
        </Row>
    );
};


export const FUNDING_TYPE_SUBHEADER = (count)=>{
    var ccount = count-1;
    return (
        <Row>
            <Column key={`blank`} header="" colSpan={1} />
            {[...Array(ccount)].map((_, index) => (
                    <Column key={`count-${index}`} header={index%2 === 0? "Count" : "Amount" } colSpan={1} />
            ))}
        </Row>
    )
}

export const FUNDING_TYPE_IN_MILLION_SUBHEADER = (count)=>{
    var ccount = count-1;
    return (
        <Row>
            <Column key={`blank`} header="" colSpan={1} />
            {[...Array(ccount)].map((_, index) => (
                    <Column key={`count-${index}`} header={index%2 === 0? "Count" : "Amount (in Mil)" } colSpan={1} />
            ))}
        </Row>
    )
}



export const MONTHLY_REPORT_SUBHEADER = (count)=>{
    var ccount = count-1;
    // ccount = ccount *2;
    return (
        <Row>
            <Column key={`blank`} header="" colSpan={1} />
            {[...Array(ccount)].map((_, index) => (
                    <Column key={`count-${index}`} header={index%2 === 0? "#" : "-" } colSpan={1} />
            ))}
        </Row>
    )
}



