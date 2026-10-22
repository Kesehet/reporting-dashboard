import React, { useState, useEffect } from 'react';
import { dataParser, generateLineChartData, showPointValuesInLineChart, showQuarterMarkersInLineChart } from './Utils';
import ChartDataService from '../../Services/ChartDataService';
import { Chart } from 'primereact/chart';
import { Card } from 'primereact/card';
import { ProgressSpinner } from 'primereact/progressspinner';

const DEFAULT_CHART_PARAMS = {};

const FNBLineChart = ({data, showPointValues = false, chartAPIParams=DEFAULT_CHART_PARAMS}) => {
    data = data && typeof data === 'object' ? dataParser(data) : data;

    const [chartData, setChartData] = useState({ labels: [], datasets: [] });

    const getChartData = async () => {
        let chart = new ChartDataService(data,chartAPIParams);
        let chartResponse = await chart.getChart();

        const parsedData = chartResponse ? dataParser(generateLineChartData(chartResponse)) : { labels: [], datasets: [] };
        setChartData({
            labels: parsedData.labels || [],
            datasets: parsedData.datasets || []
        });
    };
   
    useEffect(() => {
        const fetchData = () => {
            if (typeof data === 'string') {
                getChartData();
            }
        };

        fetchData();
    }, [data, chartAPIParams]);


    if (!chartData || !chartData.labels || !chartData.labels.length || !chartData.datasets || !chartData.datasets.length) {
        return (
            <Card className="p-mt-3">
                <div className="p-d-flex p-ai-center p-jc-center" style={{ height: '300px' }}>
                    {typeof data === 'string' ? (
                        <p>{'Loading ' + data + '...'}</p>
                    ) : (
                        <ProgressSpinner />
                    )}
                </div>
            </Card>
        );
    }

    const renderLegends = () => {
        if (!chartData || !chartData.datasets) return null;

        return (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                {chartData.datasets.map((dataset, index) => (
                    <div key={index} style={{ display: 'flex', alignItems: 'center' }}>
                        <span
                            style={{
                                width: '12px',
                                height: '12px',
                                backgroundColor: dataset.borderColor,
                                display: 'inline-block',
                                marginRight: '8px'
                            }}
                        ></span>
                        <span>{dataset.label}</span>
                    </div>
                ))}
            </div>
        );
    };

    const PLUGINS = []
    if(showPointValues) PLUGINS.push(showPointValuesInLineChart());
                        PLUGINS.push(showQuarterMarkersInLineChart());

    return (
        <div className="p-d-flex" style={{ position: 'relative', height: '100%', width: '100%', flexDirection: 'column' }}>
            <div className="p-mt-3" style={{ height: '100%', width: '100%' }}>
                <Chart
                    style={{ height: '100%', width: '100%', minHeight: '60vh' }}
                    type="line"
                    data={chartData}
                    plugins={PLUGINS}
                    options={{
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                enabled: true
                            },
                            datalabels: {
                                display: true, 
                                align: 'top',
                                formatter: (value) => value 
                            }
                        },
                        scales: {
                            y: { 
                                beginAtZero: true,
                                ticks: {
                                    autoSkip: true, // Ensure all y-axis values are displayed
                                    display: true 
                                }
                            },
                            x: { 
                                grid: { display: false },
                                ticks: {
                                    autoSkip: true, // Ensure all x-axis values are displayed
                                    display: true 
                                }
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                        elements: {
                            line: {
                                tension: 0 
                            }
                        }
                    }}
                />
            </div>
            <div style={{ marginTop: '16px', textAlign: 'center' }}>
                {renderLegends()}
            </div>
        </div>
    );
};

export default FNBLineChart;