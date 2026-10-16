import React, { useState, useEffect } from 'react';
import { dataParser, getColorforTransactionType } from './Utils';
import ChartDataService from '../../Services/ChartDataService';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import 'primereact/resources/themes/saga-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import { Button } from 'primereact/button';

const FNBDataTable = ({ data, extraParams = {}, styleNow = {} }) => {

    data = dataParser(data);

    if (!styleNow.width) styleNow.width = '100%';
    if (!styleNow.color) styleNow.color = 'black';

    const [TableData, setTableData] = useState({ headers: [], rows: [] });

    const getChartData = async () => {
        let chart = new ChartDataService(data, extraParams);
        let chartResponse = await chart.getChart();

        setTableData(
            dataParser(chartResponse)
        );
    };

    useEffect(() => {
        const fetchData = () => {
            if (typeof data === 'string') {
                getChartData();
            } else {
                setTableData(data);
            }
        };

        fetchData();
    }, [data, JSON.stringify(extraParams)]);

    if (TableData.headers.length === 0 || TableData.rows.length === 0) {
        if (typeof data === 'string') {
            return <p>{'Loading ' + data + '...'}</p>;
        }

        return <p>Loading...</p>;
    }

    const formattedRows = TableData.rows.map((row) => {
        const rowData = {};

        TableData.headers.forEach((header, colIndex) => {
            if (!row[colIndex] || row[colIndex] === '-') {
                delete rowData[header];
            } else {
                rowData[header] = row[colIndex];
            }
        });

        return rowData;
    });

    const renderValue = (value, depth = 0) => {
        if (value === null || value === undefined || value === '') {
            return '-';
        }

        if (typeof value === 'string') {
            const trimmed = value.trim();

            if (
                (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
                (trimmed.startsWith('[') && trimmed.endsWith(']'))
            ) {
                try {
                    const parsed = JSON.parse(trimmed);
                    return renderValue(parsed, depth);
                } catch {
                    // Not valid JSON
                }
            }

            return (
                <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {value}
                </span>
            );
        }

        if (Array.isArray(value)) {
            return (
                <div
                    style={{
                        marginLeft: depth ? '0.75rem' : 0,
                        borderLeft: depth ? '1px solid #e5e7eb' : 'none',
                        paddingLeft: depth ? '0.5rem' : 0
                    }}
                >
                    {value.map((item, index) => (
                        <div key={index} style={{ marginTop: index ? '0.35rem' : 0 }}>
                            <div style={{ fontWeight: 600 }}>
                                {index + 1}.
                            </div>
                            <div style={{ marginLeft: '0.75rem' }}>
                                {renderValue(item, depth + 1)}
                            </div>
                        </div>
                    ))}
                </div>
            );
        }

        if (typeof value === 'object') {
            return (
                <div
                    style={{
                        marginLeft: depth ? '0.75rem' : 0,
                        borderLeft: depth ? '1px solid #e5e7eb' : 'none',
                        paddingLeft: depth ? '0.5rem' : 0
                    }}
                >
                    {Object.entries(value).map(([key, val]) => (
                        <div
                            key={key}
                            style={{
                                display: 'flex',
                                gap: '0.35rem',
                                alignItems: 'flex-start',
                                marginTop: '0.25rem'
                            }}
                        >
                            <span
                                style={{
                                    fontWeight: 600,
                                    minWidth: 'max-content'
                                }}
                            >
                                {key}:
                            </span>

                            <div style={{ flex: 1 }}>
                                {renderValue(val, depth + 1)}
                            </div>
                        </div>
                    ))}
                </div>
            );
        }

        return String(value);
    };

    const cellStyle = (value) => {
        if (typeof value === 'string') {
            return { color: getColorforTransactionType(value) };
        }

        return {};
    };

    const exportCSV = () => {
        let csvContent = TableData.headers.join(',') + '\n';

        csvContent += TableData.rows
            .map((row) =>
                row.map((cell) =>
                    typeof cell === 'object'
                        ? JSON.stringify(cell)
                        : cell
                ).join(',')
            )
            .join('\n');

        const blob = new Blob(
            [csvContent],
            { type: 'text/csv;charset=utf-8;' }
        );

        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', data + '.csv');
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const dynamicColumns = TableData.headers.map((header, index) => (
        <Column
            key={index}
            field={header}
            header={header}
            frozen={header === '-'}
            body={(rowData) => (
                <span style={cellStyle(rowData[header])}>
                    {renderValue(rowData[header])}
                </span>
            )}
        />
    ));

    return (
        <div className="p-d-flex p-jc-center">
            <Button
                label="Export as CSV"
                icon="pi pi-download"
                onClick={exportCSV}
                className="mb-3"
            />

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
                {dynamicColumns.map((column) =>
                    React.cloneElement(column, {
                        sortable: true,
                        filter: true,
                        filterPlaceholder: `Filter by ${column.props.header}`,
                        filterMatchMode: 'contains'
                    })
                )}
            </DataTable>
        </div>
    );
};

export default FNBDataTable;