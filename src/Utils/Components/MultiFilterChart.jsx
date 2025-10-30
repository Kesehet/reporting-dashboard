// MultiFilterChart.jsx (UI-only redesign: PrimeReact + W3.CSS)
// Functionality, state, and data flow preserved.

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement,
  RadialLinearScale, ArcElement,
  Tooltip, Legend
} from "chart.js";
import { Chart } from "react-chartjs-2";
import ChartDataService from "../../Services/ChartDataService";

// PrimeReact components
import { Card } from "primereact/card";
import { Dropdown } from "primereact/dropdown";
import { MultiSelect } from "primereact/multiselect";
import { Checkbox } from "primereact/checkbox";
import { Button } from "primereact/button";
import { Message } from "primereact/message";
import { Divider } from "primereact/divider";

ChartJS.register(
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement,
  RadialLinearScale, ArcElement,
  Tooltip, Legend
);

export default function MultiFilterChart({
  // Data can be passed directly or fetched by id via ChartDataService
  data,                  // optional id for ChartDataService
  extraParams,           // optional params for ChartDataService
  headers,               // optional string[]
  rows,                  // optional any[][]
  chartType = "bar",
  mapping = {},          // { x, y }
  options = {},          // { aggregation, stacked }
  serverUrl = "/final",  // route that invokes temp.py final()
  onError,
}) {
  // --- state
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const [uiType, setUiType] = useState(chartType);
  const [uiMapping, setUiMapping] = useState(() => ({
    x: mapping.x ?? "",
    y: Array.isArray(mapping.y) ? mapping.y : (mapping.y ? [mapping.y] : []),
  }));
  const [uiOpts, setUiOpts] = useState(() => ({
    aggregation: options.aggregation ?? "sum",
    stacked: !!options.stacked,
    group_dates_by: options.group_dates_by ?? "monthly"
  }));

  // --- raw data (from props or service)
  const svcKey = useMemo(
    () => JSON.stringify({ data, extraParams }, null, 0),
    [data, extraParams]
  );
  const cacheRef = useRef(new Map());
  const ensureRaw = useCallback(async () => {
    // Prefer directly supplied headers/rows
    if (Array.isArray(headers) && headers.length && Array.isArray(rows) && rows.length) {
      return { headers, rows };
    }
    if (cacheRef.current.has(svcKey)) return cacheRef.current.get(svcKey);

    if (!data || typeof data !== "string") {
      throw new Error("Either provide {headers, rows} or a 'data' id for ChartDataService.");
    }
    const svc = new ChartDataService(data, extraParams);
    const res = await svc.getChart(); // expects { headers:[], rows:[] }
    if (!Array.isArray(res?.headers) || !Array.isArray(res?.rows)) {
      throw new Error("ChartDataService returned invalid shape");
    }
    cacheRef.current.set(svcKey, res);
    return res;
  }, [headers, rows, data, extraParams, svcKey]);

  const [cols, setCols] = useState(() => (Array.isArray(headers) ? headers.map(String) : []));
  useEffect(() => {
    (async () => {
      try {
        const raw = await ensureRaw();
        setCols(raw.headers.map(String));
      } catch (e) {
        const m = e?.message ?? "Failed to load columns";
        setErr(m); onError?.(m);
      }
    })();
  }, [ensureRaw, onError]);

  // --- server build (POST to temp.py final())
  const generate = useCallback(async () => {
    setLoading(true); setErr(null);
    try {
      const raw = await ensureRaw();
      const body = {
        chartType: uiType,
        mapping: { x: uiMapping.x ?? "", y: Array.isArray(uiMapping.y) ? uiMapping.y : [] },
        options: { aggregation: uiOpts.aggregation, stacked: !!uiOpts.stacked, group_dates_by: uiOpts.group_dates_by },
        headers: raw.headers,
        rows: raw.rows,
      };
      const res = await fetch(serverUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const text = await res.text();
      if (!res.ok) {
        let details = text;
        try { details = JSON.stringify(JSON.parse(text), null, 2); } catch {}
        throw new Error(details);
      }
      const json = JSON.parse(text); // expected { type, data, options }
      setCfg(json);
      return json;
    } catch (e) {
      const m = e?.message ?? "Build failed";
      setErr(m); onError?.(m); setCfg(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [ensureRaw, uiType, uiMapping, uiOpts, serverUrl, onError]);

  const reset = useCallback(() => {
    setUiType(chartType);
    setUiMapping({
      x: mapping.x ?? "",
      y: Array.isArray(mapping.y) ? mapping.y : (mapping.y ? [mapping.y] : []),
    });
    setUiOpts({
      aggregation: options.aggregation ?? "sum",
      stacked: !!options.stacked,
      group_dates_by: options.group_dates_by ?? "monthly"
    });
    setErr(null);
  }, [chartType, mapping, options]);

  // --- PrimeReact data sources
  const chartTypeOptions = useMemo(
    () => ["bar", "line", "radar", "pie", "doughnut", "scatter"].map(t => ({ label: t, value: t })),
    []
  );
  const aggregationOptions = useMemo(
    () => ["sum", "avg", "count"].map(a => ({ label: a, value: a })),
    []
  );
  const columnOptions = useMemo(
    () => (cols || []).map(c => ({ label: c, value: c })),
    [cols]
  );

  const groupDatesByOptions = useMemo(
    () => ["daily", "monthly", "yearly", "weekly"].map(a => ({ label: a, value: a })),
    []
  )


  // --- UI sections
  const Actions = () => (
    <div className="flex flex-wrap align-items-center gap-2 w3-margin-bottom">
      <Button
        label={loading ? "Building…" : "Generate"}
        icon="pi pi-play"
        onClick={generate}
        disabled={loading}
        severity="primary"
        className="p-button-raised p-button-rounded"
        tooltip="Build chart from current selections"
        tooltipOptions={{ position: 'top' }}
      />
      <Button
        label="Reset"
        icon="pi pi-refresh"
        onClick={reset}
        disabled={loading}
        className="p-button-outlined p-button-rounded"
        tooltip="Reset fields and options to initial"
        tooltipOptions={{ position: 'top' }}
      />
      {err && (
        <Message
          severity="error"
          text={String(err).length > 140 ? String(err).slice(0, 140) + "…" : String(err)}
          className="w3-padding-small"
        />
      )}
    </div>
  );

  const Controls = () => (
    <div className="grid w-full">
      {/* Chart selection */}
      <div className="col-12 md:col-4">
        <Card className="w3-padding-small">
          <div className="text-sm font-semibold w3-margin-bottom">Chart</div>
          <Dropdown
            value={uiType}
            onChange={(e) => setUiType(e.value)}
            options={chartTypeOptions}
            placeholder="Select chart type"
            className="w-full"
            showClear={false}
          />
        </Card>
      </div>

      {/* Field mapping */}
      <div className="col-12 md:col-4">
        <Card className="w3-padding-small">
          <div className="text-sm font-semibold w3-margin-bottom">Fields</div>

          <div className="w3-small w3-text-grey w3-margin-bottom-4">X</div>
          <Dropdown
            value={uiMapping.x ?? ""}
            onChange={(e) => setUiMapping((m) => ({ ...m, x: e.value }))}
            options={columnOptions}
            placeholder="Select X column"
            className="w-full"
            filter
          />

          <Divider className="w3-margin-top w3-margin-bottom" />

          <div className="w3-small w3-text-grey w3-margin-bottom-4">Y (one or more)</div>
          <MultiSelect
            value={uiMapping.y ?? []}
            onChange={(e) => setUiMapping((m) => ({ ...m, y: e.value }))}
            options={columnOptions}
            placeholder="Select Y columns"
            className="w-full"
            display="chip"
            filter
            maxSelectedLabels={3}
          />

          <p className="w3-small w3-text-gray w3-margin-top">
            For <b>pie/doughnut</b>: X = category, Y = single numeric column.
            <br />
            For <b>scatter</b>: pick two numeric columns (X and first Y).
          </p>
        </Card>
      </div>

      {/* Options */}
      <div className="col-12 md:col-4">
        <Card className="w3-padding-small">
          <div className="text-sm font-semibold w3-margin-bottom">Options</div>

          <div className="w3-small w3-text-grey w3-margin-bottom-4">Aggregation</div>
          <Dropdown
            key={"aggregation_"+uiOpts.aggregation}
            value={uiOpts.aggregation}
            onChange={(e) => setUiOpts((o) => ({ ...o, aggregation: e.value }))}
            options={aggregationOptions}
            placeholder="Aggregation"
            className="w-full"
          />

          

          <div className="flex align-items-center gap-2 w3-margin-bottom-4 w3-margin-top">
            <Checkbox
              inputId="stackedOpt"
              checked={!!uiOpts.stacked}
              onChange={(e) => setUiOpts((o) => ({ ...o, stacked: e.checked }))}
            />
            <label htmlFor="stackedOpt" className="text-sm">Stacked</label>
          </div>

          <div className="w3-small w3-text-grey w3-margin-bottom-4  w3-margin-top">Group Dates By</div>
          <Dropdown
            key={"date_by_"+uiOpts.group_dates_by}
            value={uiOpts.group_dates_by}
            onChange={(e) => setUiOpts((o) => ({ ...o, group_dates_by: e.value }))}
            options={groupDatesByOptions}
            placeholder="Group Dates By"
            className="w-full"
          />

        </Card>
      </div>
    </div>
  );

  const ChartArea = () => (
    <Card className="w3-padding-small w3-half">
      <div style={{ minHeight: 260 }}>
        {!cfg ? (
          <div className="opacity-60 text-sm">
            No chart yet. Configure fields then click <b>Generate</b>.
          </div>
        ) : (
          <Chart
            type={cfg.type ?? uiType}
            data={cfg.data ?? {}}
            options={cfg.options ?? {}}
          />
        )}
      </div>
    </Card>
  );

  return (
    <div className="w-full ">
      <div class="w3-half">
        <Actions />
        <Controls />
      </div>
      
      <ChartArea />
    </div>
  );
}
