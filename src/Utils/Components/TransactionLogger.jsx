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
    const [error, setError] = useState('');

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
        let active = true;
        const buildParams = async () => {
            setLoading(true);
            setError('');
            try {
                const startDate =
                    dates?.[0]?.toISOString().split('T')[0] ??
                    localStorage.getItem('start_date');

                const endDate =
                    dates?.[1]?.toISOString().split('T')[0] ??
                    localStorage.getItem('end_date');

                let trackingCodes = [...requestedTransactionFilter];

                if (trackingCodes.length === 0) {
                    const service = new ChartDataService(
                        'Transaction Logger Recent Txns',
                        {
                            start_date: startDate,
                            end_date: endDate,
                            form_code: selectedFormCode
                        }
                    );

                    const recentTxns = await service.getChart();

                    if (!Array.isArray(recentTxns)) throw new Error('Invalid recent transaction response');
                    trackingCodes = recentTxns.flat().filter(code => typeof code === 'string' && code.trim());
                }

                const params = {
                    start_date: startDate,
                    end_date: endDate,
                    form_code: selectedFormCode
                };

                if (trackingCodes.length) {
                    params.tracking_codes = trackingCodes.join(',');
                }

                if (active) setTableParams(params);
            } catch {
                if (active) {
                    setTableParams(null);
                    setError('Unable to load recent Journey Manager transactions. You can try a specific transaction ID.');
                }
            } finally {
                if (active) setLoading(false);
            }
        };

        buildParams();
        return () => { active = false; };
    }, [dates, requestedTransactionFilter, selectedFormCode]);

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

                    {error && <p role="alert">{error}</p>}
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