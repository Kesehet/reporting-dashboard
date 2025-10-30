import React, { useState, useEffect } from 'react';
import { dataParser, FNB_PIE_SECONDARY_COLOURS, getColorforTransactionType } from './Utils';
import ChartDataService from "../../Services/ChartDataService";
import { Button } from 'primereact/button';

const FNBMultipleTable = ({ data, dates, columnWidth=250 }) => {
    const [isLoading, setLoading] = useState(true);
    const [tableData, setTableData] = useState({ headers: [], rowSets: {} });
    const [foldedRows, setFoldedRows] = useState({}); // Track folded state for each subheader

    const getChartData = async () => {
        setLoading(true)
        const chart = new ChartDataService(data);
        const chartResponse = await chart.getChart();
        // console.log("Data", chartResponse);
        setTableData(dataParser(chartResponse));
        setLoading(false)
    };
    const fetchData = () => {
        if (typeof data === "string") {
            // console.log("Table Data received", data);
            getChartData();
        } else {
            // console.log("Generating Chart raw");
            setTableData(data);
        }
    };

    useEffect(() => {
        

        fetchData();
    }, [data]);

    useEffect(() => {
            if (!dates || dates[0] === null || dates[1] === null) {
                return; // Exit early if dates are invalid
            }
            const timeout = setTimeout(() => {
                fetchData();
            }, 2500);
    
            return () => clearTimeout(timeout);
        }, [dates]);
    
    useEffect(()=>{
        const initialFoldedState = Object.keys(tableData.rowSets).reduce((acc,subHeader) => {
            acc[subHeader] = true;
            return acc;
        },{});
        setFoldedRows(initialFoldedState);
    }, [tableData]);

    if (tableData.headers.length === 0 || Object.keys(tableData.rowSets).length === 0) {
        return <p>Loading...</p>;
    }

    const formatRows = (rows) => {
        if (rows.length === 1) {
            const combinedRow = {};
            tableData.headers.forEach((header, colIndex) => {
                if (rows[0][colIndex] && rows[0][colIndex] !== "-") {
                    combinedRow[header] = rows[0][colIndex];
                }
            });
            return [combinedRow];
        }
        
        return rows.map((row) => {
            const rowData = {};
            tableData.headers.forEach((header, colIndex) => {
                if (row[colIndex] && row[colIndex] !== "-") {
                    rowData[header] = row[colIndex];
                }
            });
            return rowData;
        });
    };

    

    const handleSubHeaderClick = (subHeader) => {
        setFoldedRows(prevState => ({
            ...prevState,
            [subHeader]: !prevState[subHeader],
        }));
    };

    const exportToCSV = () => {
    const reportName = "Lending And Deposits Report";
    if (!tableData.headers.length || !Object.keys(tableData.rowSets).length) return;

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        if (isNaN(date)) return dateStr;
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        const yyyy = date.getFullYear();
        return `${mm}/${dd}/${yyyy}`;
    };
    const formattedStart = dates && dates[0] ? formatDate(dates[0]) : '';
    const formattedEnd = dates && dates[1] ? formatDate(dates[1]) : '';

    let combinedCSV = '';
    combinedCSV += tableData.headers.join(',') + '\n';

    Object.keys(tableData.rowSets).forEach(subHeader => {
        let csvContent = '';
        csvContent += tableData.headers.join(',') + '\n';
        combinedCSV += subHeader + '\n';
        tableData.rowSets[subHeader].forEach(row => {
            const formattedRow = row.map(cell => {
                if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
                    return `"${cell.replace(/"/g, '""')}"`;
                }
                return cell;
            }).join(',');
            csvContent += formattedRow + '\n';
            
            combinedCSV += formattedRow + '\n'; // Add to combined CSV
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const cleanSubHeader = subHeader.replace(/[\\/:*?"<>|]/g, '');
        link.setAttribute(
            'download',
            `${reportName} - ${cleanSubHeader} ${formattedStart} - ${formattedEnd}.csv`
        );
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Export combined CSV
    const combinedBlob = new Blob([combinedCSV], { type: 'text/csv;charset=utf-8;' });
    const combinedUrl = URL.createObjectURL(combinedBlob);
    const combinedLink = document.createElement('a');
    combinedLink.href = combinedUrl;
    combinedLink.setAttribute(
        'download',
        `${reportName} - Combined ${formattedStart} - ${formattedEnd}.csv`
    );
    document.body.appendChild(combinedLink);
    combinedLink.click();
    document.body.removeChild(combinedLink);
};


    const renderTable = () => (
        <div className="datatable-container" style={{ display: 'flex', flexDirection: 'column', width: (tableData.headers.length * columnWidth)+"px", maxHeight: '80vh', overflowY: 'scroll' }}>
            <Button 
                label="Export to CSV"
                onClick={exportToCSV}
                style={{ marginBottom: '10px', alignSelf: 'flex-start' }}
            />
            {/* Table Headers */}
            <div className="datatable-header" style={{ display: 'flex', backgroundColor: '#f4f4f4', marginBottom: '10px', zIndex: '100', position: 'sticky', top: '0' }}>
            {tableData.headers.map((item, columnIndex) => (
                <div
                    key={columnIndex}
                    style={{
                        flex: 1,
                        padding: '10px',
                        fontWeight: 'bold',
                        minWidth: columnWidth+'px',
                        textAlign: 'center',
                        position: columnIndex === 0 ? 'sticky' : 'static', // Apply sticky only to the first column
                        left: columnIndex === 0 ? 0 : 'auto', // Ensure it stays in place when scrolled
                        backgroundColor: columnIndex === 0 ? 'white' : 'transparent', // Ensure it has a background to overlap content
                        zIndex: columnIndex === 0 ? 1 : 'auto', // Keep it on top
                    }}
                >
                    {item}
                </div>
            ))}

            </div>

            {/* Table Rows */}
            {Object.keys(tableData.rowSets).map((subHeader, rowIndex) => {
                const rowData = tableData.rowSets[subHeader];

                const rows = rowData.map((row, rowDataIndex) => (
                    <div
                        key={`${rowIndex}-${rowDataIndex}`}
                        className="datatable-row"
                        style={{ display: 'flex', marginBottom: '10px',  }}
                    >
                        {tableData.headers.map((item, columnIndex) => (
                            <div
                                key={columnIndex}
                                className={"datatable-cell " + (columnIndex === 0 ? 'w3-animate-left': 'w3-animate-zoom')}
                                style={{
                                    flex: 1,
                                    padding: '10px',
                                    minWidth: columnWidth+'px',
                                    textAlign: 'center',
                                    borderBottom: '1px solid #ddd',
                                    position: columnIndex === 0 ? 'sticky' : 'static', // Apply sticky only to the first column
                                    left: columnIndex === 0 ? 0 : 'auto', // Ensure it stays in place when scrolled
                                    color: columnIndex === 0 ? getColorforTransactionType(row[columnIndex]) : 'black',
                                    backgroundColor: columnIndex === 0 ? 'white' : 'transparent', // Ensure it has a background to overlap content
                                    zIndex: columnIndex === 0 ? 1 : 'auto', // Keep it on top
                                }}
                            >
                                {row[columnIndex]}
                            </div>
                        ))}

                    </div>
                ));

                return (
                    <div key={rowIndex}>
                        {/* Subheader with toggle functionality */}
                        <div
                            onClick={() => handleSubHeaderClick(subHeader)}
                            style={{
                                width: '100%',
                                cursor: 'pointer',
                                marginBottom: '5px',
                                position: 'sticky',
                                fontSize: '18px',
                                top: '40px',
                                padding:'16px',
                                color: getColorforTransactionType(subHeader),
                                left: 0,
                                background:"white",
                                textAlign: 'left',
                                zIndex: 10,
                            }}
                            className="w3-animate-top w3-button"
                        >
                            {subHeader}
                        </div>

                        {/* Conditionally render rows */}
                        {!foldedRows[subHeader] && rows}
                        <hr/>
                    </div>
                );
            })}
        </div>
    );

    if(isLoading){
        return (
            <div className='w3-button' style={{zIndex:'-1'}}>
                {"Loading " + data   + " ..."}
            </div>
        )
    }
    return <div className="p-d-flex p-jc-center" >
        {renderTable()}
        </div>;
};

export default FNBMultipleTable;
