import React, { useState, useRef, useEffect } from 'react';
import { Accordion, AccordionTab } from 'primereact/accordion';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { MultiSelect } from 'primereact/multiselect';
import ChartDataService from '../../Services/ChartDataService';
import { Dialog } from 'primereact/dialog';
import { DataTable } from 'primereact/datatable';
import BorAccordion from './BorAccordion';
import { ToggleButton } from 'primereact/togglebutton';
import { Dropdown } from 'primereact/dropdown';
import CellDataService from '../../Services/CellDataService';
import getCellData from './Utils';

export default function FNBReport({dates, CHART_NAME="Abandonment Report", renderAccordionContentOrder=[], SingularOrPlural=["Report","Reports"], idName="BranchID",
    globalSettingSetter= null, globalSettings = {}
    }) {
    const [chartData, setChartData] = useState(null);
    const toast = useRef(null);
    const [dialogVisible, setDialogVisible] = useState(false);
    const [dialogData, setDialogData] = useState(null);
    const [selectedBranches, setSelectedBranches] = useState(["All"]);
    const [loading, setLoading] = useState(false);
    const [progress, setProgress] = useState(0); // <-- Add progress state
    const [application_type, setApplication_type] = useState("All"); // Banker Assisted or Online

    const fetchData = async () => {
        if (loading) {
            return;
        }
        setChartData(null);
        setDialogData(null);
        setDialogVisible(false);
        setLoading(true);
        setProgress(0); // <-- Reset progress

        try {
            // Fetch all branch IDs first
            const chartDataServiceA = new ChartDataService("All Branch Ids");
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
            const totalBranches = branchIDs.length ? branchIDs.length : 1;
            for (const branchID of branchIDs.length ? branchIDs : ["All"]) {
                const chartDataService = new ChartDataService(CHART_NAME, { [idName]: branchID, "application_type": application_type, start_date: localStorage.getItem('start_date'), end_date: localStorage.getItem('end_date') });
                setProgress(ctr); // <-- Update progress
                ctr++;
                // eslint-disable-next-line no-await-in-loop
                const data = await chartDataService.getChart();
                if (data && data.rows && data.rows.length > 0) {
                    if (!headers) headers = data.headers;
                    allRows = allRows.concat(data.rows.map(row => ({ ...row, [idName]: branchID })));
                }
            }
            setProgress(branchIDs.length); // <-- Set progress to max at end
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
    }, [dates, application_type]);

    if (!chartData) {
        return (
            <div className="flex flex-column justify-content-center align-items-center" style={{ minHeight: '120px' }}>
            <Dropdown
                    value={application_type}
                    options={[
                        { label: "All", value: "All" },
                        { label: "Banker Assisted", value: "Banker Assisted" },
                        { label: "Online", value: "Online" }
                    ]}
                    onChange={(e) => {
                        let newSetting = {...globalSettings, "Abandonment Report Application Type": e.value};

                        if (globalSettingSetter) {
                            globalSettingSetter(newSetting);
                        }
                        setApplication_type(e.value);
                        console.log(e.value)
                    }}
                    placeholder="Select Application Type"
                    style={{ width: '200px', height: '40px', marginBottom: '1rem' }}
                />
            <i className="pi pi-spin pi-spinner" style={{ fontSize: '2rem' }}></i>
            <div className="ml-2 mt-2">
                Loading {progress}/{selectedBranches.length} branches...
            </div>
            <div style={{ width: 250, marginTop: 12 }}>
                <div className="p-progressbar p-component" style={{ height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
                <div
                    className="p-progressbar-value"
                    style={{
                    width: `${selectedBranches.length > 0 ? Math.min((progress / selectedBranches.length) * 100, 100) : 0}%`,
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
        ? Array.from(new Set(rows.map((row) => row[idName]))).map((mainId) => ({
              label: `${mainId} ${mainId == "All" ? SingularOrPlural[1] : SingularOrPlural[0]}`,
              value: mainId,
          }))
        : [];

    const filteredRows = selectedBranches.length
        ? rows.filter((row) => selectedBranches.includes(row[idName]))
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

    const showDialogWithData = (data) => {
        getCellData(data).then((resolvedData) => {
            setDialogData(resolvedData);
            setDialogVisible(true);
        });
    };


    const dialogFooter = (
        <div>
            <Button label="Close" icon="pi pi-times" onClick={() => setDialogVisible(false)} />
        </div>
    );

    const renderAccordionContent = (data) => {
        const customOrder = renderAccordionContentOrder || []
        const orderedKeys = customOrder.concat(
            Object.keys(data).filter((key) => !customOrder.includes(key))
        );

        return (
            <div className="p-3">
            <div className="flex flex-wrap gap-3">
                {orderedKeys.map((key, index) => {
                if (key.startsWith('_report_') || data[key] == "All") return null;
                if ( key == "Start-Date"||  key == "End-Date") return null;
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
                                <CellDataService query={data[key]} />
                            )}
                        </p>
                    </div>
                    {data["_report_" + key] && (
                        <>
                        <Button
                            icon="pi pi-file"
                            label="Export"
                            onClick={() => exportRowAsCSV(data["_report_" + key], key + " " + data["Date"] + '.csv')}
                            className="p-button-text"
                        />
                        <Button
                            icon="pi pi-eye"
                            label="View"
                            onClick={() => showDialogWithData(data["_report_" + key])}
                            className="p-button-text"
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
            <Toast ref={toast} />
            <div className="flex flex-wrap justify-content-end gap-2 mb-3">
                <Dropdown
                    value={application_type}
                    options={[
                        { label: "All", value: "All" },
                        { label: "Banker Assisted", value: "Banker Assisted" },
                        { label: "Online", value: "Online" }
                    ]}
                    onChange={(e) => { 
                        let newSetting = {...globalSettings, "Abandonment Report Application Type": e.value};

                        if (globalSettingSetter) {
                            globalSettingSetter(newSetting);
                        }
                        setApplication_type(e.value);  
                    }}
                    placeholder="Select Application Type"
                    style={{ width: '200px', height: '40px', marginBottom: '1rem' }}
                />
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
                {filteredRows.map((row, index) => (
                    <BorAccordion tab={{header:row.BranchID + (row.BranchID == "All"? " Branches" : " Branch"),content:renderAccordionContent(row)}} 
                    key={index} 
                    show={(filteredRows.length < 2)}
                    hardShow ={(filteredRows.length == 1)}
                    />
                ))}
            </div>
            <Dialog
                header="Detailed Data"
                visible={dialogVisible}
                style={{ width: '100vw', height: '100vh', margin: '0 auto' }}
                onHide={() => setDialogVisible(false)}
                footer={dialogFooter}
                maximizable
            >
                {dialogData && dialogData.length > 0 ? (
                    <DataTable value={dialogData} paginator rows={10} className="p-datatable-responsive p-datatable-sm">
                        <DataTable.Column field="Date" header="Date" sortable />
                        {Object.keys(dialogData[0]).map((key, index) => {
                            if (key === "Date") return null;
                            return <DataTable.Column key={index} field={key} header={key} sortable />;
                        })}
                    </DataTable>
                ) : dialogData && dialogData.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '2rem' }}>
                        <p>No data available for this branch</p>
                    </div>
                ) : (
                    <div style={{ textAlign: 'center', padding: '2rem' }}>
                        <p>No data to display</p>
                    </div>
                )}
            </Dialog>
        </div>
    );

    async function exportRowAsCSV(rowData, filename = 'exported_data.csv') {
        rowData = await getCellData(rowData);
        const csvContent = rowData
            .map((row) =>
                Object.keys(row)
                    .map((key) => `"${row[key]}"`)
                    .join(',')
            )
            .join('\n');
        const headers = Object.keys(rowData[0]).join(',');
        const fullCsvContent = `${headers}\n${csvContent}`;
        const blob = new Blob([fullCsvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
}
