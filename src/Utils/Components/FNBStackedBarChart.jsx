import { useState, useEffect } from 'react';
import { Chart } from "primereact/chart";
import { ProgressSpinner } from "primereact/progressspinner";
import { dataParser, generateStackedBarChartData } from "./Utils";
import ChartDataService from "../../Services/ChartDataService";

const FNBStackedBarChart = ({ data, dates, setBarColor = false, chartAPIParams={} }) => {
    const [barData, setBarData] = useState(null);
    const [loading, setLoading] = useState(true);

    const getChartData = async () => {
        try {
            const chartService = new ChartDataService(data, chartAPIParams);
            const chartResponse = await chartService.getChart();
            const parsedData = dataParser(chartResponse);
            const generatedData = generateStackedBarChartData(parsedData, data, true);
            setBarData(dataParser(generatedData));
        } catch (error) {
            console.error("Error fetching chart data:", error);
        }
    };

    useEffect(() => {
        const fetchData = () => {
            
            if (typeof data === "string") {
                getChartData();
            } else {
                const parsedData = dataParser(data);
                setBarData(generateStackedBarChartData(parsedData, data, setBarColor));
            }
            setTimeout(setLoading(false), 3000)
        };
        if(dates && dates[0] != null && dates[1] != null){
            setLoading(true)
            setTimeout(fetchData, 2000)    
        }
        

    }, [data, dates, JSON.stringify(chartAPIParams)]);

    if (loading) {
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <ProgressSpinner />
            </div>
        );
    }

    if (!barData) {
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <p>Loading...</p>
            </div>
        );
    }

    const renderLegend = () => {
        return (
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '16px', marginTop: '16px' }}>
                {barData.labels.map((label, index) => (
                    <div key={index} style={{ display: 'flex', alignItems: 'center' }}>
                        <span
                            style={{
                                width: '12px',
                                height: '12px',
                                backgroundColor: barData.datasets[0].backgroundColor[index],
                                display: 'inline-block',
                                marginRight: '8px'
                            }}
                        ></span>
                        <span>{label}</span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="p-d-flex" style={{ position: 'relative', height: '100%', width: '100%', flexDirection: 'column' }}>
            <div className="p-d-flex" style={{ flex: 1 }}>
                <Chart
                    type="bar"
                    data={barData}
                    options={{
                        plugins: {
                            legend: {
                                display: false,
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                stacked: true,
                            },
                            y: {
                                stacked: true,
                            }
                        }
                    }}
                    style={{ justifySelf: 'center', minHeight: '30vh', minWidth: '100%' }}
                />
            </div>
            <div style={{ marginTop: '16px', textAlign: 'center' }}>
                {renderLegend()}
            </div>
        </div>
    );
};

export default FNBStackedBarChart;
