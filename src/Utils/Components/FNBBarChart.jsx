import React, { useState, useEffect } from 'react';
import { Chart } from "primereact/chart";
import { ProgressSpinner } from "primereact/progressspinner";
import { Card } from "primereact/card";
import { generateBarChartData, dataParser } from "./Utils";
import ChartDataService from "../../Services/ChartDataService";

const FNBBarChart = ({ data, setBarColor = false, chartAPIParams={} }) => {
    const [barData, setBarData] = useState(null);
    const [loading, setLoading] = useState(true);

    const getChartData = async () => {
        try {
            const chartService = new ChartDataService(data, chartAPIParams);
            const chartResponse = await chartService.getChart();
            const parsedData = dataParser(chartResponse);
            const generatedData = generateBarChartData(parsedData, data, true);
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
                setBarData(generateBarChartData(parsedData, data, setBarColor));
            }
            setLoading(false);
        };

        fetchData();

    }, [data, JSON.stringify(chartAPIParams)]);

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

    if (!barData.labels || barData?.labels.length <= 0){
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <p>Chart did not have any numbers to show</p>
            </div>
        );
    }

    const isVerticalStack = barData?.labels?.some(label => label.length > 20);

    const chartType = isVerticalStack ? "bar" : "bar";
    const scalesConfig = isVerticalStack
        ? {
            x: {
                beginAtZero: true,
            },
            y: {
                beginAtZero: true,
            }
        }
        : {
            x: {
                beginAtZero: true,
                stacked: true,
            },
            y: {
                beginAtZero: true,
                stacked: true,
            }
        };


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
                    type={chartType}
                    data={barData}
                    options={{
                        plugins: {
                            legend: {
                                display: false,
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                        indexAxis: isVerticalStack ? 'y' : 'x',
                        scales: scalesConfig
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

export default FNBBarChart;
