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
    data = dataParser(data);
    let pointers = data.labels;

    let labels = Object.keys(data.datasetMap);
    let values = Object.values(data.datasetMap);
    var dataset = [];
    for(let i=0; i < values.length; i++){
        dataset.push({
            "label": labels[i],
            "data": values[i],
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
        if(q == "Q"+(i+1)){
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
                else if (transactionObject.NumLendingProducts ==1 && transactionObject.NumDepositProducts == 0){
                    category = "loanOnly"
                }
                else if (transactionObject.NumDepositProducts ==1 && transactionObject.NumLendingProducts == 0){
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
    
        console.log("Query to Process for UI", query);

    const url = `${base}/query`;

    if (!String(query).toLowerCase().includes("select")) {
        console.log("Query Returned");
        return query;
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': localStorage.getItem('token'),
            },
            body: JSON.stringify({ query, ...extraParams })
        });

        const data = await response.json();
        return data;
    } catch (error) {
        console.error(error);
        return "Unknown Error Occurred.";
    }
};




export default getCellData;

// _________________________________ General Functions _________________________________

export function normalizeNumber(value) {
  if (typeof value !== 'number') {
    try{
        value = parseFloat(value);
    } catch(e) {
        return value;
    }
  }

  // Check if the number has a non-zero decimal part
  if (value % 1 === 0) {
    return parseInt(value); // Return as integer
  } else {
    return parseFloat(value); // Return as float
  }
}





export function randomInt(min,max){
    return Math.floor(Math.random() * (max-min + 1)) + min;
}

export function getRandomItemFromList(list){
    return list[randomInt(0,list.length)]
}

export function getRandomColor(){
    let hex_vals = ['a','b','c','d','e','f','1','2','3','4','5','6','7','8','9','0']
    let color = `#${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}${getRandomItemFromList(hex_vals)}`
    console.log(color)
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


export function showPointValuesInLineChart(){
    console.log("showPointValuesInLineChart")
    return {
        id : 'pointValue',
        afterDatasetsDraw: (chart) => {
            const { ctx } = chart;
            chart.data.datasets.forEach((dataset, datasetIndex) => {
                const meta = chart.getDatasetMeta(datasetIndex);
                

                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';

                meta.data.forEach((point, index) => {

                    
                    const value = dataset.data[index];
                    if (value === null || value == 0) return; // Skip null values
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
    console.log("Unique List",uniqueList, subColumnRows)
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
    var ccount = count-2;

    console.log()
    
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
    // ccount = ccount *2;
    console.log("count", count)
    return (
        <Row>
            <Column key={`blank`} header="" colSpan={1} />
            {[...Array(ccount)].map((_, index) => (
                    <Column key={`count-${index}`} header={index%2 == 0? "Count" : "Amount" } colSpan={1} />
            ))}
        </Row>
    )
}

export const FUNDING_TYPE_IN_MILLION_SUBHEADER = (count)=>{
    var ccount = count-1;
    // ccount = ccount *2;
    console.log("count", count)
    return (
        <Row>
            <Column key={`blank`} header="" colSpan={1} />
            {[...Array(ccount)].map((_, index) => (
                    <Column key={`count-${index}`} header={index%2 == 0? "Count" : "Amount (in Mil)" } colSpan={1} />
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
                    <Column key={`count-${index}`} header={index%2 == 0? "#" : "% Chg" } colSpan={1} />
            ))}
        </Row>
    )
}




//    ('1583064','1583547','1585403','1585438','1585559','1585593','1585899','1585928','1586121','1587571','1587627','1587835','1587899','1587954','1588026','1588076','1588124','1588345','1588448','1588585','1588600','1588692','1588735','1588794','1588830','1588883','1590243','1590293','1593676','1593735','1593822','1593842','1593922','1593965','1593996','1594157','1594188','1594395','1594471','1594525','1594584','1596074','1596365','1596446','1596670','1596776','1598665','1598720','1599195','1599275','1599395','1599416','1601091','1601163','1601199','1601222','1601445','1601682','1603293','1603347','1603406','1603439','1603467','1603816','1605023','1607761','1607852','1607873','1608378','1608413','1608738','1610687','1610871','1611103','1612673','1612751','1612799','1613160','1613447','1615021','1615221','1615251','1615252','1615280','1615371','1615392','1617038','1617053','1617071','1617096','1617400','1617592','1617689','1617769','1617793','1623184','1623295','1623317','1623599','1623902','1624210','1626036','1626179','1629009','1629348','1630703','1631642','1631654','1631997','1632042','1632132','1632386','1634522','1634586','1634743','1634936','1634940','1635243','1641018','1641702','1643569','1643572','1643634','1643682','1643739','1643756','1644145','1645626','1645704','1646236','1646310','1648649','1648653','1648656','1648664','1648892','1649003','1650653','1650983','1651065','1651103','1651123','1651327','1656556','1656764','1656842','1656891','1656950','1656964','1657143','1657249','1658696','1658785','1658806','1658928','1659033','1659125','1659273','1659286','1659330','1659335','1659341','1659403','1659430','1659458','1659476','1659500','1659572','1659590','1659592','1659640','1659679','1660242','1661474','1661490','1661509','1661629','1661639','1661641','1661684','1661726','1661773','1661782','1661787','1661846','1661886','1661915','1661925','1661972','1662007','1662038','1662044','1662055','1662079','1662097','1662108','1662172','1662212','1662236','1662238','1662258','1662296','1662339','1662420','1662454','1662536','1662594','1662640','1664319','1664374','1664460','1664491','1664503','1664505','1664510','1664539','1664546','1664611','1664637','1664670','1664714','1664767','1664775','1664859','1664847','1664935','1664890','1664990','1665053','1665107','1665111','1665148','1665152','1665156','1665180','1665185','1665199','1665205','1665256','1665305','1665327','1665342','1665349','1665500','1665547','1667268','1667438','1667441','1667443','1667446','1667480','1667503','1667506','1667566','1667610','1667627','1667691','1667708','1667737','1667761','1667788','1667804','1667806','1667830','1667907','1667945','1667987','1668001','1668079','1668086','1668126','1668109','1668137','1668155','1668174','1668205','1668211','1668215','1668269','1668278','1668284','1668299','1668323','1668364','1668391','1668395','1668415','1668472','1668502','1669792','1669803','1669817','1669884','1669899','1669932','1669939','1669921','1670007','1673530','1673564','1673582','1673587','1673644','1673678','1673717','1673740','1673781','1673801','1673837','1673838','1673872','1673899','1674034','1674028','1674049','1674065','1674073','1674134','1674178','1674201','1674204','1674270','1674282','1674284','1674337','1674347','1674354','1674374','1674377','1674384','1674414','1674458','1674443','1674502','1674520','1674550','1674557','1674642','1674609','1674695','1674709','1674731','1674740','1674765','1674793','1674806','1674813','1674858','1674846','1674872','1674847','1675157','1675170','1675210','1675260','1675266','1677165','1677185','1677213','1677243','1677283','1677292','1677314','1677320','1677343','1677366','1677427','1677436','1677507','1677525','1677570','1677615','1677630','1677648','1677661','1677678','1677685','1677726','1677747','1677749','1677703','1677780','1677832','1677844','1677917','1677889','1677898','1677974','1677951','1677982','1677989','1677995','1678019','1678097','1678126','1678284','1678289','1678303','1678307','1678345','1678368','1678400','1678479','1678444','1678462','1678497','1678505','1678524','1678535','1678589','1678616','1678680','1678715','1678778','1678786','1678809','1678841','1678878','1678871','1678910','1678934','1678966','1679019','1679071','1679078','1679100','1679148','1679158','1681047','1681052','1681057','1681075','1681115','1681128','1681163','1681167','1681179','1681201','1681202','1681204','1681210','1681241','1681245','1681254','1681275','1681295','1681310','1681314','1681330','1681341','1681377','1681385','1681428','1681451','1681464','1681484','1681486','1681499','1681540','1681532','1681545','1681566','1681573','1681652','1681656','1681658','1681706','1681731','1681766','1681867','1681881','1681893','1681910','1681964','1681989','1682084','1682108','1682161','1682165','1682189','1682217','1682237','1682272','1682340','1682391','1682402','1682431','1682448','1682478','1682536','1682538','1682644','1684664','1684688','1684739','1684764','1684808','1684825','1684861','1684853','1684874','1684900','1684881','1684910','1684914','1684931','1684932','1684933','1684943','1684941','1684944','1684982','1685002','1685012','1685025','1685030','1685044','1685051','1685078','1685102','1685197','1685288','1685447','1685485','1685512','1685540','1685570','1685577','1685605','1685608','1685641','1685655','1685720','1685799','1685825','1685842','1685851','1685860','1685899','1685915','1685975','1685940','1686036','1686074','1686100','1688030','1688043','1688049','1688095','1688117','1688150','1688191','1688223','1688238','1688244','1688246','1688259','1688295','1688298','1688319','1688324','1688369','1688448','1688456','1688411','1688434','1688479','1688512','1688519','1688544','1688591','1688554','1688568','1688577','1688597','1688616','1688650','1688653','1688673','1688715','1688727','1688747','1688751','1688780','1688788','1688837','1688840','1688862','1688866','1688873','1688898','1688901','1688925','1688927','1688957','1688975','1688986','1689027','1689029','1689156','1689081','1689086','1689105','1689130','1689147','1689165','1689121','1689207','1689193','1689241','1689224','1689270','1689276','1689301','1689346','1689354','1689368','1689392','1689441','1689405','1689448','1689413','1689420','1689411','1689480','1689512','1689510','1689526','1689559','1689566','1689589','1689602','1689613','1689628','1689637','1689679','1689733','1691179','1691184','1691196','1691214','1691227','1691289','1691333','1691343','1691381','1691414','1691456','1691459','1692251','1696864','1696874','1696895','1696905','1696869','1696950','1696957','1696965','1696984','1696988','1697014','1697020','1697006','1697027','1697073','1697090','1697094','1697134','1697138','1697142','1697158','1697194','1697205','1697253','1697261','1697324','1697322','1697355','1697359','1697388','1697367','1697380','1697382','1697406','1697421','1697435','1697438','1697441','1697499','1697540','1697545','1697554','1697570','1697574','1697584','1697578','1697612','1697626','1697630','1697651','1697668','1697683','1697685','1697707','1697710','1697734','1697751','1697782','1697853','1697820','1697860','1697906','1697891','1697923','1697925','1697930','1697985','1698044','1698020','1698062','1698069','1698072','1698101','1698130','1698177','1698171','1698182','1698221','1698226','1698244','1698259','1698273','1698379','1698404','1698433','1698442','1698501','1700267','1700298','1700324','1700338','1700357','1700361','1700399','1700406','1700433','1700471','1700489','1700510','1700527','1700532','1700537','1700542','1700552','1700624','1700627','1700640','1700660','1700678','1700680','1700687','1700776','1700716','1700726','1700731','1700750','1700769','1700773','1700849','1700850','1700865','1700892','1700895','1700916','1700983','1700990','1700999','1701003','1701016','1701044','1701049','1701069','1701072','1701082','1701096','1701122','1701124','1701113','1701134','1701102','1701162','1701214','1701171','1701172','1701230','1701152','1701238','1701240','1701273','1701282','1701288','1701292','1701297','1701332','1701309','1701348','1701354','1701176','1701386','1701405','1701430','1701432','1701507','1701510','1701519','1701521','1701523','1701598','1701601','1701622','1701628','1701653','1701675','1701681','1701687','1701702','1701708','1701729','1701731','1701771','1701773','1701816','1701827','1701845','1701876','1701915','1701935','1703529','1703537','1703573','1703583','1703638','1703669','1703691','1703716','1703743','1703764','1703766','1703779','1703803','1703785','1703816','1703829','1703882','1703905','1703917','1703993','1704003','1704007','1704043','1704048','1704066','1704094','1704103','1704122','1704131','1704144','1704146','1704158','1704167','1704186','1704233','1704294','1704285','1704336','1704349','1704371','1704372','1704394','1704435','1704456','1704460','1704463','1704535','1704549','1704551','1704556','1704566','1704586','1704640','1704692','1704696','1704703','1704726','1704743','1704773','1704795','1704825','1704800','1704814','1704829','1704839','1704860','1704868','1704874','1704883','1704900','1704902','1704926','1704967','1704960','1705055','1705165')
