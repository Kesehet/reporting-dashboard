import React, { useState, useRef, useEffect } from 'react';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { MultiSelect } from 'primereact/multiselect';
import { Dialog } from 'primereact/dialog';
import { DataTable } from 'primereact/datatable';
import BorAccordion from './BorAccordion'; // Consider renaming this to a generic Accordion if needed
import ChartDataService from '../../Services/ChartDataService';
// the data thats comes into the Business Deposit Report must be filtered for the eca tracking code - where we consider only B- codes
/**
 * FNBTileSet - A generic tile set component for displaying data in tiles with filtering and export.
 * 
 * Props:
 * - dates: [start, end] date range
 * - fetchDataService: (dates) => Promise<{ headers, rows }>
 * - tileOrder: array of field keys for custom tile order
 * - tileLabels: object mapping field keys to display labels
 * - branchField: string, field name for branch/grouping (default: 'BranchID')
 * - branchLabel: (branchValue) => string, function to render branch label
 * - renderAccordion: (props) => ReactNode, optional custom accordion/tab renderer
 * - tileRenderExtras: (data, key) => ReactNode, optional extra content in tile
 */
export default function FNBTileSet({
    chartName = "Branch Originated Reports",
    dates,
    fetchDataService,
    tileOrder = [],
    tileLabels = {},
    branchField = 'BranchID',
    branchLabel = (branch) => `${branch} ${branch === "All" ? "Branches" : "Branch"}`,
    renderAccordion,
    tileRenderExtras,
}) {
    const [chartData, setChartData] = useState(null);
    const toast = useRef(null);
    const [dialogVisible, setDialogVisible] = useState(false);
    const [dialogData, setDialogData] = useState(null);
    const [selectedBranches, setSelectedBranches] = useState(["All"]);
    const [loading, setLoading] = useState(false);

    const fetchData = () => {
        if (loading) return;
        setChartData(null);
        setDialogData(null);
        setDialogVisible(false);
        setLoading(true);
        const chartDataService = new ChartDataService(chartName);
        chartDataService.getChart()
            .then((data) => {
                setChartData(data);
                setLoading(false);
            })
            .catch((error) => {
                setLoading(false);
                console.error("Error fetching chart data:", error);
            });
    };

    useEffect(() => {
        if (!dates || dates[0] == null || dates[1] == null) return;
        const timeout = setTimeout(fetchData, 2500);
        return () => clearTimeout(timeout);
        // eslint-disable-next-line
    }, [dates]);

    if (!chartData) {
        return (
            <div className="flex justify-content-center align-items-center">
                <i className="pi pi-spin pi-spinner" style={{ fontSize: '2rem' }}></i>
            </div>
        );
    }

    const { headers, rows } = chartData;

    const branchOptions = rows
        ? Array.from(new Set(rows.map((row) => row[branchField]))).map((branch) => ({
            label: branchLabel(branch),
            value: branch,
        }))
        : [];

    const filteredRows = selectedBranches.length
        ? rows.filter((row) => selectedBranches.includes(row[branchField]))
        : rows;

    const handleBranchSelection = (selected) => {
        if (selected[selected.length - 1] === "All") {
            selected = ["All"];
        } else if (selected.includes("All")) {
            selected = selected.filter((branch) => branch !== "All");
        }
        if (selected.length === 0) {
            selected = ["All"];
        }
        setSelectedBranches(selected);
    };

    const showDialogWithData = (data) => {
        setDialogData(data);
        setDialogVisible(true);
    };

    const dialogFooter = (
        <div>
            <Button label="Close" icon="pi pi-times" onClick={() => setDialogVisible(false)} />
        </div>
    );

    const renderTileContent = (data) => {
        // Compose the order of keys for tiles
        const orderedKeys = tileOrder.concat(
            Object.keys(data).filter((key) => !tileOrder.includes(key))
        );

        return (
            <div className="p-3">
                <div className="flex flex-wrap gap-3">
                    {orderedKeys.map((key, index) => {
                        if (key.startsWith('_report_') || data[key] === "All") return null;
                        if (key === "Start-Date" || key === "End-Date") return null;
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
                                    <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#333' }}>
                                        {tileLabels[key] || key}
                                    </h4>
                                </div>
                                <div className="p-card-body">
                                    <p style={{ margin: 0, fontSize: '0.95rem', color: '#555' }}>
                                        {key === "Date" ? (
                                            <>
                                                {data["Start-Date"]} <br /> {"To"} <br /> {data["End-Date"]}
                                            </>
                                        ) : (
                                            <div>
                                                Total: {data[key]}
                                                {tileRenderExtras ? tileRenderExtras(data, key) : null}
                                            </div>
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
        <div>
            <Toast ref={toast} />
            <div className="flex flex-wrap justify-content-end gap-2 mb-3">
                <MultiSelect
                    value={selectedBranches}
                    options={branchOptions}
                    onChange={(e) => handleBranchSelection(e.value)}
                    placeholder="Filter by Branch"
                    className="p-mr-2"
                    style={{ maxWidth: '200px' }}
                />
                <Button icon="pi pi-refresh" label="Refresh" onClick={fetchData} text />
            </div>
            <div>
                {filteredRows.map((row, index) =>
                    renderAccordion ? (
                        renderAccordion({
                            tab: {
                                header: branchLabel(row[branchField]),
                                content: renderTileContent(row),
                            },
                            key: index,
                            show: filteredRows.length < 2,
                            hardShow: filteredRows.length === 1,
                        })
                    ) : (
                        <BorAccordion
                            tab={{
                                header: branchLabel(row[branchField]),
                                content: renderTileContent(row),
                            }}
                            key={index}
                            show={filteredRows.length < 2}
                            hardShow={filteredRows.length === 1}
                        />
                    )
                )}
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

    function exportRowAsCSV(rowData, filename = 'exported_data.csv') {
        if (!rowData || !rowData.length) return;
        const headers = Object.keys(rowData[0]).join(',');
        const csvContent = rowData
            .map((row) =>
                Object.keys(row)
                    .map((key) => `"${row[key]}"`)
                    .join(',')
            )
            .join('\n');
        const fullCsvContent = `${headers}\n${csvContent}`;
        const blob = new Blob([fullCsvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
}
