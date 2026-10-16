import React, { useEffect, useState } from 'react';
import { Card } from 'primereact/card';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Divider } from 'primereact/divider';
import MetricsDataService from '../Services/MetricsDataService';

const MetricsCard = () => {
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            const service = new MetricsDataService();
            const data = await service.getMetrics();
            setMetrics(data);
            setLoading(false);
        };

        fetchData();
    }, []);

    const renderValue = (value) => {
        if (Array.isArray(value)) {
            return (
                <div className="p-ml-2">
                    {value.map((item, index) => (
                        <div key={index} className="p-mb-2">
                            {typeof item === 'object' && item !== null ? (
                                Object.entries(item).map(([subKey, subValue]) => (
                                    <div key={subKey}>
                                        <strong>{subKey}:</strong> {String(subValue)}
                                    </div>
                                ))
                            ) : (
                                <div>{String(item)}</div>
                            )}
                        </div>
                    ))}
                </div>
            );
        } else if (typeof value === 'object' && value !== null) {
            return (
                <div className="p-ml-2">
                    {Object.entries(value).map(([subKey, subValue]) => (
                        <div key={subKey}>
                            <strong>{subKey}:</strong> {String(subValue)}
                        </div>
                    ))}
                </div>
            );
        } else {
            return String(value);
        }
    };


    return (
        <Card title="Metrics Overview" style={{overflowY:'scroll', maxHeight:"300px", position:"absolute", bottom:0}} >
            {loading ? (
                <div className="p-d-flex p-jc-center">
                    <ProgressSpinner />
                </div>
            ) : (
                <div className="p-grid">
                    {metrics && Object.entries(metrics).map(([key, value]) => (
                        <React.Fragment key={key}>
                            <div className="p-col-4"><strong>{key}</strong></div>
                            <div className="p-col-8" style={{"fontSize":"9px"}}>{renderValue(value)}</div>
                            <Divider />
                        </React.Fragment>
                    ))}
                </div>
            )}
        </Card>
    );
};

export default MetricsCard;
