import React, { useState, useEffect } from 'react';
import 'primeicons/primeicons.css';
import 'primereact/resources/themes/nova/theme.css';
import 'primereact/resources/primereact.min.css';
import './primeflex.css';
import './Styles/App.css';
import './Styles/header.css';
import 'primereact/resources/primereact.css';
import 'primereact/resources/themes/lara-light-indigo/theme.css';

import ReportHeaderComponent from './Components/reportHeaderComponent';
import ReportLoginComponent from './Components/reportLoginComponent';
import AuthorizationService from './Services/AuthorizationService';
import { establishSsoSession } from './Services/msalInstance';
import ReportFooterComponent from './Components/reportFooterComponent';
import AnalyticsReportComponent from './Components/analyticsReportComponent';
import ChartCard from './Utils/Components/ChartCard';
import FNBLineChart from './Utils/Components/FNBLineChart';
import FNBReport from './Utils/Components/FNBReport';
import FNBTable from './Utils/Components/FNBTable';
import FNBMultiTable from './Utils/Components/FNBMultiTable';
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
import TransactionLogger from './Utils/Components/TransactionLogger';
import { Dropdown } from 'primereact/dropdown';
import ChartDataService from './Services/ChartDataService';
import CsvLoaderReportsTab from './Components/CsvLoaderReportsTab';
import CryptoRotationTab from './Components/CryptoRotationTab';

class PageErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error) {
        return { error };
    }

    componentDidUpdate(prevProps) {
        if (prevProps.resetKey !== this.props.resetKey && this.state.error) {
            this.setState({ error: null });
        }
    }

    componentDidCatch(error, errorInfo) {
        console.error('Page render error:', error, errorInfo);
    }

    render() {
        const { error } = this.state;
        if (error) {
            return (
                <div className="p-d-flex p-jc-center p-ai-center" style={{ minHeight: '60vh', padding: '24px' }}>
                    <div className="w3-container w3-card-4" style={{ width: '100%', maxWidth: '800px' }}>
                        <h2 className="w3-center">Unable to load {this.props.pageName || 'this page'}</h2>
                        <p>{error.message || 'An unexpected error occurred while rendering the page.'}</p>
                        <details style={{ whiteSpace: 'pre-wrap', marginTop: '16px' }}>
                            {error.stack}
                        </details>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}

function App() {
    const [ssoReady, setSsoReady] = useState(
        () => localStorage.getItem('login_method') !== 'msal'
    );

    useEffect(() => {
        if (ssoReady || localStorage.getItem('login_method') !== 'msal') return;
        let mounted = true;
        // Recover an existing Microsoft session before mounting chart requests.
        establishSsoSession().then(() => {
            if (mounted) setSsoReady(true);
        }).catch(() => {
            new AuthorizationService('', '').clearSession();
            if (mounted) setSsoReady(true);
        });
        return () => { mounted = false; };
    }, [ssoReady]);

    const [dates, setDates] = useState(() => {
        const today = new Date();
        const tonight = new Date(today.setHours(23, 59, 59, 999));
        
        const thirtyDaysAgoMorning = new Date(today);
        thirtyDaysAgoMorning.setUTCDate(thirtyDaysAgoMorning.getUTCDate() - 90);
        thirtyDaysAgoMorning.setUTCHours(0, 0, 0, 0);
        localStorage.setItem("start_date",thirtyDaysAgoMorning.toISOString().split('T')[0]);
        localStorage.setItem("end_date", tonight.toISOString().split('T')[0]);
        return [thirtyDaysAgoMorning, tonight];
      });
    const [CorBFilter, setCorBFilter] = useState("All");
    
    const [showPage, setPage] = useState("Customer Document Center");
    //const [showPage, setPage] = useState("All Filters Table");
    
    
    const [pageConfig, setPageConfig] = useState({
            "Abandonment Report Application Type": "All",
            "BOR Component Application Type": "All",
            "Monthly Report Product Type Selector": "All",
            "Business Deposit Report Application Type": "All",
        })

    useEffect(() => {
        localStorage.setItem("CorBFilter", CorBFilter);
        // Set page to "loading" temporarily to show loading state
        let pNow = showPage;
        setPage("loading");
        pageConfig["Direct Deposit Switch Current Total DDS Amount"] = null
        pageConfig["Direct Deposit Switch Total Number of Successful Switches"] = null
        setTimeout(() => {
            setPage(pNow);
        }, 1000);
    }, [CorBFilter]);

    useEffect(() => {
        // Set page to "loading" temporarily to show loading state
        let pNow = showPage;
        setPage("loading");
        setTimeout(() => {
            setPage(pNow);
        }, 1000);
    }, [pageConfig]);

    useEffect(() => {
        if (!dates || dates.length !== 2 || !dates[0] || !dates[1]) {   return; }
        localStorage.setItem("start_date", dates[0].toISOString().split('T')[0]);
        localStorage.setItem("end_date", dates[1].toISOString().split('T')[0]);
        let pNow = showPage;
        pageConfig["Direct Deposit Switch Current Total DDS Amount"] = null
        pageConfig["Direct Deposit Switch Total Number of Successful Switches"] = null
        setPage("loading");
        setTimeout(() => {
            setPage(pNow);
        }, 1000);
    }, [dates]);

    

    if (!new AuthorizationService('', '').isLoggedIn()) return <ReportLoginComponent />;
    if (!ssoReady) return <div role="status">Completing Microsoft sign-in...</div>;

    const getPage = (page) => {
        try {
            
        
            if (page === "Graphs") {
                return (<AnalyticsReportComponent pageConfig={pageConfig} setPageConfig={setPageConfig} />)
            }
            else if (page === "loading") {
                return (
                    <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                        <p>Loading...</p>
                    </div>
                );
            }
            else if (page === "BOR") {
                return (
                    <>
                        <div className="w3-container w3-card-4">



                            <h2 className="w3-center">In-Branch Originated Report</h2>
                            <BORAsync dates={dates} send_application_type_filter={(val)=>{
                                setPageConfig({...pageConfig,"BOR Component Application Type":val});
                            }} />
                            
                        </div>
                        <div className="w3-margin-top"><><hr /></></div>
                        <div className="w3-container w3-card-4 w3-margin-top"> 
                            <h3>Branch Originated Reports Monthly Analytics</h3>  
                            <div class="w3-third">
                                <FNBLineChart data="Branch Originated Reports Monthly Analytics Line" dates={dates} chartAPIParams={{variant:"Started", application_type: pageConfig["BOR Component Application Type"] }} showPointValues={true} />
                            </div>
                            <div class="w3-third">
                                <FNBLineChart data="Branch Originated Reports Monthly Analytics Line" dates={dates} chartAPIParams={{variant:"Submitted", application_type: pageConfig["BOR Component Application Type"]}} showPointValues={true} />
                            </div>
                            <div class="w3-third">
                                <FNBLineChart data="Branch Originated Reports Monthly Analytics Line" dates={dates} chartAPIParams={{variant:"Opened/Approved", application_type: pageConfig["BOR Component Application Type"]}} showPointValues={true} />
                            </div>
                        </div>
                    </>
                )
            }
            else if (page === "Business Deposit Reports") {

                return (
                    <>
                        <div className="w3-container w3-card-4">
                            <h2 className="w3-center">Business Deposit And Loan Reports</h2>
                            <BORAsync dates={dates} chartName='Business Deposit Reports' applicationTypeFilter={true} send_application_type_filter={(val)=>{
                                setPageConfig({...pageConfig,"Business Deposit Report Application Type":val});
                            }} />
                        </div>
                        <div className="w3-margin-top"><><hr /></></div>
                        <div className="w3-container w3-card-4 w3-margin-top">
                            <h3>Business Deposit And Loan Reports Monthly Analytics</h3>
                            <div class="w3-third">
                                <FNBLineChart data="Business Deposit Reports Monthly Analytics Line" dates={dates} chartAPIParams={{variant:"Started", application_type: pageConfig["Business Deposit Report Application Type"]}} showPointValues={true} />
                            </div>
                            <div class="w3-third">
                                <FNBLineChart data="Business Deposit Reports Monthly Analytics Line" dates={dates} chartAPIParams={{variant:"Submitted", application_type: pageConfig["Business Deposit Report Application Type"]}} showPointValues={true} />
                            </div>
                            <div class="w3-third">
                                <FNBLineChart data="Business Deposit Reports Monthly Analytics Line" dates={dates} chartAPIParams={{variant:"Opened/Approved", application_type: pageConfig["Business Deposit Report Application Type"]}} showPointValues={true} />
                            </div>
                        </div>
                    </>
                )
            }
            else if (page === "Multi Product Reports") {
                return (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap:'16px', padding: '16px' }}  >
                    <ChartCard title={"Top 10 Multi-Product Combinations"}
                        styleNow={{"width":"99%"}}
                        items={(
                            <div className="p-grid">
                                <FNBBarChart data={"Multi Products Product Set Id Bar"} />
                                <FNBDataTable data={"Multi Products Product Set Id Table"} />
                            </div>
                        )}
                    />
                    <CardReport CHART_NAME="Multi Products Daily Product Set Id Insights"/>
                    <ChartCard title={"Multi-Product Combinations By Month"}
                        styleNow={{"width":"99%"}}
                        items={(
                            <div className="p-grid">
                                <div class="w3-half">
                                    <FNBLineChart data={"Monthly Multi Product Reports Line"} showPointValues={true} chartAPIParams={{stat_type:"Opened / Approved"}}/>
                                </div>
                                <div class="w3-half">
                                    <FNBLineChart data={"Monthly Multi Product Reports Line"} showPointValues={true} chartAPIParams={{stat_type:"Submitted"}}/>
                                </div>
                            </div>
                        )}
                    />



                </div>)

            }
            else if (page === "Cross Sell Reports") {
                return (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap:'16px', padding: '16px' }}  >
                    
                    <ChartCard title={"Top 10 Single product with Cross Sell Products"}
                        styleNow={{"width":"99%"}}
                        items={(
                            <div className="p-grid ">
                                <FNBBarChart data={"Top 10 Single product with Cross Sell Products Bar"} />
                                <FNBDataTable data={"Top 10 Single product with Cross Sell Products Table"}  />
                            </div>
                        )}
                    />
                    
                    <ChartCard title={"Top 10 Multi Cross Sell Products"}
                        styleNow={{"width":"99%"}}
                        items={(
                            <div className="p-grid ">
                                <FNBBarChart data={"Multi Products Cross Sell Bar"} />
                                <FNBDataTable data={"Multi Products Cross Sell Table"} />
                            </div>
                        )}
                    />

                    <hr/>
                    
                    <h3>Cross Sell Products - Presented and Accepted</h3>
                    
                    <div className={"w3-container w3-cetner "} style={{width:"100%"}} >
                        
                        <div class="w3-third">
                            <ChartCard title={"All Apps"}
                            styleNow={{"width":"99%"}}
                            items={(
                                <>
                                    <FNBBarWithLineChart data="Cross Sell Products Presented and Accepted Line" dates={dates} chartAPIParams={{show_line: true, "type":"all"}} />
                                    <FNBTable data={"Cross Sell Products Presented and Accepted Table"} dates={dates} chartAPIParams={{"type":"all"}} />
                                </>
                            )} />
                        </div>
                        
                        <div class="w3-third">
                            <ChartCard title={"Submitted Apps"}
                                styleNow={{"width":"99%"}}
                                items={(
                                    <>
                                        <FNBBarWithLineChart data="Cross Sell Products Presented and Accepted Line" dates={dates} chartAPIParams={{show_line: true, "type":"submitted"}} />
                                        <FNBTable data={"Cross Sell Products Presented and Accepted Table"} dates={dates} chartAPIParams={{"type":"submitted"}} />
                                    </>
                                )} />
                        </div>
                        <div class="w3-third">
                            <ChartCard title={"Opened/Approved Apps"}
                                styleNow={{"width":"99%"}}
                                items={(
                                    <>
                                        <FNBBarWithLineChart data="Cross Sell Products Presented and Accepted Line" dates={dates} chartAPIParams={{show_line: true, "type":"opened/approved"}} />
                                        <FNBTable data={"Cross Sell Products Presented and Accepted Table"} dates={dates} chartAPIParams={{"type":"opened/approved"}} />
                                    </>
                                )} />
                        </div>
                    </div>

                                    
                    
                    
                </div>)

            }
            else if (page === "New vs Exisitng Customers"){
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
                                                <FNBLineChart data={"Declined Report Line"} chartAPIParams={{}} />
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
                        
                    <CardReport CHART_NAME={"All Bot Deduped Data Monthly Insights"} title={"All Bot Deduped Data"} />
                        <FNBDataTable data="All Transactions" extraParams={{showComma:"false"}} />
                    </>
                )
            }
            else if (page === "Transaction Logger") {
                return (
                    <TransactionLogger dates={dates} />
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
                                                <FNBBarChart data={"Abandonment Report by Year Pie"} chartAPIParams={{ showComma:"false",
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
                    <FNBMultiTable data="Lending And Deposit Reports" dates={dates} columnWidth={200} />
                )
            }
            else if (page === "Funding Type Report") {
                return(
                            <>
                                    <ChartCard title="Funding Type Report"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                <FNBLineChart data={"Funding Type Report Line"} chartAPIParams={{}} />
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
            else if (page === "All Filters Table"){
                return (
                    <>
                        <MultiFilterTable extraParams={{showComma:"false"}} />
                    </>
                )
            }
            else if(page === "Spot And Current Balance Amounts"){
                return (
                    <>
                        <CardReport CHART_NAME={"Spot And Current Balance Account Insights"} title={"Spot And Current Balance Account Insights"} />
                        
                                
                                <h2>Common App</h2>
                                <h3>Opening Deposit (Spot) Amount</h3>
                                            <FNBStackedBarChart chartAPIParams={{
                                                what_column_to_add : "Initial_Deposit",
                                                application_type: "Online",
                                            }} dates={dates}  data={"Spot And Current Balance Account Stacked Chart"} />
                                <h3>Current Balance Amount</h3>
                                            <FNBStackedBarChart chartAPIParams={{
                                                what_column_to_add : "Current_Balance",
                                                application_type: "Online",
                                            }} dates={dates}  data={"Spot And Current Balance Account Stacked Chart"} />



                                <h2>In Branch</h2>
                                <h3>Opening Deposit (Spot) Amount</h3>
                                            <FNBStackedBarChart chartAPIParams={{
                                                what_column_to_add : "Initial_Deposit",
                                                application_type: "Banker Assisted",
                                            }} dates={dates}  data={"Spot And Current Balance Account Stacked Chart"} />

                                <h3>Current Balance Amount</h3>
                                <FNBStackedBarChart chartAPIParams={{
                                    what_column_to_add : "Current_Balance",
                                    application_type: "Banker Assisted",
                                }} dates={dates}  data={"Spot And Current Balance Account Stacked Chart"} />


                                <h3> Monthly Opening And Current Balance Table </h3>
                                <FNBTable data="Monthly Opening And Current Balance Table" dates={dates} chartAPIParams={{}} />
                    </>
                )
            }
            else if (page === "Loan Commitments"){
                const AppTypeNow = pageConfig["Loan Commitments Application Type Selector"];
                const heading_suffix = AppTypeNow && typeof(AppTypeNow) !== "object" ? " (" + AppTypeNow + ")" : ""
                return (
                    <>

                        <Dropdown
                            value={AppTypeNow}
                            onChange={(e) => setPageConfig({
                                ...pageConfig,
                                "Loan Commitments Application Type Selector": e.value
                            })}
                            options={[
                                { label: 'All', value: null },
                                { label: 'Online', value: 'Online' },
                                { label: 'Banker Assisted', value: 'Banker Assisted' },
                            ]}
                            placeholder="Select an App Type"
                            />




                        <CardReport
                            CHART_NAME={"Loan Commitment Insights" }
                            params={{ BranchID: 'All', start_date: localStorage.getItem('start_date'), end_date: localStorage.getItem('end_date'), application_type:AppTypeNow }}
                            title={"Loan Accounts and Commitment($) Report" + heading_suffix}
                            renderOrder={['Started', 'Submitted', 'Opened/Approved']}
                            />
                        <ChartCard title={"Loan Account and Commitment($) - Quarterly Analysis"  + heading_suffix }
                        styleNow={{ width: '99%' }}
                        items={(
                                <>
                                    <FlipCard title={"Loan Accounts and Commitments($)" + heading_suffix}
                                    styleNow={{"width":"100%"}}
                                    itemFront={(
                                    <>
                                    <FNBBarWithLineChart data="Loan Commitment Bar And Line" dates={dates} chartAPIParams={{show_line: true, application_type:AppTypeNow}} />
                                    
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
                                            sideByside:true,
                                            application_type:AppTypeNow
                                        }} 
                                    />
                                    </>
                                    )}
                                    />
                                    <FNBTable data="Loan Commitment Stacked Table" dates={dates} chartAPIParams={{send_avg:true, application_type:AppTypeNow}} />  
                                </>
                            )}
                        />
                        
                        <ChartCard title={"Loan Account and Commitment($) - Secured (vs) Unsecured Loans"  + heading_suffix }
                        styleNow={{ width: '99%' }}
                        items={(
                                <>
                                    <FNBStackedBarChart dates={dates}  data={"Loan Commitment Stacked Bar"} chartAPIParams={{application_type:AppTypeNow}} />
                                    <FNBTable data="Loan Commitment Stacked Table" dates={dates} subHeaderRow={
                                                    FUNDING_TYPE_IN_MILLION_SUBHEADER
                                                } chartAPIParams={{send_sec_unsec:true,send_total:true,application_type:AppTypeNow}} />   
                                </>
                            )}
                        />
                    </>

                    
                )
            }
            else if (page === "Monthly Report") {
                {
                    
                    var start_date = new Date();
                    var thisYear = start_date.getFullYear();
                    var lastYear = thisYear - 1;
                    start_date = lastYear + "-01-01";
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
                                        { label: 'All Applications', value: 'All' },
                                        { label: 'All Products', value: 'Products' },
                                        { label: 'Loan Products', value: 'Loan Products' },
                                        { label: 'Mixed Products', value: 'Mixed Products' },
                                        { label: 'Deposit Products', value: 'Deposit Products' }
                                    ]}
                                    placeholder="Select a Variant"
                                    />
                                    
                                    <ChartCard title="Common App In Branch and Consumer Facing Report"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                
                                                <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Common App In Branch and Consumer Facing Report"} data="Common App In Branch and Consumer Facing Report" dates={dates}  chartAPIParams={{
                                                    start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]
                                                }} freezeStyle={"left"} />
                                            </div>
                                        )}
                                    />


                                    <ChartCard title="Common App (In Branch)"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                
                                                <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Common App (In Branch)"} data="Monthly In Branch Report" dates={dates} chartAPIParams={{
                                                    start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]
                                                }} freezeStyle={'left'}  />
                                            </div>
                                        )}
                                    />
                                    <ChartCard title="Common App (Consumer-Facing)"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Common App (Consumer-Facing)"} data="Monthly Consumer Facing Report" dates={dates} chartAPIParams={{start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]}}  freezeStyle={'left'}  />
                                            </div>
                                        )}
                                    />
                                    <ChartCard title="Business Deposits and Loans Report"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                <FNBTable key={pageConfig["Monthly Report Product Type Selector"]+" Business Deposits"} data="Monthly Business Deposits And Loans Report" dates={dates} chartAPIParams={{start_date, end_date, monthlyReportProductTypeSelector: pageConfig["Monthly Report Product Type Selector"]}}  freezeStyle={'left'}  />
                                            </div>
                                        )}
                                    />
                                    {/* <ChartCard title="In Branch BPM/CRIF Entered"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                <FNBTable data="Monthly BPM and CRIF Report" dates={dates} chartAPIParams={{start_date,end_date}}  freezeStyle={'left'}  />
                                            </div>
                                        )}
                                    />
                                    <ChartCard title="In Branch - eCA vs. BPM/CRIF - %eCA Store Common App vs. % BPM/CRIF App "
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <div className="p-grid p-justify-center">
                                                <FNBTable data="Monthly In Branch vs BPM and CRIF Report" dates={dates}  chartAPIParams={{start_date,end_date}}  freezeStyle={'left'}  />
                                            </div>
                                        )}
                                    /> */}
                                <hr />
                            </>
                )
            }
            else if (page === "Customer Document Center"){
                const documentCenterEndDate = new Date();
                const documentCenterRightStartDate = new Date(documentCenterEndDate);
                documentCenterRightStartDate.setMonth(documentCenterRightStartDate.getMonth() - 12);
                const documentCenterLeftStartDate = new Date(documentCenterRightStartDate);
                documentCenterLeftStartDate.setMonth(documentCenterLeftStartDate.getMonth() - 12);
                const formatDocumentCenterDate = (date) => date.toISOString().slice(0, 10);
                var start_date_for_left_graph = formatDocumentCenterDate(documentCenterLeftStartDate);
                var end_date_for_left_graph = formatDocumentCenterDate(documentCenterRightStartDate);
                var start_date_for_right_graph = formatDocumentCenterDate(documentCenterRightStartDate);
                var end_date_for_right_graph = formatDocumentCenterDate(documentCenterEndDate);
                return (
                    <>
                        <FNBTable data="Document Center Insigths" dates={dates} chartAPIParams={{
                            start_date_for_left_graph, end_date_for_left_graph,
                            start_date_for_right_graph, end_date_for_right_graph
                        }} />
                        <hr/>
                        <h3>Monthly Document Center Upload Stats</h3>
                        <FNBTable data="Document Center Monthly Insigths" dates={dates} chartAPIParams={{
                            start_date: start_date_for_left_graph,
                            end_date: end_date_for_right_graph
                        }} />
                        
                        <div class="w3-half">
                            <FNBBarWithLineChart data="Document Center Monthly Insigths Line" dates={dates} chartAPIParams={{start_date:start_date_for_left_graph, end_date:end_date_for_left_graph}}  showPointValues={true} dont_show_for_index={[0]} />
                        </div>
                        <div class="w3-half">
                            <FNBBarWithLineChart data="Document Center Monthly Insigths Line" dates={dates} chartAPIParams={{start_date:start_date_for_right_graph, end_date:end_date_for_right_graph}} showPointValues={true}  dont_show_for_index={[0]} />
                        </div>
                        <div class="w3-half">
                            <CardReport CHART_NAME={"Shot Clock Application Reports Insights"} />
                        </div>
                        
                    </>
                )
            }
            else if (page === "Key Rotation") {
                return <CryptoRotationTab />;
            }
            else if (page === "CSV Loader Reports") {
                return <CsvLoaderReportsTab />;
            }
            else if (page === "Direct Deposit Switch"){
                var cds = new ChartDataService("Current Total DDS Amount and Switches Insights", {});
                if( pageConfig["Direct Deposit Switch Current Total DDS Amount"] === null || pageConfig["Direct Deposit Switch Total Number of Successful Switches"] === null){                
                    cds.getChart().then((resolvedData) => {
                        setPageConfig({...pageConfig, 
                        "Direct Deposit Switch Current Total DDS Amount": resolvedData["Current Total DDS Amount"],
                        "Direct Deposit Switch Total Number of Successful Switches": resolvedData["Total Number of Successful Switches"]
                        });
                    });
                }
                
                return (
                    <>
                        <CardReport CHART_NAME={"Direct Deposit Switch Reports Insights"} title={"Direct Deposit Switch Reports Insights - eSTORE COMMON APP"} />
                        
                        <FNBDataTable data={"Direct Deposit Switch Reports Table"} chartAPIParams={{}} />
                        <h3> Current Total DDS Amount: {pageConfig["Direct Deposit Switch Current Total DDS Amount"]}
                            &nbsp;&&nbsp;
                            {pageConfig["Direct Deposit Switch Total Number of Successful Switches"]} Successful Switches
                        </h3>
                    </>
                )
            }
            else if (page === "Bot Generated Reports"){
                return (
                    <>
                        <CardReport CHART_NAME={"Bot Generated Reports Insights"} title={"Bot Generated Reports Insights"} />
                        <CardReport CHART_NAME={"Bot Generated Reports Monthly Insights"} title={"Bot Generated Reports Monthly Insights"} />
                    </>
                )
            }
            else if (page === "Payment Switch Reports"){
                return (
                    <>
                        <CardReport CHART_NAME={"Payment Switch Insights"} title={"Payment Switch Insights"} />
                    </>
                )
            }
            else if (page === "E-Delivery Report"){
                return (
                    <>
                        <CardReport CHART_NAME={"E-Delivery Report Insights"} title={"E-Delivery Report Insights"} />
                    </>
                )
            }
            else if (page === "Student Checking Report"){
                return (
                    <>
                        <CardReport CHART_NAME="Student Checking Report Insights" />
                        <FNBDataTable data="Student Checking Monthly Report Table" dates={dates}/>
                        
                    </>
                )
            }
            else if (page === "Business Accounts Summary"){
                var start_date_now = new Date().getFullYear()-1 + '-01-01'
                var end_date_now = new Date().toISOString().slice(0,10)
                setInterval(() => {
                    let list = document.getElementsByClassName("greyed_out"); 
                    for (let i = 0; i < list.length; i++) {
                        list[i].parentElement.parentElement.style.backgroundColor = '#eee';
                    }
                }, 5000)
                return(
                    <>
                    <h1 className="w3-center">Business Accounts Summary</h1>
                    <ChartCard title="Number Of Applications by Product Type"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <FNBTable data="Business Account Summary Number Of Apps Table" dates={dates} chartAPIParams={{
                                                start_date_now, end_date_now
                                            }} freezeStyle={'left'} />
                                        )}
                                    />
                        <ChartCard title="Top 10 Products"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <FNBTable data="Business Account Summary Top 10 Products Table" dates={dates} chartAPIParams={{
                                                    start_date_now, end_date_now, showComma:"false"
                                                }} freezeStyle={'left'} />
                                        )}
                                    />

                        <ChartCard title="Top 10 Branches"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <FNBTable data="Business Account Summary Top 10 Branches Table" dates={dates} chartAPIParams={{
                                                    start_date_now, end_date_now, showComma:"false"
                                                }} freezeStyle={'left'} />
                                        )}
                                    />
                        <ChartCard title="Current Balance and Initial Deposit Table"
                                        styleNow={{"width":"100%"}}
                                        items={(
                                            <FNBTable data="Business Account Summary Current Balance and Initial Deposit Table" dates={dates} chartAPIParams={{
                                                    start_date_now, end_date_now, showComma:"true"
                                                }} freezeStyle={'left'} />
                                        )}
                                    />

                        

                    </>
                )
            }
            else if (page === "E Delivery Report LOB"){
                return (
                    <FNBTable data="E Delivery Report LOB Table" dates={dates} chartAPIParams={{}} />
                )
            }
            else if (page === "PennState University Banking Reports"){
                return (
                    <>
                        <CardReport CHART_NAME={"PennState Branch Report Insights"} renderOrder={['Started', 'Submitted', 'Opened/Approved']} />
                        <CardReport CHART_NAME={"PennState Student Banking Reports Insights"} renderOrder={['Started', 'Submitted', 'Opened/Approved']} />
                        <div  className="w3-third">
                            <FNBLineChart data="PennState Student Banking Reports Line" dates={dates} chartAPIParams={{"variant":"Started"}} showPointValues={true} />
                        </div>
                        <div  className="w3-third">
                            <FNBLineChart data="PennState Student Banking Reports Line" dates={dates} chartAPIParams={{"variant":"Submitted"}} showPointValues={true} />
                        </div>
                        <div  className="w3-third">
                            <FNBLineChart data="PennState Student Banking Reports Line" dates={dates} chartAPIParams={{"variant":"Opened/Approved"}} showPointValues={true} />
                        </div>
                    </>
                )
            }

            
        } catch (error) {
            return (
                <div className="w3-container w3-card-4">
                    <h2 className="w3-center">Error Loading {page} Report</h2>
                    <p>{error.message}</p>
                </div>
            )    
        }
    }
    
    
    return (
        <div>
            {/* <ReportHeaderComponent dates={dates} setDates={setDates} setCorBFilter={setCorBFilter} setPage={setPage} /> */}

            <SidebarLayout
                items={ReportHeaderComponent(dates, setDates, CorBFilter, setCorBFilter, setPage)}
                mainContent={
                    <PageErrorBoundary resetKey={showPage} pageName={showPage}>
                        {getPage(showPage)}
                    </PageErrorBoundary>
                }
                pageToShow={showPage}
            >

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
