import 'primeicons/primeicons.css';
import 'primereact/resources/themes/nova/theme.css';
import 'primereact/resources/primereact.min.css';
import './../Styles/analyticsRep.css';
import FNBPieChart from '../Utils/Components/FNBPieChart';
import FNBTable from '../Utils/Components/FNBTable';
import FNBLineChart from '../Utils/Components/FNBLineChart';
import ChartCard from '../Utils/Components/ChartCard';
import { APP_PRODS_SUB_HEADER } from '../Utils/Components/Utils';
import { YearQuarterList } from '../Utils/Components/YearQuarterList';
import React, { useState } from 'react';



const AnalyticsReportComponent = () => {
    
    var thisyear = new Date().getFullYear();
    let yearOffset = 2
    let past10years = Array.from({ length: (yearOffset+1) }, (_, i) => thisyear - i);
    let next10years = Array.from({ length: yearOffset }, (_, i) => thisyear + i + 1);
    let allYears = past10years.concat(next10years);
    allYears.push(thisyear);
    allYears = Array.from(new Set(allYears)).sort((a, b) => a - b);
    const [analyticsConfig, setanalyticsConfig] = useState({
        "Custom Quarterly List": [{ year: thisyear, quarter: 'Q1' }, { year: thisyear, quarter: 'Q2' }],
    });
    return (
        <>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap:'16px', padding: '16px' }}  >

                

                
                
                <ChartCard title="Application Volume By Product (All Started Apps) - Year to Date" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume By Product (All Started Apps) Pie - Year to Date"} />
                                <FNBTable data={"Application Volume By Product (All Started Apps) Pie Table - Year to Date"} styleNow={{ width: '102%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Submitted Apps) - Year to Date" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume By Product (All Submitted Apps) Pie - Year to Date"} />
                                <FNBTable data={"Application Volume By Product (All Submitted Apps) Pie Table - Year to Date"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Approved Apps) - Year to Date" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume By Product (All Opened Or Approved Apps) Pie - Year to Date"} />
                                <FNBTable data={"Application Volume By Product (All Opened Or Approved Apps) Pie Table - Year to Date"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Started Apps)" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product (All Started Apps) Line"} chartAPIParams={{}} />
                                <FNBTable data={"Application Volume By Product (All Started Apps) Line Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Submitted Apps)" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product (All Submitted Apps) Line"} chartAPIParams={{}} />
                                <FNBTable data={"Application Volume By Product (All Submitted Apps) Line Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Approved Apps)" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product (All Opened Or Approved Apps) Line"} chartAPIParams={{}} />
                                <FNBTable data={"Application Volume By Product (All Opened Or Approved Apps) Line Table"} styleNow={{ width: '101%' }}  chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Started Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume By Product Quarterly (All Started Apps) Pie"} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Started Apps) Table"} styleNow={{ width: '101%' }} subHeaderRow={APP_PRODS_SUB_HEADER} chartAPIParams={{}} />
                            </>
                        )}
                /> 
                <ChartCard title="Application Volume By Product Quarterly (All Submitted Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume By Product Quarterly (All Submitted Apps) Pie"} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Submitted Apps) Table"} styleNow={{ width: '101%' }}  subHeaderRow={APP_PRODS_SUB_HEADER}  chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Approved Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume By Product Quarterly (All Opened Or Approved Apps) Pie"} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Opened Or Approved Apps) Table"} styleNow={{ width: '101%' }}  subHeaderRow={APP_PRODS_SUB_HEADER}  chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Started Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product Quarterly (All Started Apps) Line"} chartAPIParams={{}} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Started Apps) Table"} styleNow={{ width: '101%' }}  subHeaderRow={APP_PRODS_SUB_HEADER} chartAPIParams={{}}  />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Submitted Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product Quarterly (All Submitted Apps) Line"} chartAPIParams={{}} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Submitted Apps) Table"} styleNow={{ width: '101%' }}   subHeaderRow={APP_PRODS_SUB_HEADER} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Approved Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product Quarterly (All Opened Or Approved Apps) Line"} chartAPIParams={{}} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Opened Or Approved Apps) Table"} styleNow={{ width: '101%' }}  subHeaderRow={APP_PRODS_SUB_HEADER} chartAPIParams={{}}  />
                            </>
                        )}
                />
                <ChartCard title="Application Volume by Product Current Quarter (All Started Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume by Product Current Quarter (All Started Apps) Pie"} />
                                <FNBTable data={"Application Volume by Product Current Quarter (All Started Apps) Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume by Product Current Quarter (All Submitted Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume by Product Current Quarter (All Submitted Apps) Pie"} />
                                <FNBTable data={"Application Volume by Product Current Quarter (All Submitted Apps) Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume by Product Current Quarter (All Approved Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBPieChart data={"Application Volume by Product Current Quarter (All Approved Apps) Pie"} />
                                <FNBTable data={"Application Volume by Product Current Quarter (All Approved Apps) Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />             
            </div>
            <hr/><hr/>
            <YearQuarterList
                                    
                                    initialValue={analyticsConfig["Custom Quarterly List"] || []}
                                    years={allYears}
                                    ariaLabelPrefix="Reporting Period"
                                    maxItems ={8}
                                    setList={(list)=>{
                                        if (list.length !== analyticsConfig["Custom Quarterly List"]?.length){   
                                            setanalyticsConfig({...analyticsConfig, "Custom Quarterly List": list});
                                        }
                                    }} />

            <ChartCard title="Custom Quarterly Analytics Table" styleNow={{ width: '100%' }} noDialog={true}
                    items={(
                            <>
                                
                                    {
                                        analyticsConfig["Custom Quarterly List"]?.length > 0 ? (
                                            <>
                                                <FNBTable data={"Custom Quarterly Analytics Common App Table"} styleNow={{ width: '101%' }} chartAPIParams={{quarters:analyticsConfig["Custom Quarterly List"], requestMethod:"POST"}} />
                                                <hr/>
                                                <FNBTable data={"Custom Quarterly Analytics Customer eCA Table"} styleNow={{ width: '101%' }} chartAPIParams={{quarters:analyticsConfig["Custom Quarterly List"], requestMethod:"POST"}} />
                                                <hr/>
                                                <FNBTable data={"Custom Quarterly Analytics InBranch Common App Table"} styleNow={{ width: '101%' }} chartAPIParams={{quarters:analyticsConfig["Custom Quarterly List"], requestMethod:"POST"}} />
                                            </>
                                        )
                                        : (
                                            <>
                                            <p>Please select at least one Year-Quarter to display the data table.</p>
                                            </>
                                        )
                                    }
                            </>
                    )}
                    />
        </>
    );
}; 

export default AnalyticsReportComponent;
