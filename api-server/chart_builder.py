from collections import defaultdict, Counter
from statistics import mean
from datetime import datetime

MONTH_ALIASES = {
    "jan","january","feb","february","mar","march","apr","april","may","jun","june",
    "jul","july","aug","august","sep","sept","september","oct","october","nov","november","dec","december"
}

def _is_number(x):
    try:
        if x is None or (isinstance(x, str) and x.strip() == ""):
            return False
        float(x)
        return True
    except Exception:
        return False

def _try_parse_date(x):
    if not isinstance(x, str):
        return None
    x_strip = x.strip()
    # quick month-name check (Jan, January, etc.)
    if x_strip.lower() in MONTH_ALIASES:
        # Use month index for ordering; day=1, current year fallback
        try:
            m = list(MONTH_ALIASES).index(x_strip.lower()) % 12 + 1
        except Exception:
            m = datetime.strptime(x_strip[:3], "%b").month
        return datetime(datetime.utcnow().year, m, 1)
    # common formats
    fmts = [
        "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%Y-%m", "%Y/%m", "%b %Y", "%B %Y", "%d %b %Y", "%d %B %Y",
        "%Y"  # year-only
    ]
    for f in fmts:
        try: 
            return datetime.strptime(x_strip, f)
        except Exception:
            pass
    return None

def _infer_col_types(headers, rows):
    col_types = []  # "numeric" | "date" | "category"
    for j, h in enumerate(headers):
        cells = [r[j] for r in rows if j < len(r)]
        nums = sum(1 for c in cells if _is_number(c))
        dates = sum(1 for c in cells if _try_parse_date(str(c)))
        # choose the majority signal
        if nums >= dates and nums >= len(cells) * 0.5:
            col_types.append("numeric")
        elif dates > 0 and dates >= len(cells) * 0.5:
            col_types.append("date")
        else:
            col_types.append("category")
    return col_types

def _order_labels_if_time_like(labels):
    # Try to sort by detected dates; if 70% parse, keep sorted.
    parsed = [(lbl, _try_parse_date(str(lbl))) for lbl in labels]
    good = [p for _, p in parsed if p]
    if len(good) >= 0.7 * len(labels):
        return [lbl for lbl, _ in sorted(parsed, key=lambda t: (t[1] or datetime.max))]
    # specific month name ordering
    if all(isinstance(l, str) and l.strip().lower() in MONTH_ALIASES for l in labels):
        month_order = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
        idx = {m:i for i,m in enumerate(month_order)}
        def keyf(s): 
            return idx.get(s.strip().lower()[:3], 999)
        return sorted(labels, key=keyf)
    return labels  # keep input order

def auto_chartjs_config(headers, rows, opts=None):
    """
    Heuristically builds a Chart.js v4 config from unknown tabular data.

    headers: list[str]
    rows: list[list]
    opts (optional): {
        "title": str,
        "stacked": bool,
        "legend": "top"|"left"|"bottom"|"right"|"hidden",
        "chart_type": "bar"|"line"|"pie"|"doughnut"|"radar"|"scatter",  # force a type
        "aggregation": "sum"|"avg"|"count"|None,  # default "sum" when grouping by label
        "colors": [hex,...],
    }
    """
    if not headers or not rows:
        raise ValueError("headers and rows must be non-empty")
    n_cols = len(headers)
    col_types = _infer_col_types(headers, rows)
    palette = (opts or {}).get("colors") or [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
        "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
    ]
    legend_pos = (opts or {}).get("legend", "top")
    display_legend = legend_pos != "hidden"
    stacked = bool((opts or {}).get("stacked", False))
    forced_type = (opts or {}).get("chart_type")
    aggregation = (opts or {}).get("aggregation")
    title = (opts or {}).get("title")

    # === Determine structure intent ===
    numeric_idxs = [i for i,t in enumerate(col_types) if t == "numeric"]
    non_numeric_idxs = [i for i,t in enumerate(col_types) if t != "numeric"]
    date_idxs = [i for i,t in enumerate(col_types) if t == "date"]

    # Case A: Only two columns and both numeric -> scatter
    if not forced_type and n_cols == 2 and len(numeric_idxs) == 2:
        forced_type = "scatter"

    # Choose label (x/category) column:
    # Prefer a non-numeric (date or category). Fall back to first column.
    if non_numeric_idxs:
        label_i = non_numeric_idxs[0]
    else:
        label_i = 0  # may be numeric; scatter/radar will kick in
    label_name = headers[label_i]

    # Choose value columns:
    value_idxs = [i for i in range(n_cols) if i != label_i and col_types[i] == "numeric"]
    # If none and we had only numerics, handle special cases later.
    value_names = [headers[i] for i in value_idxs]

    # === Build datasets depending on pattern ===
    def group_rows_by_label():
        groups = defaultdict(list)
        for r in rows:
            if label_i < len(r):
                groups[str(r[label_i])].append(r)
        return groups

    # Type decision tree (can be overridden)
    chart_type = forced_type
    if not chart_type:
        if len(numeric_idxs) == n_cols:  # all numeric
            if n_cols == 2:       # 2 numeric cols -> scatter
                chart_type = "scatter"
            elif n_cols <= 8:     # compact numeric matrix -> radar
                chart_type = "radar"
            else:
                chart_type = "bar"
        else:
            # If label looks time-like -> line, else bar (pie if 1 metric and few categories)
            time_like = (col_types[label_i] == "date" or
                         all(isinstance(r[label_i], str) and r[label_i].strip().lower() in MONTH_ALIASES
                             for r in rows if len(r) > label_i))
            if time_like:
                chart_type = "line"
            else:
                if len(value_idxs) == 1:
                    # Consider pie/doughnut if distinct categories are small
                    distinct = len(set(str(r[label_i]) for r in rows if len(r) > label_i))
                    chart_type = "doughnut" if distinct <= 8 else "bar"
                else:
                    chart_type = "bar"

    # === Scatter special case ===
    if chart_type == "scatter" and len(numeric_idxs) >= 2:
        x_i, y_i = numeric_idxs[0], numeric_idxs[1]
        points = []
        for r in rows:
            if x_i < len(r) and y_i < len(r) and _is_number(r[x_i]) and _is_number(r[y_i]):
                points.append({"x": float(r[x_i]), "y": float(r[y_i])})
        data = {"datasets": [{
            "label": f"{headers[y_i]} vs {headers[x_i]}",
            "data": points,
            "showLine": False,
            "borderColor": palette[0],
            "backgroundColor": palette[0],
        }]}
        options = {
            "responsive": True,
            "plugins": {
                "legend": {"display": display_legend, "position": legend_pos if display_legend else "top"},
                "title": {"display": bool(title), "text": title or ""}
            },
            "scales": {"x": {"title": {"display": True, "text": headers[x_i]}},
                       "y": {"title": {"display": True, "text": headers[y_i]}}}
        }
        return {"type": chart_type, "data": data, "options": options}

    # === Non-scatter paths ===
    # When label repeats, aggregate (default sum)
    groups = group_rows_by_label()
    labels = list(groups.keys())
    # If time-like labels, sort them chronologically
    labels = _order_labels_if_time_like(labels)

    # Decide aggregation
    agg = ("sum" if aggregation in (None, "", "none") else aggregation).lower()

    def reduce_vals(vals, how):
        if how == "sum":   return sum(vals) if vals else None
        if how == "avg":   return mean(vals) if vals else None
        if how == "count": return float(len(vals))
        raise ValueError("aggregation must be one of: sum, avg, count/None")

    # If no numeric value columns (e.g., one label col only), fabricate a count
    if not value_idxs:
        value_idxs = []
        for j in range(n_cols):
            if j != label_i:
                value_idxs.append(j)
                value_names = [headers[j]]
                break
        agg = "count"

    # Build series per value col
    series_by_value = {headers[j]: [] for j in value_idxs}
    for lbl in labels:
        bucket = groups[lbl]
        for j in value_idxs:
            vals = []
            for r in bucket:
                if j < len(r) and _is_number(r[j]):
                    vals.append(float(r[j]))
                elif agg == "count":
                    vals.append(1.0)
            series_by_value[headers[j]].append(reduce_vals(vals, agg))

    # Datasets
    datasets = []
    for i, name in enumerate(series_by_value.keys()):
        color = palette[i % len(palette)]
        ds = {"label": name, "data": series_by_value[name],
              "borderColor": color, "backgroundColor": color}
        if chart_type == "line":
            ds["tension"] = 0.3
            ds["fill"] = False
        if chart_type in ("pie","doughnut","radar"):
            # per-segment colors for pies; radar uses single color
            if chart_type in ("pie","doughnut"):
                ds["backgroundColor"] = [palette[k % len(palette)] for k in range(len(series_by_value[name]))]
        datasets.append(ds)

    data = {"labels": labels, "datasets": datasets}

    # Options
    options = {
        "responsive": True,
        "plugins": {
            "legend": {"display": display_legend, "position": legend_pos if display_legend else "top"},
            "title": {"display": bool(title), "text": title or ""}
        }
    }

    # Scales (skip for pie/doughnut)
    if chart_type not in ("pie","doughnut"):
        if chart_type == "radar":
            options["scales"] = {
                "r": {"title": {"display": False, "text": ""}, "pointLabels": {"centerPointLabels": True}}
            }
        else:
            options["scales"] = {
                "x": {"stacked": stacked, "title": {"display": True, "text": headers[label_i]}},
                "y": {"stacked": stacked, "title": {"display": True, "text": "Value"}}
            }

    return {"type": chart_type, "data": data, "options": options}


def final(requests):
    req = requests.json
    all_headers = requests.json.get("headers")
    all_rows = requests.json.get("rows")
    x_axis_header = req.get("mapping").get("x")
    y_axis_headers = req.get("mapping").get("y")
    headers, rows = get_rows_for_headers(all_headers,all_rows, [x_axis_header] + y_axis_headers)


    return auto_chartjs_config( headers, rows ,{
        "aggregation": req.get("options").get("aggregation"),
        "stacked": req.get("options").get("stacked"),
        "chart_type": req.get("chartType"),

    })

def get_rows_for_headers(headers, rows, selected_headers, date_segmentation_requested="monthly"):
    '''
    Filters out the rows to include only the selected headers.

    Parameters:
        headers : list of all headers, e.g., ["A", "B", "C", "D"]
        rows : list of rows, e.g., [["A1", "B1", "C1", "D1"], ["A2", "B2", "C2", "D2"]]
        selected_headers : list of headers to keep, e.g., ["A", "C"]

    Returns:
        final_headers : list of selected headers
        final_rows : list of rows with only values corresponding to selected headers
    '''
    # Map header to its index for quick lookup
    header_index_map = {header: idx for idx, header in enumerate(headers)}

    # Filter rows based on selected headers
    final_rows = []
    for row in rows:
        filtered_row = []
        for header in selected_headers:
            idx = header_index_map.get(header)
            if idx is not None and idx < len(row):
                # Doing a quick check to set date based grouping frequency
                check_if_date = set_date_group(row[idx], date_segmentation_requested)
                filtered_row.append(check_if_date)
            else:
                filtered_row.append(None)  # Handle missing data gracefully
        final_rows.append(filtered_row)

    final_headers = selected_headers
    return final_headers, final_rows

from datetime import datetime

def set_date_group(value, segment):
    '''
    Checks if the input `value` is a string and represents a valid ISO-like datetime.
    If valid, parses the date and formats it based on the `segment` value.

    Parameters:
        value (str): A string in the format "YYYY-MM-DDTHH:MM:SS".
        segment (str): The grouping segment - "monthly", "weekly", "yearly", or "daily".

    Returns:
        str: A formatted string based on the segment:
             - "monthly": "MonthName `Year" (e.g., "August `2025")
             - "weekly": "Week <week_number> of `Year" (e.g., "Week 35 of `2025")
             - "yearly": "`Year" (e.g., "`2025")
             - "daily": "YYYY-MM-DD" (e.g., "2025-08-29")
             - If parsing fails or segment is unsupported, returns the original value.
    '''
    if isinstance(value, str):
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            segment = segment.lower()
            if segment == "monthly":
                return f"{date_obj.strftime('%B')} `{date_obj.year}"
            elif segment == "weekly":
                week_number = date_obj.isocalendar()[1]
                return f"Week {week_number} of `{date_obj.year}"
            elif segment == "yearly":
                return f"`{date_obj.year}"
            elif segment == "daily":
                return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            pass  # value is not a valid date string
    return value