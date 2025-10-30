import React, { useEffect } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { MultiSelect } from 'primereact/multiselect';
import { Menubar } from 'primereact/menubar';
import { Button } from 'primereact/button';
import { write, utils } from "xlsx"
import FileSaver from 'file-saver';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';

const TableComponent = ({ transactions, loading, columns, visibleColumns, setVisibleColumns, setPage, columnGroups }) => {

    const exportExcel = () => {
        const selectedFields = transactions.map(transaction => {
            let selected = {};
            visibleColumns.forEach(col => {
                selected[col] = transaction[col];
            });
            return selected;
        });

        
        const worksheet = utils.json_to_sheet(selectedFields);
        const workbook = { Sheets: { data: worksheet }, SheetNames: ['data'] };
        const excelBuffer = write(workbook, { bookType: 'xlsx', type: 'array' });
        saveAsExcelFile(excelBuffer, 'transactions');
        
    };

    const saveAsExcelFile = (buffer, fileName) => {
       
        let EXCEL_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
        let EXCEL_EXTENSION = '.xlsx';
        const data = new Blob([buffer], { type: EXCEL_TYPE });
        FileSaver.saveAs(data, fileName + '_export_' + new Date().getTime() + EXCEL_EXTENSION);
            
    };

    const handleMultiSelectChange = (e) => {
        const selectedGroups = e.value;
        let newVisibleColumns = [];

        selectedGroups.forEach(group => {
            if (columnGroups[group]) {
                newVisibleColumns = [...newVisibleColumns, ...columnGroups[group]];
            }
        });

        setVisibleColumns(newVisibleColumns);
    };

    const multiSelectOptions = Object.keys(columnGroups).map(group => ({ label: `Group: ${group}`, value: group }));

    const items = [
        {
            template: () => ( 
                <div data-testid="multiselect-container">
                    <MultiSelect 
                        options={multiSelectOptions} 
                        value={Object.keys(columnGroups).filter(group => columnGroups[group].every(col => visibleColumns.includes(col)))} 
                        optionLabel="label" 
                        onChange={handleMultiSelectChange} 
                        display="chip"
                    />
                </div>
            )
        },
        {
            template: () => (
                <div className='p-m-2'>
                    <Button label="Analytics" icon="pi pi-chart-bar" className="p-button-rounded p-button-info" onClick={() => setPage("Graphs")} />
                </div>
            )
        },
        {
            template: () => (
                <div className='p-m-2'>
                    <Button label="Export" icon="pi pi-file-excel" className="p-button-rounded p-button-success" onClick={exportExcel} />
                </div>
            )
        }
    ];

    useEffect(() => {
 
    }, [transactions, columns, visibleColumns]);

    const renderBodyTemplate = (data, field) => {
        const value = data[field];
        if (Array.isArray(value)) {
            return value.join(', ');
        } else if (typeof value === 'object' && value !== null) {
            return JSON.stringify(value);
        }
        return value;
    };

    return (
        <div className='p-grid p-align-center p-justify-center'>
            <div className='p-col-12' data-testid="menubar-container">
                <Menubar model={items} />
            </div>
            <div className='p-col-12' data-testid="datatable-container">
                <DataTable value={transactions} loading={loading} emptyMessage="No rows matched." responsiveLayout="scroll" paginator paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown" dataKey="id" showGridlines stripedRows className="datatable-responsive" currentPageReportTemplate="Showing {first} to {last} of {totalRecords} Records" rows={20}>
                    {visibleColumns.map(col => (
                        <Column key={col} field={col} header={columns.find(column => column.field === col)?.header} sortable filter body={(data) => renderBodyTemplate(data, col)} />
                    ))}
                </DataTable>
            </div>
        </div>
    );
};

export default TableComponent;
