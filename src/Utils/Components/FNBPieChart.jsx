import React, { useState, useEffect } from 'react';
import { Chart } from "primereact/chart";
import { ProgressSpinner } from "primereact/progressspinner";
import { Card } from "primereact/card";
import { generatePieChartData, dataParser } from "./Utils";
import ChartDataService from "../../Services/ChartDataService";
import ChartDataLabels from 'chartjs-plugin-datalabels';

const FNBPieChart = ({ data, setPieColor = false }) => {
    const [pieData, setPieData] = useState(null);
    const [loading, setLoading] = useState(true);

    const getChartData = async () => {
        try {
            const chartService = new ChartDataService(data);
            const chartResponse = await chartService.getChart();
            const parsedData = dataParser(chartResponse);
            const generatedData = generatePieChartData(parsedData, data, true);
            setPieData(dataParser(generatedData));
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
                setPieData(generatePieChartData(parsedData, data, setPieColor));
            }
            setLoading(false);
        };

        fetchData();
    }, [data]);

    if (loading) {
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <ProgressSpinner />
            </div>
        );
    }

    if (!pieData) {
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <p>Loading...</p>
            </div>
        );
    }

    const renderLegend = () => {
        return (
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '16px', marginTop: '16px' }}>
                {pieData.labels.map((label, index) => (
                    <div key={index} style={{ display: 'flex', alignItems: 'center' }}>
                        <span
                            style={{
                                width: '12px',
                                height: '12px',
                                backgroundColor: pieData.datasets[0].backgroundColor[index],
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
                    type="pie"
                    data={pieData}
                    plugins={[ChartDataLabels]}
                    options={{
                        plugins: {
                            legend: {
                                display: false,
                            },
                            datalabels: {
                                display: true,
                                color: '#fff',
                                anchor: 'center',
                                align: 'center',
                                formatter: (value, context) => {
                                    
                                    return `${value}`;
                                }
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }}
                    style={{ justifySelf: 'center', minHeight: '30vh' }}
                />
            </div>
            <div style={{ marginTop: '16px', textAlign: 'center' }}>
                {renderLegend()}
                </div>
        </div>
    );
};

export default FNBPieChart;
