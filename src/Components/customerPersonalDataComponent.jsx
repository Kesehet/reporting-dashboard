import React, { useState, useEffect } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { MultiSelect } from 'primereact/multiselect';



const CustomerPersonalData = () => {
    const columns = [
        { field: 'name', header: 'Name' },
        { field: 'category', header: 'Category' },
        { field: 'quantity', header: 'Quantity' }
    ];
    const [visibleColumns, setVisibleColumns] = useState(columns);

    const onColumnToggle = (event) => {
        let selectedColumns = event.value;
        let orderedSelectedColumns = columns.filter((col) => selectedColumns.some((sCol) => sCol.field === col.field));

        setVisibleColumns(orderedSelectedColumns);
    };

    const header = <MultiSelect value={visibleColumns} options={columns} optionLabel="header" onChange={onColumnToggle} className="w-full sm:w-20rem" display="chip" />;

    return (
        <>
            <h1>Title</h1>
            <DataTable header={header} tableStyle={{ minWidth: '50rem' }}>
                {columns.map((col) => (
                    <Column key={col.field} field={col.field} header={col.header} />
                ))}
            </DataTable>
        </>
    );
}

export default CustomerPersonalData