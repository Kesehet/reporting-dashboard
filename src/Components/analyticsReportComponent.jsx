import 'primeicons/primeicons.css';
import 'primereact/resources/themes/nova/theme.css';
import 'primereact/resources/primereact.min.css';
import './../Styles/analyticsRep.css';
import FNBPieChart from '../Utils/Components/FNBPieChart';
import FNBTable from '../Utils/Components/FNBTable';
import FNBLineChart from '../Utils/Components/FNBLineChart';
import ChartCard from '../Utils/Components/ChartCard';
import { APP_PRODS_SUB_HEADER } from '../Utils/Components/Utils';



const AnalyticsReportComponent = () => {
    

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
                                <FNBLineChart data={"Application Volume By Product (All Started Apps) Line"} />
                                <FNBTable data={"Application Volume By Product (All Started Apps) Line Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Submitted Apps)" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product (All Submitted Apps) Line"} />
                                <FNBTable data={"Application Volume By Product (All Submitted Apps) Line Table"} styleNow={{ width: '101%' }} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product (All Approved Apps)" styleNow={{ width: '32.5%' }}
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product (All Opened Or Approved Apps) Line"} />
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
                                <FNBLineChart data={"Application Volume By Product Quarterly (All Started Apps) Line"} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Started Apps) Table"} styleNow={{ width: '101%' }}  subHeaderRow={APP_PRODS_SUB_HEADER} chartAPIParams={{}}  />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Submitted Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product Quarterly (All Submitted Apps) Line"} />
                                <FNBTable data={"Application Volume By Product Quarterly (All Submitted Apps) Table"} styleNow={{ width: '101%' }}   subHeaderRow={APP_PRODS_SUB_HEADER} chartAPIParams={{}} />
                            </>
                        )}
                />
                <ChartCard title="Application Volume By Product Quarterly (All Approved Apps)"styleNow={{ width: '32.5%' }} 
                    items={(
                            <>
                                <FNBLineChart data={"Application Volume By Product Quarterly (All Opened Or Approved Apps) Line"} />
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
        </>
    );
}; 

export default AnalyticsReportComponent;
