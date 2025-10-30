import React, { useState, useEffect } from 'react';
import { Button } from 'primereact/button';
import ChartDataService from '../../Services/ChartDataService';
import { dataParser } from './Utils';

const ExportButton = ({ data, dates }) => {
    const [tableData, setTableData] = useState({ headers: [], rowSets: {} });

    useEffect(() => {
        const fetchData = async () => {
            if (typeof data === 'string') {
                const chart = new ChartDataService(data);
                const chartResponse = await chart.getChart();
                setTableData(dataParser(chartResponse));
            } else {
                setTableData(data);
            }
        };

        fetchData();
    }, [data, dates]);

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        if (isNaN(date)) return dateStr;
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        const yyyy = date.getFullYear();
        return `${mm}/${dd}/${yyyy}`;
    };

    const exportToCSV = () => {
        const reportName = "Lending And Deposits Report";
        if (!tableData.headers.length || !Object.keys(tableData.rowSets).length) return;

        const formattedStart = dates?.[0] ? formatDate(dates[0]) : '';
        const formattedEnd = dates?.[1] ? formatDate(dates[1]) : '';

        Object.keys(tableData.rowSets).forEach(subHeader => {
            let csvContent = tableData.headers.join(',') + '\n';

            tableData.rowSets[subHeader].forEach(row => {
                csvContent += row.map(cell => {
                    if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
                        return `"${cell.replace(/"/g, '""')}"`;
                    }
                    return cell;
                }).join(',') + '\n';
            });

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            const cleanSubHeader = subHeader.replace(/[\\/:*?"<>|]/g, '');
            link.setAttribute(
                'download',
                `${reportName} - ${cleanSubHeader} ${formattedStart} - ${formattedEnd}.csv`
            );
            link.href = url;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    };

    return (
        <Button
            label="Export CSV"
            icon="pi pi-download"
            onClick={exportToCSV}
            className="p-button-sm p-button-secondary"
        />
    );
};

export default ExportButton;
