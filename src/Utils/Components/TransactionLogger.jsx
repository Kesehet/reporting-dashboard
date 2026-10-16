import React, { useEffect, useState, useMemo } from 'react';
import { InputText } from 'primereact/inputtext';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import ChartDataService from '../../Services/ChartDataService';
import ChartCard from './ChartCard';
import FNBDataTable from './FNBDataTable';

const TransactionLogger = ({ dates, requestedTransactions = [] }) => {
    const [requestedTxnInput, setRequestedTxnInput] = useState(
        (requestedTransactions || []).join(', ')
    );

    const [requestedTransactionFilter, setRequestedTransactionFilter] =
        useState(requestedTransactions || []);

    const [selectedFormCode, setSelectedFormCode] =
        useState('fnb-consumer');

    const [tableParams, setTableParams] = useState(null);
    const [loading, setLoading] = useState(false);
    const [formChanged, setformChanged] = useState(true);

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

    useEffect(() => {
        const buildParams = async () => {
            setLoading(true);
            try {
                const startDate =
                    dates?.[0]?.toISOString().split('T')[0] ??
                    localStorage.getItem('start_date');

                const endDate =
                    dates?.[1]?.toISOString().split('T')[0] ??
                    localStorage.getItem('end_date');

                let trackingCodes = [...requestedTransactionFilter];

                if (trackingCodes.length === 0 || formChanged) {
                    const service = new ChartDataService(
                        'Transaction Logger Recent Txns',
                        {
                            start_date: startDate,
                            end_date: endDate,
                            form_code: selectedFormCode
                        }
                    );

                    const recentTxns = await service.getChart();

                    trackingCodes = recentTxns?.[0] || [];
                }

                const params = {
                    start_date: startDate,
                    end_date: endDate,
                    form_code: selectedFormCode
                };

                if (!formChanged) {
                    params.tracking_codes = trackingCodes.join(',');
                }

                setTableParams(params);
            } finally {
                setLoading(false);
                setformChanged(false);
            }
        };

        buildParams();
    }, [dates, requestedTransactionFilter, selectedFormCode, formChanged]);

    const parseRequestedTransactions = (value) => {
        if (!value) return [];

        return value
            .split(',')
            .map(x => x.trim())
            .filter(Boolean);
    };

    const handleLoadTransactions = () => {
        setRequestedTransactionFilter(
            parseRequestedTransactions(requestedTxnInput)
        );
    };

    return (
        <ChartCard
            title="Transaction Logger"
            styleNow={{ width: '100%' }}
            noDialog={true}
            items={
                <div style={{ width: '100%' }}>
                    <div
                        style={{
                            marginBottom: '0.75rem',
                            display: 'flex',
                            gap: '0.5rem',
                            flexWrap: 'wrap'
                        }}
                    >
                        <InputText
                            value={requestedTxnInput}
                            onChange={(e) =>
                                setRequestedTxnInput(e.target.value)
                            }
                            placeholder="Transaction IDs (comma separated)"
                        />

                        <Dropdown
                            value={selectedFormCode}
                            options={formCodeOptions}
                            onChange={(e) => {
                                    setSelectedFormCode(e.value);
                                    setformChanged(true);
                                    setRequestedTransactionFilter([]);
                                }
                            }
                        />

                        <Button
                            label="Load"
                            icon="pi pi-search"
                            onClick={handleLoadTransactions}
                        />
                    </div>

                    {loading ? (
                        <p>Loading recent transactions...</p>
                    ) : (
                        tableParams && (
                            <FNBDataTable
                                key={JSON.stringify(tableParams)}
                                data="Transaction Logger"
                                extraParams={tableParams}
                                styleNow={{ width: '100%' }}
                            />
                        )
                    )}
                </div>
            }
        />
    );
};

export default TransactionLogger;