import React, { useState, useEffect } from 'react';
import { dataParser, getColorforTransactionType, getQuarterlyTableHeader } from './Utils';
import ChartDataService from '../../Services/ChartDataService';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import { ProgressSpinner } from 'primereact/progressspinner';

const FNBTable = ({data, dates, styleNow={}, subHeaderRow=null, chartAPIParams={}}) => {
    data = dataParser(data);

    if(!styleNow['width']) styleNow['width'] = '100%';
    if(!styleNow['color']) styleNow['color'] = 'black';

    const [TableData, setTableData] = useState({ headers: [], rows: [] });

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
            // console.log(value+index);
            return value+index;
    });

    const formattedRows = TableData.rows.map((row, rowIndex) => {
        const rowData = {};
        
        headerReplicaWithUniqueDuplicates.forEach((header, colIndex) => {
            if(!row[colIndex] || row[colIndex] == "-"){
                delete rowData[header]
            }
            else{
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

    const dynamicColumns = TableData.headers.map((header, index) => {
        if (header === "-") {
            return (
                <Column
                    key={headerReplicaWithUniqueDuplicates[index]}
                    field={headerReplicaWithUniqueDuplicates[index]}
                    header={header}
                    headerStyle={{ textAlign: 'center' }}
                    body={(rowData) => (
                        <span style={cellStyle(rowData[headerReplicaWithUniqueDuplicates[index]])}>
                            {rowData[headerReplicaWithUniqueDuplicates[index]]}
                        </span>
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
                        <span style={cellStyle(rowData[headerReplicaWithUniqueDuplicates[index]])}>
                            {rowData[headerReplicaWithUniqueDuplicates[index]]}
                        </span>
                    )}
                />
            );
        }
    });
    
    // console.log("My formatted rows",formattedRows);

    return (
        <div className="p-d-flex p-jc-center">
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
