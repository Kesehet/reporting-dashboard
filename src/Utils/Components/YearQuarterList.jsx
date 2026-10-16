import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Tag } from 'primereact/tag';
import { Toast } from 'primereact/toast';

export const YearQuarterList = ({
    setList,
    initialValue = [],
    years,
    disabled = false,
    ariaLabelPrefix = 'Year Quarter',
    maxItems = null,
}) => {
    const toast = useRef(null);

    // Default years: currentYear-5 .. currentYear+1
    const defaultYears = useMemo(() => {
        const now = new Date();
        const current = now.getFullYear();
        const from = current - 5;
        const to = current + 1;
        return Array.from({ length: to - from + 1 }, (_, i) => from + i);
    }, []);

    const yearOptions = years && years.length ? years : defaultYears;

    const quarterOptions = ['Q1', 'Q2', 'Q3', 'Q4'];

    const [selectedYear, setSelectedYear] = useState(null);
    const [selectedQuarter, setSelectedQuarter] = useState(null);
    const [items, setItems] = useState(initialValue);

    // Push current list to parent whenever it changes
    useEffect(() => {
        setList(items);
    }, [items, setList]);

    const showWarn = (summary, detail) => {
        toast.current?.show({ severity: 'warn', summary, detail, life: 2500 });
    };

    const showInfo = (summary, detail) => {
        toast.current?.show({ severity: 'info', summary, detail, life: 2000 });
    };

    const addItem = () => {
        if (selectedYear === null || selectedQuarter === null) {
            showWarn('Missing selection', 'Choose both Year and Quarter.');
            return;
        }
        const candidate = { year: selectedYear, quarter: selectedQuarter };
        if (maxItems !== null && items.length >= maxItems) {
            showWarn('Limit reached', `You can only add up to ${maxItems} items.`);
            return;
        }
        const exists = items.some(i => i.year === candidate.year && i.quarter === candidate.quarter);
        if (exists) {
            showWarn('Duplicate not allowed', `${candidate.quarter} ${candidate.year} is already in the list.`);
            return;
        }

        // Add and keep list sorted (year desc, quarter desc)
        const newItems = [...items, candidate].sort((a, b) => {
            if (a.year !== b.year) return a.year - b.year;
            const order = { Q1: 1, Q2: 2, Q3: 3, Q4: 4 };
            return order[a.quarter] - order[b.quarter];
        });

        setItems(newItems);
        showInfo('Added', `${candidate.quarter} ${candidate.year} added.`);
    };

    const removeItem = (row) => {
        const newItems = items.filter(i => !(i.year === row.year && i.quarter === row.quarter));
        setItems(newItems);
        showInfo('Removed', `${row.quarter} ${row.year} removed.`);
    };

    const clearAll = () => {
        if (items.length === 0) {
            showWarn('Nothing to clear');
            return;
        }
        setItems([]);
        showInfo('Cleared', 'All entries removed.');
    };

    // Renderers
    const quarterBody = (row) => <Tag value={row.quarter} severity="info" />;
    const yearBody = (row) => <span>{row.year}</span>;
    const actionsBody = (row) => (
        <Button
            icon="pi pi-trash"
            severity="danger"
            text
            rounded
            aria-label="Remove"
            onClick={() => removeItem(row)}
            disabled={disabled}
        />
    );

    return (
        <div className="flex flex-column gap-3">
            <Toast ref={toast} />

            {/* Controls */}
            <div className="flex flex-row align-items-end gap-2 flex-wrap">
                <span className="p-float-label" style={{ minWidth: 160 }}>
                    <Dropdown
                        inputId="yq-year"
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(e.value)}
                        options={yearOptions}
                        optionLabel={(y) => String(y)}
                        itemTemplate={(y) => <span>{y}</span>}
                        placeholder="Select year"
                        disabled={disabled}
                        aria-label={`${ariaLabelPrefix} - Year`}
                        showClear
                        filter
                    />
                    <label htmlFor="yq-year">Year</label>
                </span>

                <span className="p-float-label" style={{ minWidth: 160 }}>
                    <Dropdown
                        inputId="yq-quarter"
                        value={selectedQuarter}
                        onChange={(e) => setSelectedQuarter(e.value)}
                        options={quarterOptions}
                        placeholder="Select quarter"
                        disabled={disabled}
                        aria-label={`${ariaLabelPrefix} - Quarter`}
                    />
                    <label htmlFor="yq-quarter">Quarter</label>
                </span>

                <Button
                    label="Add"
                    icon="pi pi-plus"
                    onClick={addItem}
                    disabled={disabled}
                />

                <div className="flex-1" />

                <Button
                    label="Clear All"
                    icon="pi pi-times"
                    severity="secondary"
                    outlined
                    onClick={clearAll}
                    disabled={disabled || items.length === 0}
                />
            </div>

            {/* List */}
            <DataTable
                value={items}
                emptyMessage="No year/quarter selected."
                size="small"
                stripedRows
                aria-label={`${ariaLabelPrefix} - Selected list`}
            >
                <Column header="Year" body={yearBody} sortable field="year" style={{ width: '8rem' }} />
                <Column header="Quarter" body={quarterBody} sortable field="quarter" style={{ width: '8rem' }} />
                <Column header="Actions" body={actionsBody} style={{ width: '6rem' }} />
            </DataTable>
        </div>
    );
};
