import React, { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Card } from "primereact/card";
import { Dropdown } from "primereact/dropdown";
import { Chart } from "primereact/chart";
import ChartDataService from "../../Services/ChartDataService";

const DEFAULT_CHART_TYPES = [
  { label: "Bar", value: "bar" },
  { label: "Line", value: "line" },
  { label: "Pie", value: "pie" },
  { label: "Doughnut", value: "doughnut" },
  { label: "Radar", value: "radar" },
  { label: "Polar Area", value: "polarArea" },
  { label: "Bubble", value: "bubble" },
  { label: "Scatter", value: "scatter" },
];

const SINGLE_SERIES_CHARTS = new Set(["pie", "doughnut", "polarArea"]);
const XY_CHARTS = new Set(["scatter", "bubble", ]);

const COLORS = [
  "#42A5F5",
  "#66BB6A",
  "#FFA726",
  "#AB47BC",
  "#26A69A",
  "#EF5350",
  "#FFCA28",
  "#5C6BC0",
  "#EC407A",
  "#7E57C2",
  "#29B6F6",
  "#9CCC65"
];

const asNumberIfPossible = (value) => {
  if (value === null || value === undefined) return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : value;
};

const sanitizeRows = (rows = [], headers = []) =>
  rows
    .filter((row) => Array.isArray(row))
    .map((row) => row.slice(0, headers.length));

const getColor = (index) => COLORS[index % COLORS.length];

const buildXYDataset = (headers, rows, chartType, axisConfig = {}) => {
  const { xIndex = 0, yIndex = 1, rIndex = null } = axisConfig;

  const hasValidAxes =
    Number.isInteger(xIndex) &&
    Number.isInteger(yIndex) &&
    xIndex < headers.length &&
    yIndex < headers.length;

  if (!hasValidAxes) {
    return { datasets: [] };
  }

  const xLabel = headers[xIndex] ?? "X";
  const yLabel = headers[yIndex] ?? "Y";

  const data = rows
    .map((row) => ({
      x: asNumberIfPossible(row[xIndex]),
      y: asNumberIfPossible(row[yIndex]),
      ...(chartType === "bubble"
        ? {
            r: (() => {
              if (!Number.isInteger(rIndex) || rIndex >= headers.length) {
                return 5;
              }

              const rawValue = asNumberIfPossible(row[rIndex]);
              const parsedRadius = Number(rawValue);

              return Number.isFinite(parsedRadius) && parsedRadius > 0
                ? Math.abs(parsedRadius)
                : 5;
            })(),
          }
        : {})
    }))
    .filter((point) =>
      typeof point.x === "number" && typeof point.y === "number"
    );

  if (!data.length) {
    return { datasets: [] };
  }

  return {
    datasets: [
      {
        label: `${yLabel} vs ${xLabel}`,
        data,
        backgroundColor: data.map((_, index) => getColor(index)),
        borderColor: data.map((_, index) => getColor(index)),
      }
    ]
  };
};

const buildSingleSeriesDataset = (headers, rows) => {
  if (headers.length < 2) {
    return { labels: [], datasets: [] };
  }

  const labels = rows.map((row) => row[0]);
  const data = rows.map((row) => asNumberIfPossible(row[1]) || 0);

  return {
    labels,
    datasets: [
      {
        label: headers[1],
        data,
        backgroundColor: labels.map((_, index) => getColor(index)),
        borderColor: labels.map((_, index) => getColor(index)),
        borderWidth: 1,
      }
    ]
  };
};

const buildMultiSeriesDataset = (headers, rows, chartType) => {
  if (headers.length < 2) {
    return { labels: [], datasets: [] };
  }

  const [, ...valueHeaders] = headers;
  const labels = rows.map((row) => row[0]);

  const datasets = valueHeaders.map((header, index) => {
    const color = getColor(index);

    return {
      label: header,
      data: rows.map((row) => asNumberIfPossible(row[index + 1]) || 0),
      backgroundColor: color,
      borderColor: color,
      fill: chartType !== "line",
      tension: chartType === "line" ? 0.4 : undefined,
    };
  });

  return { labels, datasets };
};

const buildChartData = (
  headers = [],
  rows = [],
  chartType = "bar",
  axisConfig = {},
  { preSanitized = false } = {}
) => {
  const sanitizedRows = preSanitized ? rows : sanitizeRows(rows, headers);

  if (!sanitizedRows.length) {
    return { labels: [], datasets: [] };
  }

  console.log(headers, sanitizedRows)

  if (XY_CHARTS.has(chartType)) {
    return buildXYDataset(headers, sanitizedRows, chartType, axisConfig);
  }

  if (SINGLE_SERIES_CHARTS.has(chartType)) {
    return buildSingleSeriesDataset(headers, sanitizedRows);
  }

  return buildMultiSeriesDataset(headers, sanitizedRows, chartType);
};

const buildChartOptions = (title, chartType, headers, axisConfig = {}) => {
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
    //   legend: {
    //     position: SINGLE_SERIES_CHARTS.has(chartType) ? "right" : "top",
    //   },
      title: {
        display: Boolean(title),
        text: title || "",
      },
    },
  };

  if (XY_CHARTS.has(chartType)) {
    const { xIndex = 0, yIndex = 1 } = axisConfig;
    const xAxisTitle = headers[xIndex] ?? "X";
    const yAxisTitle = headers[yIndex] ?? "Y";

    baseOptions.scales = {
      x: {
        type: "linear",
        title: { display: true, text: xAxisTitle },
        beginAtZero: true,
      },
      y: {
        title: { display: true, text: yAxisTitle },
        beginAtZero: true,
      },
    };
  }

  return baseOptions;
};

const OneShotChart = ({
  data,
  extraParams,
  title = "Generated Chart",
  initialType = "bar",
  typeOptions = DEFAULT_CHART_TYPES,
  onTypeChange,
  className = "",
  chartHeight = "400px",
}) => {
  const [selectedType, setSelectedType] = useState(initialType);
  const [selectedXField, setSelectedXField] = useState(0);
  const [selectedYField, setSelectedYField] = useState(1);
  const [selectedRadiusField, setSelectedRadiusField] = useState(2);
  const [dataSource, setDataSource] = useState({ headers: [], rows: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setLoadError(null);

      try {
        const c = new ChartDataService(data, extraParams);
        const response = await c.getChart();

        if (cancelled) return;

        const nextHeaders = Array.isArray(response?.headers)
          ? response.headers
          : [];
        const nextRows = Array.isArray(response?.rows) ? response.rows : [];

        setDataSource((previous) => {
          if (previous.headers === nextHeaders && previous.rows === nextRows) {
            return previous;
          }

          return { headers: nextHeaders, rows: nextRows };
        });
      } catch (error) {
        if (cancelled) return;

        console.error("Failed to load chart data", error);
        setLoadError(error);
        setDataSource({ headers: [], rows: [] });
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [data, extraParams]);

  const headers = useMemo(
    () => (Array.isArray(dataSource?.headers) ? dataSource.headers : []),
    [dataSource]
  );

  const rows = useMemo(
    () => (Array.isArray(dataSource?.rows) ? dataSource.rows : []),
    [dataSource]
  );

  const sanitizedRows = useMemo(
    () => sanitizeRows(rows, headers),
    [rows, headers]
  );

  const headerOptions = useMemo(
    () =>
      headers.map((header, index) => ({
        label: header ?? `Column ${index + 1}`,
        value: index,
      })),
    [headers]
  );

  useEffect(() => {
    if (!headerOptions.length) {
      setSelectedXField(null);
      setSelectedYField(null);
      setSelectedRadiusField(null);
      return;
    }

    setSelectedXField((prev) =>
      Number.isInteger(prev) && prev < headerOptions.length
        ? prev
        : headerOptions[0].value
    );

    setSelectedYField((prev) => {
      if (Number.isInteger(prev) && prev < headerOptions.length) {
        return prev;
      }

      const fallbackIndex = headerOptions[Math.min(1, headerOptions.length - 1)]
        ?.value;
      return fallbackIndex ?? headerOptions[0].value;
    });

    setSelectedRadiusField((prev) => {
      if (Number.isInteger(prev) && prev < headerOptions.length) {
        return prev;
      }

      if (headerOptions.length > 2) {
        return headerOptions[2].value;
      }

      return null;
    });
  }, [headerOptions]);

  const bubbleRadiusOptions = useMemo(() => {
    if (!headerOptions.length) {
      return [];
    }

    return [
      { label: "Auto (constant size)", value: null },
      ...headerOptions,
    ];
  }, [headerOptions]);

  const axisConfig = useMemo(
    () => ({
      xIndex: selectedXField,
      yIndex: selectedYField,
      rIndex: selectedRadiusField,
    }),
    [selectedXField, selectedYField, selectedRadiusField]
  );

  const deferredHeaders = useDeferredValue(headers);
  const deferredRows = useDeferredValue(sanitizedRows);
  const deferredAxisConfig = useDeferredValue(axisConfig);

  const chartData = useMemo(
    () =>
      buildChartData(
        deferredHeaders,
        deferredRows,
        selectedType,
        deferredAxisConfig,
        { preSanitized: true }
      ),
    [deferredHeaders, deferredRows, selectedType, deferredAxisConfig]
  );

  const chartOptions = useMemo(
    () =>
      buildChartOptions(title, selectedType, deferredHeaders, deferredAxisConfig),
    [title, selectedType, deferredHeaders, deferredAxisConfig]
  );

  const hasRenderableData =
    Array.isArray(chartData.datasets) && chartData.datasets.length > 0;

  const handleTypeChange = (value) => {
    setSelectedType(value);
    if (onTypeChange) onTypeChange(value);
  };

  const showAxisSelectors =
    XY_CHARTS.has(selectedType) && headerOptions.length >= 2;

  return (
    <Card className={`p-4 w-full ${className}`}>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <h2 className="text-xl font-semibold">{title}</h2>
        <Dropdown
          value={selectedType}
          options={typeOptions}
          optionLabel="label"
          optionValue="value"
          onChange={(event) => handleTypeChange(event.value)}
          placeholder="Select Chart Type"
          className="w-full md:w-56"
          disabled={isLoading}
        />
      </div>

      {showAxisSelectors && (
        <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Dropdown
            value={selectedXField}
            options={headerOptions}
            optionLabel="label"
            optionValue="value"
            onChange={(event) => setSelectedXField(event.value)}
            placeholder="Select X Axis"
            className="w-full"
            disabled={isLoading}
          />
          <Dropdown
            value={selectedYField}
            options={headerOptions}
            optionLabel="label"
            optionValue="value"
            onChange={(event) => setSelectedYField(event.value)}
            placeholder="Select Y Axis"
            className="w-full"
            disabled={isLoading}
          />
          {selectedType === "bubble" && (
            <Dropdown
              value={selectedRadiusField}
              options={bubbleRadiusOptions}
              optionLabel="label"
              optionValue="value"
              onChange={(event) => setSelectedRadiusField(event.value)}
              placeholder="Select Radius Field"
              className="w-full"
              disabled={isLoading}
            />
          )}
        </div>
      )}

      <div className="mt-6" style={{ minHeight: chartHeight }}>
        {isLoading ? (
          <p className="text-center text-sm text-gray-500">Loading chart data</p>
        ) : loadError ? (
          <div className="text-center text-sm text-red-500">
            Unable to load chart data.
          </div>
        ) : hasRenderableData ? (
          <Chart
            type={selectedType}
            data={chartData}
            options={chartOptions}
            style={{ minHeight: chartHeight }}
          />
        ) : (
          <p className="text-center text-sm text-gray-500">
            No data available for the selected chart type.
          </p>
        )}
      </div>
    </Card>
  );
};

export default OneShotChart;

