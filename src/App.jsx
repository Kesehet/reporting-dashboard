import React, { useState, useEffect } from 'react';
import 'primeicons/primeicons.css';
import 'primereact/resources/themes/nova/theme.css';
import 'primereact/resources/primereact.min.css';
import './Styles/App.css';
import './Styles/header.css';
import 'primereact/resources/primereact.css';
import 'primereact/resources/themes/lara-light-indigo/theme.css';

import ReportHeaderComponent from './Components/reportHeaderComponent';
import ReportFooterComponent from './Components/reportFooterComponent';
import ReportLoginComponent from './Components/reportLoginComponent';
import AnalyticsReportComponent from './Components/analyticsReportComponent';
import AuthorizationService from './Services/AuthorizationService';
import ChartCard from './Utils/Components/ChartCard';
import FNBLineChart from './Utils/Components/FNBLineChart';
import FNBReport from './Utils/Components/FNBReport';
import FNBTable from './Utils/Components/FNBTable';
import FNBMultipleTable from './Utils/Components/FNBMultiTable';
import FNBBarChart from './Utils/Components/FNBBarChart';
import FNBDataTable from './Utils/Components/FNBDataTable';
import { Card } from 'primereact/card';
import { FUNDING_TYPE_SUBHEADER, MONTHLY_REPORT_SUBHEADER, FUNDING_TYPE_IN_MILLION_SUBHEADER } from './Utils/Components/Utils';
import SidebarLayout from './Components/SidebarComponent';
import BORAsync from './Utils/Components/BORAsync';
import FNBStackedBarChart from './Utils/Components/FNBStackedBarChart';
import MultiFilterTable from './Utils/Components/MultiFilterTable';
import FlipCard from './Utils/Components/FlipCard';
import FNBBarWithLineChart from './Utils/Components/FNBBarWithLineChart';
import CardReport from './Utils/Components/CardReport';
import { Dropdown } from 'primereact/dropdown';
import msalInstance, { msalIsLoggedIn, msalLogin } from './Services/msalInstance';

function App() {
    const [dates, setDates] = useState(() => {
        const today = new Date();
        const tonight = new Date(today.setHours(23, 59, 59, 999));
        
        const thirtyDaysAgoMorning = new Date('2025-04-08T00:00:00Z');
        // console.log("Setting dates to:", thirtyDaysAgoMorning, "to", tonight);
        localStorage.setItem("start_date",thirtyDaysAgoMorning.toISOString().split('T')[0]);
        localStorage.setItem("end_date", tonight.toISOString().split('T')[0]);
        return [thirtyDaysAgoMorning, tonight];
      });
    const [CorBFilter, setCorBFilter] = useState("All");
    
    const [showPage, setPage] = useState("Monthly Report");
    //const [showPage, setPage] = useState("All Filters Table");
    
    const [pageConfig, setPageConfig] = useState({
            "Abandonment Report Application Type": "All",
            "BOR Component Application Type": "All",
            "Monthly Report Product Type Selector": "All"
        })

    const authService = new AuthorizationService("","");
    


    useEffect(() => {
        localStorage.setItem("CorBFilter", CorBFilter);
        // Set page to "loading" temporarily to show loading state
        let pNow = showPage;
        console.log(showPage);
        setPage("loading");
        setTimeout(() => {
            setPage(pNow);
        }, 1000);
    }, [CorBFilter]);

    useEffect(() => {
        // console.log("Setting start and end dates in local storage:", dates);
        if (!dates || dates.length !== 2 || !dates[0] || !dates[1]) {   return; }
        localStorage.setItem("start_date", dates[0].toISOString().split('T')[0]);
        localStorage.setItem("end_date", dates[1].toISOString().split('T')[0]);
    }, [dates]);

    

    if (!authService.isLoggedIn()) {
        
        return <ReportLoginComponent />;
    }


    const getPage = (page) => {
        if (page === "Graphs") {
            return (<AnalyticsReportComponent setPage={setPage} />)
        } 
        else if (page == "loading") {
            return (
                <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                    <p>Loading...</p>
                </div>
            );
        }
        else if (page === "BOR") {
            return (
                <div className="w3-container w3-card-4">
                    <h2 className="w3-center">In-Branch Originated Report</h2>
                    <BORAsync dates={dates} />
                </div>
            )
        }
        else if (page === "Business Deposit Reports") {
            return (
                <div className="w3-container w3-card-4">
                    <h2 className="w3-center">Business Deposit Reports</h2>
                    <BORAsync dates={dates} chartName='Business Deposit Reports' applicationTypeFilter={true} />
                </div>
            )
        }
        else if (page === "Multi Product Reports") {
            return (<div style={{ display: 'flex', flexWrap: 'wrap', gap:'16px', padding: '16px' }}  >
                <ChartCard title={"Top 10 Multi-Product Combinations"}
                                    styleNow={{"width":"99%"}}
                                    items={(
                                        <div className="p-grid">
                                            <FNBBarChart data={"Multi Products Product Set Id Bar"} />
                                            <FNBDataTable data={"Multi Products Product Set Id Table"} />
                                        </div>
                                    )}
                                />
                <ChartCard title={"Top 10 Cross Sell Products"}
                                    styleNow={{"width":"99%"}}
                                    items={(
                                        <div className="p-grid ">
                                            <FNBBarChart data={"Multi Products Cross Sell Bar"} />
                                            <FNBDataTable data={"Multi Products Cross Sell Table"} />
                                        </div>
                                    )}
                                />

                                <ChartCard title={"Top 10 Single product with Cross Sell Products"}
                                    styleNow={{"width":"99%"}}
                                    items={(
                                        <div className="p-grid ">
                                            <FNBBarChart data={"Top 10 Single product with Cross Sell Products Bar"} />
                                            <FNBDataTable data={"Top 10 Single product with Cross Sell Products Table"} />
                                        </div>
                                    )}
                                />

                                
                
                
            </div>)

        }
        else if (page == "New vs Exisitng Customers"){
             return (
                 <ChartCard title="New vs Existing Customer Report"
                     styleNow={{"width":"100%"}}
                     items={(
                             <div className="p-grid p-justify-center">
                                 <FNBStackedBarChart dates={dates} data={"New vs Exisitng Customers"} />
                                 <FNBTable dates={dates} data={"New vs Existing Customers Table"} chartAPIParams={{}} />
                             </div>
                         )}
                 />
             )
        }
        else if (page === "Declined Report") {
             return(
                         <>
                                <ChartCard title="Declined Report"
                                     styleNow={{"width":"100%"}}
                                     items={(
                                         <div className="p-grid p-justify-center">
                                             <FNBLineChart data={"Declined Report Line"} />
                                             <FNBTable data="Declined Report Table" dates={dates} 
                                              chartAPIParams={{}} />
                                         </div>
                                     )}
                                 />
                             <hr />
                                <ChartCard title="Declined Report"
                                     styleNow={{"width":"100%"}}
                                     items={(
                                         <div className="p-grid p-justify-center">
                                             <FNBBarChart data={"Type Of Decline Reasons Bar"} />
                                             <FNBDataTable data="Type Of Decline Reasons Table" dates={dates} 
                                              chartAPIParams={{}} />
                                         </div>
                                     )}
                                 />
                         </>
             )
        }
        else if (page === "All Transactions") {
            return (
                <>
                    
                   
                    <FNBDataTable data="All Transactions" />
                </>
            )
        }
        else if (page === "Abandonment Report") {
            return (
                        <>
                        
                            <Card title="Abandonment Report" style={{"width":"100%"}}>
                                <FNBReport dates={dates} chartName="Abandonment Report" SingularOrPlural={["Branch", "Branches"]} globalSettings={pageConfig} 
                                globalSettingSetter={setPageConfig} />
                            </Card>
                        
                            <hr />
                        
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', padding: '16px' }}>
                                <ChartCard title={"Abandonment Report by Week (" + pageConfig["Abandonment Report Application Type"] + ")"}
                                    styleNow={{"width":"49%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBBarChart data={"Abandonment Report by Week Bar"} chartAPIParams={{
                                                "application_type": pageConfig["Abandonment Report Application Type"]
                                            }} />
                                        </div>
                                    )}
                                />
                                <ChartCard title={"Abandonment Report by Month (" + pageConfig["Abandonment Report Application Type"] + ")"}
                                    styleNow={{"width":"49%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBBarChart data={"Abandonment Report by Month Pie"} chartAPIParams={{
                                                "application_type": pageConfig["Abandonment Report Application Type"]
                                            }} />
                                        </div>
                                    )}
                                />
                                <ChartCard title={"Abandonment Report by Year (" + pageConfig["Abandonment Report Application Type"] + ")"}
                                    styleNow={{"width":"49%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBBarChart data={"Abandonment Report by Year Pie"} chartAPIParams={{
                                                "application_type": pageConfig["Abandonment Report Application Type"]
                                            }} />
                                        </div>
                                    )}
                                />
                                <ChartCard title={"Abandonment Report by Types of Abandonment (" + pageConfig["Abandonment Report Application Type"] + ")"}
                                    styleNow={{"width":"49%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBBarChart data={"Abandonment Report by Types of Abandonment Pie"} chartAPIParams={{
                                                "application_type": pageConfig["Abandonment Report Application Type"]
                                            }} />
                                        </div>
                                    )}
                                />
                                <ChartCard title={"Zero Product Applications (" + pageConfig["Abandonment Report Application Type"] + ")"}
                                    styleNow={{"width":"98%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBBarChart data={"Zero Product Applications Bar"} chartAPIParams={{
                                                "application_type": pageConfig["Abandonment Report Application Type"]
                                            }} />
                                        </div>
                                    )}
                                />
                                <ChartCard title={"Zero Product Applications (" + pageConfig["Abandonment Report Application Type"] + ")"}
                                    styleNow={{"width":"98%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBTable data={"Zero Product Applications Table"} chartAPIParams={{
                                                "application_type": pageConfig["Abandonment Report Application Type"]
                                            }} />
                                        </div>
                                    )}
                                />
                                
                            </div>
                            
                        </>
            )
        }
        else if (page === "Lending & Deposit Control Report") {
            return (
                <FNBMultipleTable data="Lending And Deposit Reports" dates={dates} columnWidth={200} />
            )
        }
        else if (page === "Funding Type Report") {
            return(
                        <>
                                <ChartCard title="Funding Type Report"
                                    styleNow={{"width":"100%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBLineChart data={"Funding Type Report Line"} />
                                            <FNBTable data="Funding Type Report" dates={dates} subHeaderRow={
                                                FUNDING_TYPE_SUBHEADER
                                            } chartAPIParams={{}} />
                                        </div>
                                    )}
                                />
                            <hr />
                            
                        </>
            )
        }
        else if (page == "All Filters Table"){
            return (
                <>
                    <MultiFilterTable  />
                </>
            )
        }
        else if(page == "Spot & Current Balance Amounts"){
            return (
                <>
                    <CardReport CHART_NAME={"Spot & Current Balance Account Insights"} title={"Spot & Current Balance Account Insights"} />
                    
                            
                            <h2>Common App</h2>
                            <h3>Opening Deposit (Spot) Amount</h3>
                                        <FNBStackedBarChart chartAPIParams={{
                                            what_column_to_add : "Initial_Deposit",
                                            application_type: "Online",
                                        }} dates={dates}  data={"Spot & Current Balance Account Stacked Chart"} />
                            <h3>Current Balance Amount</h3>
                                        <FNBStackedBarChart chartAPIParams={{
                                            what_column_to_add : "Current_Balance",
                                            application_type: "Online",
                                        }} dates={dates}  data={"Spot & Current Balance Account Stacked Chart"} />



                            <h2>In Branch</h2>
                            <h3>Opening Deposit (Spot) Amount</h3>
                                        <FNBStackedBarChart chartAPIParams={{
                                            what_column_to_add : "Initial_Deposit",
                                            application_type: "Banker Assisted",
                                        }} dates={dates}  data={"Spot & Current Balance Account Stacked Chart"} />

                            <h3>Current Balance Amount</h3>
                            <FNBStackedBarChart chartAPIParams={{
                                what_column_to_add : "Current_Balance",
                                application_type: "Banker Assisted",
                            }} dates={dates}  data={"Spot & Current Balance Account Stacked Chart"} />
                </>
            )
        }
        else if (page == "Loan Commitments"){
            return (
                <>
                    <CardReport
                        CHART_NAME="Loan Commitment Insights"
                        params={{ BranchID: 'All', start_date: localStorage.getItem('start_date'), end_date: localStorage.getItem('end_date') }}
                        title="Loan Accounts and Commitment Report"
                        renderOrder={['Started', 'Submitted', 'Opened/Approved']}
                        />
                    <ChartCard title="Loan Account and Commitment - Quarterly Analysis" styleNow={{ width: '99%' }}
                    items={(
                            <>
                                <FlipCard title="Loan Accounts and Commitments"
                                styleNow={{"width":"100%"}}
                                itemFront={(
                                <>
                                <FNBBarWithLineChart data="Loan Commitment Bar And Line" dates={dates} chartAPIParams={{show_line: true}} />
                                
                                </>
                                )}
                                itemBack={(
                                <>
                                <FNBBarWithLineChart
                                    data="Loan Commitment Bar And Line" 
                                    dates={dates} 
                                    sideBySide={true}
                                    chartAPIParams={{
                                        start_date: new Date(new Date().getFullYear() - 3, 0, 1).toISOString().slice(0, 10),
                                        end_date: new Date(new Date().getFullYear(), 11, 31).toISOString().slice(0, 10),
                                        sideByside:true
                                    }} 
                                />
                                </>
                                )}
                                />
                                <FNBTable data="Loan Commitment Stacked Table" dates={dates} chartAPIParams={{send_avg:true}} />  
                            </>
                        )}
                    />
                    
                    <ChartCard title="Loan Account and Commitment - Secured (vs) Unsecured Loans" styleNow={{ width: '99%' }}
                    items={(
                            <>
                                <FNBStackedBarChart dates={dates}  data={"Loan Commitment Stacked Bar"} />
                                <FNBTable data="Loan Commitment Stacked Table" dates={dates} subHeaderRow={
                                                FUNDING_TYPE_IN_MILLION_SUBHEADER
                                            } chartAPIParams={{send_sec_unsec:true,send_total:true}} />   
                            </>
                        )}
                    />
                </>

                
            )
        }
        else if (page === "Monthly Report") {
            {
                var start_date = new Date(new Date().getFullYear(), 0, 1).toISOString().slice(0, 10);
                var end_date = new Date().toISOString().slice(0, 10);
            }
            return(
                        <>
                                
                                <Dropdown
                                value={pageConfig["Monthly Report Product Type Selector"]}
                                onChange={(e) => setPageConfig({
                                    ...pageConfig,
                                    "Monthly Report Product Type Selector": e.value
                                })}
                                options={[
                                    { label: 'All', value: 'All' },
                                    { label: 'Products', value: 'Products' },
                                    { label: 'Loan Products', value: 'Loan Products' },
                                    { label: 'Mixed Products', value: 'Mixed Products' },
                                    { label: 'Deposit Products', value: 'Deposit Products' }
                                ]}
                                placeholder="Select a Variant"
                                />


                                <ChartCard title="Common App (In Branch)"
                                    styleNow={{"width":"100%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            
                                            <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Common App (In Branch)"} data="Monthly In Branch Report" dates={dates} subHeaderRow={
                                                MONTHLY_REPORT_SUBHEADER
                                            } chartAPIParams={{
                                                start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]
                                            }} />
                                        </div>
                                    )}
                                />
                                <ChartCard title="Common App (Consumer-Facing)"
                                    styleNow={{"width":"100%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Common App (Consumer-Facing)"} data="Monthly Consumer Facing Report" dates={dates} subHeaderRow={
                                                MONTHLY_REPORT_SUBHEADER
                                            } chartAPIParams={{start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]}} />
                                        </div>
                                    )}
                                />
                                <ChartCard title="Business Deposits"
                                    styleNow={{"width":"100%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Business Deposits"} data="Monthly Business Deposits Report" dates={dates} subHeaderRow={
                                                MONTHLY_REPORT_SUBHEADER
                                            } chartAPIParams={{start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]}} />
                                        </div>
                                    )}
                                />
                                <ChartCard title="In Branch BPM/CRIF Entered"
                                    styleNow={{"width":"100%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBTable data="Monthly BPM and CRIF Report" dates={dates} subHeaderRow={
                                                MONTHLY_REPORT_SUBHEADER
                                            } chartAPIParams={{start_date,end_date}} />
                                        </div>
                                    )}
                                />
                                <ChartCard title="In Branch - eCA vs. BPM/CRIF - %eCA Store Common App vs. % BPM/CRIF App "
                                    styleNow={{"width":"100%"}}
                                    items={(
                                        <div className="p-grid p-justify-center">
                                            <FNBTable data="Monthly In Branch vs BPM and CRIF Report" dates={dates} subHeaderRow={
                                                MONTHLY_REPORT_SUBHEADER
                                            } chartAPIParams={{start_date,end_date}} />
                                        </div>
                                    )}
                                />
                            <hr />
                        </>
            )
        }
        else if (page == "Customer Document Center"){
            return (
                <>
                    <FNBTable data="Document Center Insigths" dates={dates} chartAPIParams={{}} />
                    <hr/>
                    <FNBTable data="Document Center Monthly Insigths" dates={dates} chartAPIParams={{}} />
                </>
            )
        }
            
    }
    
    
    return (
        <div>
            {/* <ReportHeaderComponent dates={dates} setDates={setDates} setCorBFilter={setCorBFilter} setPage={setPage} /> */}

            <SidebarLayout items={ReportHeaderComponent(dates,setDates,CorBFilter,setCorBFilter,setPage)} mainContent={getPage(showPage)}>

            </SidebarLayout>
            <div className="p-grid p-justify-center" style={{ minHeight: '70vh' }}>
                <div className="p-col-12" style={{ padding: '16px' }}>
                    
                    {}
                </div>
            </div>
            <ReportFooterComponent />
        </div>
    );
}

export default App;
