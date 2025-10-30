import { useState, useEffect } from 'react';
import { Chart } from "primereact/chart";
import { ProgressSpinner } from "primereact/progressspinner";
import { dataParser, generateBarWithLineChartData } from "./Utils";
import ChartDataService from "../../Services/ChartDataService";

const FNBBarWithLineChart = ({ data, dates, setBarColor = false, chartAPIParams = {} }) => {
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);

    const getChartData = async () => {
        try {
            const chartService = new ChartDataService(data, chartAPIParams);
            const chartResponse = await chartService.getChart();
            const parsedData = dataParser(chartResponse);
            const generatedData = generateBarWithLineChartData(parsedData, data, true);
            setChartData(dataParser(generatedData));
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
                setChartData(generateBarWithLineChartData(parsedData, data, setBarColor));
            }
            setTimeout(() => setLoading(false), 3000);
        };

        if (dates && dates[0] != null && dates[1] != null) {
            setLoading(true);
            setTimeout(fetchData, 2000);
        }
    }, [data, dates, JSON.stringify(chartAPIParams)]);

    if (loading) {
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <ProgressSpinner />
            </div>
        );
    }

    if (!chartData) {
        return (
            <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '100%' }}>
                <p>Loading...</p>
            </div>
        );
    }

    return (
        <div className="p-d-flex" style={{ position: 'relative', height: '100%', width: '100%', flexDirection: 'column' }}>
            <div className="p-d-flex" style={{ flex: 1 }}>
                <Chart
                    type="bar"
                    data={chartData}
                    options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                            }
                        },
                        scales: {
                            x: {
                                stacked: false
                            },
                            y: {
                                type: 'linear',
                                position: 'left',
                                title: {
                                    display: true,
                                    text: ''
                                }
                            },
                            y1: {
                                type: 'linear',
                                position: 'right',
                                grid: {
                                    drawOnChartArea: false
                                },
                                title: {
                                    display: true,
                                    text: ''
                                }
                            }
                        }
                    }}

                    style={{ justifySelf: 'center', minHeight: '30vh', minWidth: '100%' }}
                />
            </div>
        </div>
    );
};

export default FNBBarWithLineChart;
