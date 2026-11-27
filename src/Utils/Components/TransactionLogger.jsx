import React, { useState, useMemo } from 'react';
import { InputText } from 'primereact/inputtext';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import '../../Styles/transactionLogger.css';
import ChartCard from './ChartCard';
import FNBDataTable from './FNBDataTable';
import ApplicationTimeline from './ApplicationTimeline';

const TransactionLogger = ({ dates, requestedTransactions = [] }) => {
    const [requestedTxnInput, setRequestedTxnInput] = useState(
        (requestedTransactions || []).join(', ')
    );

    const [requestedTransactionFilter, setRequestedTransactionFilter] =
        useState(requestedTransactions || []);

    const [selectedFormCode, setSelectedFormCode] =
        useState('fnb-consumer');

    const formCodeOptions = useMemo(
        () => [
            
            { "label": "FNB Business Dev", "value": "fnb-biz-dev" },
            { "label": "FNB Business Dev Receipt", "value": "fnb-biz-dev-receipt" },
            { "label": "FNB Business Review", "value": "sb-review" },
            { "label": "FNB Consumer Loans", "value": "fnb-consumer" },
            { "label": "FNB Consumer Loans Receipt", "value": "fnb-consumer-receipt" },
            { "label": "FNB Consumer Review", "value": "fnb-consumer-review" },
            { "label": "FNB Consumer Review Receipt", "value": "fnb-consumer-rev-rcp" },
            { "label": "FNB Consumer Review Receipt 2", "value": "fnb-consumer-rev-rc" },
            { "label": "FNB Small Business Receipt", "value": "fnb-sb-receipt" },
            { "label": "FNB Support", "value": "fnbsupport" },
            { "label": "FNB Warehouse", "value": "fnb-warehouse" },
            { "label": "FNB Dashboard", "value": "fnb-dashboard" },
            { "label": "FNB Workspaces", "value": "workspaces" },
            { "label": "Small Business CoApplicant", "value": "sb-coapplicant" },
            { "label": "Small Business Post Approval", "value": "sb-postapproval" },
            { "label": "Small Business Primary", "value": "sb-primary" }


        ],
        []
    );

    const startDate = dates?.[0]?.toISOString().split('T')[0] ?? localStorage.getItem('start_date');
    const endDate = dates?.[1]?.toISOString().split('T')[0] ?? localStorage.getItem('end_date');
    const exactSearch = requestedTransactionFilter.length > 0;
    const tableParams = exactSearch
        ? { tracking_codes: requestedTransactionFilter.join(',') }
        : { start_date: startDate, end_date: endDate, form_code: selectedFormCode };

    function loadTransactions(event) {
        event.preventDefault();
        const codes = [...new Set(requestedTxnInput.split(',').map(code => code.trim()).filter(Boolean))];
        setRequestedTransactionFilter(codes);
    }

    return (
        <ChartCard title="Transaction Logger" styleNow={{ width: '100%' }} noDialog
            items={
                <div className="transaction-logger">
                    <form className="transaction-logger__filters" onSubmit={loadTransactions}>
                        <label htmlFor="logger-tracking-codes">
                            Transaction IDs
                            <InputText id="logger-tracking-codes" value={requestedTxnInput}
                                onChange={event => setRequestedTxnInput(event.target.value)}
                                placeholder="Tracking codes (comma-separated)" />
                        </label>
                        <label htmlFor="logger-form">
                            Journey Manager form
                            <Dropdown inputId="logger-form" value={selectedFormCode}
                                options={formCodeOptions} onChange={event => {
                                    setSelectedFormCode(event.value);
                                }} disabled={exactSearch || Boolean(requestedTxnInput.trim())} />
                        </label>
                        <Button type="submit" label="Load transactions" icon="pi pi-search" />
                    </form>
                    <section className="transaction-logger__results" aria-labelledby="logger-results-title">
                        <h2 id="logger-results-title">
                            {requestedTransactionFilter.length ? 'Transaction search results' : 'Recent transactions'}
                        </h2>
                        <p>{exactSearch ? "All forms and available dates" : startDate + " through " + endDate}</p>
                        <FNBDataTable key={JSON.stringify(tableParams)} data="Transaction Logger"
                            extraParams={tableParams} styleNow={{ width: '100%' }}
                            rowDetails={row => <ApplicationTimeline trackingCode={row.tracking_code} />} />
                    </section>
                </div>
            }
        />
    );
};

export default TransactionLogger;
