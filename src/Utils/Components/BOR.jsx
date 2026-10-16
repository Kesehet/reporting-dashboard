import React, { useState, useRef, useEffect } from 'react';
import { Accordion, AccordionTab } from 'primereact/accordion';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { MultiSelect } from 'primereact/multiselect';
import ChartDataService from '../../Services/ChartDataService';
import BorAccordion from './BorAccordion';
import { Dropdown } from 'primereact/dropdown';
import ReportActions from './ReportActions';

export default function BOR({dates, chartName, applicationTypeFilter=false}) {
    const [chartData, setChartData] = useState(null);
    const toast = useRef(null);
    const [selectedBranches, setSelectedBranches] = useState(["All"]);
    const [loading, setLoading] = useState(false);
    const [application_type, setApplication_type] = useState("All"); // Banker Assisted or Online

    const fetchData = async () => {
        if (loading) {
            return;
        }
        setChartData(null);
        setLoading(true);

        try {
            // Fetch all branch IDs first
            const trackingCode = (chartName && chartName.search("Originated")) ? "B-%25" : "C-%25";
            var app = "%25"; // Default to all applications
            if (application_type && application_type !== "All") {
                app = application_type;
            }
            if  (chartName && chartName.search("Originated")) {
                app = "Banker Assisted";
            }
            const chartDataServiceA = new ChartDataService("All Branch Ids", { "eCATrackingCode": trackingCode, "application_type": app });
            const allBranchesData = await chartDataServiceA.getChart();
            let branchIDs = [];
            if (allBranchesData && allBranchesData.rows && allBranchesData.rows.length > 0) {
                branchIDs = allBranchesData.rows.map(row => row);
                
                // Remove duplicates and filter out empty values
                branchIDs = Array.from(new Set(branchIDs)).filter(id => id && id.trim() !== "");
                if (branchIDs.length > 0) {
                    // If "All" is not in the list, add it
                    if (!branchIDs.includes("All")) {
                        branchIDs.unshift("All");
                    }
                    setSelectedBranches(branchIDs);
                } else {
                    setSelectedBranches(["All"]);
                }
            } else {
                setSelectedBranches(["All"]);
            }

            // Now fetch data for each branch ID one by one
            let allRows = [];
            let headers = null;
            let ctr = 0;
            for (const branchID of branchIDs.length ? branchIDs : ["All"]) {
                const chartDataService = new ChartDataService(chartName ?? "Branch Originated Reports", { "BranchID": branchID, "application_type": application_type });
                setLoading(ctr);
                ctr++;
                // eslint-disable-next-line no-await-in-loop
                const data = await chartDataService.getChart();
                if (data && data.rows && data.rows.length > 0) {
                    if (!headers) headers = data.headers;
                    allRows = allRows.concat(data.rows.map(row => ({ ...row, BranchID: branchID })));
                }
            }
            setSelectedBranches(["All"]);
            setChartData({ headers, rows: allRows });
        } catch (error) {
            console.error("Error fetching branch data:", error);
            setSelectedBranches(["All"]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!dates || dates[0] === null || dates[1] === null) {
            return; // Exit early if dates are invalid
        }
        const timeout = setTimeout(() => {
            fetchData();
        }, 2500);

        return () => clearTimeout(timeout);
    }, [dates, chartName, application_type]);

    if (!chartData) {
        return (
            <div className="flex flex-column justify-content-center align-items-center" style={{ minHeight: '120px' }}>
            <i className="pi pi-spin pi-spinner" style={{ fontSize: '2rem' }}></i>
            <div className="ml-2 mt-2">Loading {loading}/{selectedBranches.length} branches...</div>
            <div style={{ width: 250, marginTop: 12 }}>
                <div className="p-progressbar p-component" style={{ height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
                <div
                    className="p-progressbar-value"
                    style={{
                    width: `${selectedBranches.length > 0 ? Math.min((loading / selectedBranches.length) * 100, 100) : 0}%`,
                    background: '#2196f3',
                    height: '100%',
                    transition: 'width 0.3s'
                    }}
                />
                </div>
            </div>
            </div>
        );
    }

    const { headers, rows } = chartData;

    const branchOptions = rows
        ? Array.from(new Set(rows.map((row) => row.BranchID))).map((BranchID) => ({
              label: `${BranchID} ${BranchID === "All" ? "Branches" : "Branch"}`,
              value: BranchID,
          }))
        : [];

    const filteredRows = selectedBranches.length
        ? rows.filter((row) => selectedBranches.includes(row.BranchID))
        : rows;

    const handleBranchSelection = (selected) => {
        // if last item is "All", remove all other selections
        if (selected[selected.length - 1] === "All") {
            selected = ["All"];
        } else if (selected.includes("All")) {
            selected = selected.filter((branch) => branch !== "All");
        }
        // if no branches are selected, set to "All"
        if (selected.length === 0) {
            selected = ["All"];
        }
        setSelectedBranches(selected);
    };

    const renderAccordionContent = (data) => {
        const customOrder = ["Date", "Total-Started", "Total-Submitted", "Total-Opened/Approved", "Grand-Total"]; // Define your custom order here
        const orderedKeys = customOrder.concat(
            Object.keys(data).filter((key) => !customOrder.includes(key))
        );

        return (
            <div className="p-3">
            <div className="flex flex-wrap gap-3">
                {orderedKeys.map((key, index) => {
                if (key.startsWith('_report_') || data[key] === "All") return null;
                if ( key === "Start-Date"||  key === "End-Date") return null;
                if (key.includes("[") || key.includes("]")) return null;

                return (
                    <div
                    key={index}
                    className="p-card p-component p-mb-3"
                    style={{
                        width: '250px',
                        padding: '1rem',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                        borderRadius: '8px',
                        backgroundColor: '#f9f9f9',
                    }}
                    >
                    <div className="p-card-header" style={{ marginBottom: '0.5rem' }}>
                        <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#333' }}>{key}</h4>
                    </div>

                    <div className="p-card-body">
                        <p style={{ margin: 0, fontSize: '0.95rem', color: '#555' }}>
                            {key === "Date" ? (
                                <>
                                    {data["Start-Date"]} <br /> {"To"} <br /> {data["End-Date"]}
                                </>
                            ) : (
                                <>
                                    <></>Total: {data[key]}
                                    <br />
                                    {key === "Grand-Total" ? null : (
                                        <>
                                            <br />
                                            {key === "BranchID" ? null : (
                                                <>
                                                    <b>Lending Apps:</b> {data[key + "-[Lending]"]}
                                                    <br />
                                                    <b>Deposit Apps:</b> {data[key + "-[Deposit]"]}
                                                    <br />
                                                    <b>Mixed Apps:</b> {data[key + "-[Mixed]"]}
                                                    <br />
                                                    <b>Multi Apps:</b> {data[key + "-[Multi]"]}
                                                    <br />
                                                    <b>Single Apps:</b> {data[key + "-[Single]"]}
                                                    <br />
                                                </>
                                            )}
                                        </>
                                    )}
                                </>
                            )}
                        </p>
                    </div>
                    {data["_report_" + key] && (
                        <>
                        <ReportActions
                            report={data["_report_" + key]}
                            filename={key + " " + data["Date"] + '.csv'}
                            dialogHeader={key + " Details"}
                        />
                        </>
                    )}
                    </div>
                );
                })}
            </div>
            </div>
        );
    };

    return (
        <div className="" >
            {applicationTypeDropDown()}
            <Toast ref={toast} />
            <div className="flex flex-wrap justify-content-end gap-2 mb-3">
                <MultiSelect
                    value={selectedBranches}
                    options={branchOptions}
                    onChange={(e) => handleBranchSelection(e.value)}
                    placeholder="Filter by Branch"
                    className="p-mr-2"
                    style={{maxWidth: '200px'}}
                />
                <Button icon="pi pi-refresh" label="Refresh" onClick={fetchData} text />
            </div>
            <div>
                {filteredRows.map((row, index) => {
                    // Remove BranchID from the row before passing to renderAccordionContent
                    const { BranchID, ...rowWithoutBranchID } = row;
                    return (
                        <BorAccordion
                            tab={{
                                header: BranchID + (BranchID === "All" ? " Branches" : " Branch"),
                                content: renderAccordionContent(rowWithoutBranchID)
                            }}
                            key={index}
                            show={filteredRows.length < 2}
                            hardShow={filteredRows.length === 1}
                        />
                    );
                })}
            </div>
        </div>
    );

    function applicationTypeDropDown(){
        if(!applicationTypeFilter){return}
        return (<Dropdown
                            value={application_type}
                            options={[
                                { label: "All", value: "All" },
                                { label: "Banker Assisted", value: "Banker Assisted" },
                                { label: "Online", value: "Online" }
                            ]}
                            onChange={(e) => { 
                                alert("Application Type changed to " + e.value);
                                setApplication_type(e.value);  
                                
                            }}
                            placeholder="Select Application Type"
                            style={{ width: '200px', height: '40px', marginBottom: '1rem' }}
                        />)
    }
}
