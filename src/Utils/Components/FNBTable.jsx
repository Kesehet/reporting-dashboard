import React, { useState, useEffect } from 'react';
import getCellData, { dataParser, getColorforTransactionType, getQuarterlyTableHeader } from './Utils';
import ChartDataService from '../../Services/ChartDataService';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import { ProgressSpinner } from 'primereact/progressspinner';

const FNBTable = ({data, dates, styleNow={}, subHeaderRow=null, chartAPIParams={}, freezeStyle=null }) => {
    
    data = dataParser(data);

    if(!styleNow['width']) styleNow['width'] = '100%';
    if(!styleNow['color']) styleNow['color'] = 'black';

    const [TableData, setTableData] = useState({ headers: [], rows: [] });
    const [formattedRows, setFormattedRows] = useState([]);

    const getChartData = async () => {
        let chart = new ChartDataService(data, chartAPIParams );
        let chartResponse = await chart.getChart();
        setTableData(
            dataParser(
                chartResponse
            )
        );
    };
    var headerReplicaWithUniqueDuplicates = [];


    useEffect(() => {
        const fetchData = () => {
            if (typeof (data) === "string") {
                getChartData();
            } else {
                setTableData(data);
            }
        };
    
        fetchData();
    }, [data, dates, chartAPIParams]);

    useEffect(() => {
        let isMounted = true;
        const headersWithKeys = TableData.headers.map((value, index) => value + index);

        const processRows = async () => {
            const initialRows = TableData.rows.map((row) => {
                const rowData = {};
                headersWithKeys.forEach((header, colIndex) => {
                    const value = row[colIndex];
                    if (value === '' || value === '-' ) {
                        rowData[header] = '-';
                    } else if (typeof value === 'string' && value.substring(0, 6) === 'SELECT') {
                        rowData[header] = `<div class="p-progress-spinner" role="progressbar" aria-busy="true" data-pc-name="progressspinner" data-pc-section="root"><svg class="p-progress-spinner-svg" viewBox="25 25 50 50" data-pc-section="spinner" style="animation-duration: 20s;"><circle class="p-progress-spinner-circle" cx="50" cy="50" r="7" fill="none" stroke-width="1" stroke-miterlimit="10" data-pc-section="circle"></circle></svg></div>`;
                    }
                    else {
                        rowData[header] = value;
                    }
                });
                return rowData;
            });

            setFormattedRows(initialRows);

            await Promise.all(
                TableData.rows.map(async (row, rowIndex) => {
                    const updatedRow = { ...initialRows[rowIndex] };

                    await Promise.all(
                        headersWithKeys.map(async (header, colIndex) => {
                            const value = row[colIndex];
                            if (value !== '' && value !== '-' ) {
                                const parsedValue = await getCellData(value);
                                if (!isMounted) return;
                                updatedRow[header] = parsedValue ?? value ?? '';
                            }
                        })
                    );

                    if (isMounted) {
                        setFormattedRows((prevRows) => {
                            const nextRows = [...prevRows];
                            nextRows[rowIndex] = updatedRow;
                            return nextRows;
                        });
                    }
                })
            );
        };

        if (TableData.rows.length > 0 && TableData.headers.length > 0) {
            processRows();
        } else {
            setFormattedRows([]);
        }

        return () => {
            isMounted = false;
        };
    }, [TableData.rows, TableData.headers]);

    if(!TableData.headers || !TableData.rows){
        return (
            <>
            {JSON.stringify(TableData)}
            </>
        )
    }

    
    if (TableData?.headers?.length === 0 || TableData?.rows?.length === 0) {
        
        if (typeof (data) === "string") {
            return (
                <>
                    <ProgressSpinner /> 
                    <p>{'Loading ' + data + "..."}</p>
                </>
            );
        }
        return (
            <p>Loading...</p>
        );
    }

    headerReplicaWithUniqueDuplicates = TableData.headers.map((value, index)=>{
            return value+index;
    });

    

   

    const cellStyle = (value) => {
        if (typeof value === 'string') {
            return { color: getColorforTransactionType(value) };
        }
        return {};
    };

    const dynamicColumns = TableData.headers.map((header, index) => {
        if (header === "-") {
            return (
                <Column
                    key={headerReplicaWithUniqueDuplicates[index]}
                    field={headerReplicaWithUniqueDuplicates[index]}
                    header={header}
                    alignFrozen='left'
                    headerStyle={{ textAlign: 'center' }}
                    body={(rowData) => (
                        <div dangerouslySetInnerHTML={{__html: rowData[headerReplicaWithUniqueDuplicates[index]]}} style={cellStyle(rowData[headerReplicaWithUniqueDuplicates[index]])}/>
                    )}
                />
            );
        } else {
            return (
                <Column
                    key={headerReplicaWithUniqueDuplicates[index]}
                    field={headerReplicaWithUniqueDuplicates[index]}
                    header={header}
                    headerStyle={{ textAlign: 'center' }}
                    body={(rowData) => (
                        <div dangerouslySetInnerHTML={{__html: rowData[headerReplicaWithUniqueDuplicates[index]]}} style={cellStyle(rowData[headerReplicaWithUniqueDuplicates[index]])}/>
                    )}
                />
            );
        }
    });

    return (
        <div className={`p-d-flex p-jc-center frozen-${freezeStyle ?? "none"}`}>
            <DataTable
                value={formattedRows}
                className="p-datatable-striped"
                rows={10}
                responsiveLayout="scroll"
                showGridlines
                style={styleNow ?? { width: '100%'}}
                headerColumnGroup={getQuarterlyTableHeader(TableData.headers, subHeaderRow ? subHeaderRow(TableData.headers.length) : null)}
            >
                {dynamicColumns}
            </DataTable>
        </div>
    );
};

export default FNBTable;
