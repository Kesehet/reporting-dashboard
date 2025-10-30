import React, { useState, useEffect } from 'react';
import { dataParser, FNB_PIE_PRIMARY_COLOURS, getColorforTransactionType } from './Utils';
import ChartDataService from '../../Services/ChartDataService';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import { Button } from 'primereact/button';

const FNBDataTable = ({ data, extraParams = {}, styleNow = {}}) => {
    // console.log("Received data:", data); // Print the data prop

    data = dataParser(data);

    if (!styleNow['width']) styleNow['width'] = '100%';
    if(!styleNow['color']) styleNow['color'] = 'black';

    const [TableData, setTableData] = useState({ headers: [], rows: [] });

    const getChartData = async () => {
        let chart = new ChartDataService(data, extraParams);
        let chartResponse = await chart.getChart();

        setTableData(
            dataParser(
                chartResponse
            )
        );
    };

    useEffect(() => {
        const fetchData = () => {
            if (typeof (data) === "string") {
                // console.log("Table Data received", data);
                getChartData();
            } else {
                // console.log("Generating Chart raw");
                setTableData(data);
            }
        };

        fetchData();
    }, [data]);

    if (TableData.headers.length === 0 || TableData.rows.length === 0) {
        if (typeof (data) === "string") {
            return (
                <p>{'Loading ' + data + "..."}</p>
            );
        }
        return (
            <p>Loading...</p>
        );
    }

    const formattedRows = TableData.rows.map((row, rowIndex) => {
        const rowData = {};
        TableData.headers.forEach((header, colIndex) => {
            if (!row[colIndex] || row[colIndex] === "-") {
                delete rowData[header];
            } else {
                rowData[header] = row[colIndex] ?? '';
            }
        });
        return rowData;
    });

    const cellStyle = (value) => {
        if (typeof value === 'string') {
            return { color: getColorforTransactionType(value) };
        }
        return {};
    };
    const exportCSV = () => {
        var csvContent = TableData.headers.join(',') + '\n';
        csvContent += TableData.rows.map(row => 
            row.join(',')
        ).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', data+'.csv');
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const dynamicColumns = TableData.headers.map((header, index) => {
        if (header === "-") {
            return (
                <Column
                    key={index}
                    field={header}
                    header={header}
                    frozen={true}
                    body={(rowData) => (
                        <span style={cellStyle(rowData[header])}>
                            {rowData[header]}
                        </span>
                    )}
                />
            );
        } else {
            return (
                <Column
                    key={index}
                    field={header}
                    header={header}
                    body={(rowData) => (
                        <span style={cellStyle(rowData[header])}>
                            {rowData[header]}
                        </span>
                    )}
                />
            );
        }
    });

    return (
        <div className="p-d-flex p-jc-center">
            <Button label="Export as CSV" icon="pi pi-download" onClick={exportCSV} className="mb-3" />
            <DataTable
                value={formattedRows}
                className="p-datatable-striped"
                paginator
                rows={10}
                responsiveLayout="scroll"
                showGridlines
                style={styleNow ?? { width: '100%' }}
                sortMode="multiple"
                filterDisplay="menu"
                globalFilterFields={TableData.headers}
                
            >
                {dynamicColumns.map((column, index) =>
                    React.cloneElement(column, {
                        sortable: true,
                        filter: true,
                        filterPlaceholder: `Filter by ${column.props.header}`,
                        filterMatchMode: 'contains',
                    })
                )}
            </DataTable> 
        </div>
    );
    
}


export default FNBDataTable;
