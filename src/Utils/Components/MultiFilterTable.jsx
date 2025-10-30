import React, { useEffect, useMemo, useState } from 'react';
import { MultiSelect } from 'primereact/multiselect';
import FNBDataTable from './FNBDataTable';
import MultiFilterChart from './MultiFilterChart';
import OneShotChart from './OneShotChart';

// Constant list for filter options (unchanged)
const FILTER_OPTIONS = [
  { label: 'Zero Product Applications', value: 'ZeroProductApps' },
  { label: 'Exclude Zero Product Applications', value: 'excludeZeroProductApps' },
  { label: 'Loan Apps', value: 'loanApps' },
  { label: 'Deposit Apps', value: 'depositApps' },
  { label: 'Mixed Apps', value: 'mixedApps' },
  { label: 'Single Product Applications', value: 'singleProductApps' },
  { label: 'Multi Produt Applications', value: 'multiProductApps' },
  { label: 'Exclude Bot Data', value: 'excludeBotData' },
  { label: 'Include Bot generated', value: 'includeBotData' },
  { label: 'Exclude LOS Submitted', value: 'appStatusforDashboard' },
  { label: 'Started', value: 'startedApps' },
  { label: 'Submitted', value: 'submittedApps' },
  { label: 'Opened/Approved', value: 'approvedApps' }
  

];

/**
 * Define mutually-exclusive groups (radio groups).
 * Only one value from each group can be selected at the same time.
 */
const RADIO_GROUPS = {
  ZeroProducts: ['ZeroProductApps', 'excludeZeroProductApps'],
  AppType: ['loanApps', 'depositApps', 'mixedApps'],
  AppStatus : ['startedApps','submittedApps','approvedApps'],
  ProductType: ['singleProductApps','multiProductApps'],
  BotData: ['excludeBotData', 'includeBotData'],
  LOS : ['LOS Submitted'],
};

// Build a value -> group lookup for fast checks
const valueToGroup = Object.entries(RADIO_GROUPS).reduce((acc, [group, values]) => {
  values.forEach(v => { acc[v] = group; });
  return acc;
}, {});

const MultiFilterTable = ({
  styleNow = {},
  initialFilters = [],
  extraParams: extraParamsIn = {},
  onFiltersChange,
  multiselectProps = {},
}) => {
  const [selectedFilters, setSelectedFilters] = useState(initialFilters);

  // Sanitize initial filters so there is at most one selection per group
  useEffect(() => {
    if (!initialFilters?.length) return;
    const seenGroups = new Set();
    const cleaned = [];
    for (const v of initialFilters) {
      const g = valueToGroup[v];
      if (g) {
        if (seenGroups.has(g)) continue; // skip duplicates in same group
        seenGroups.add(g);
      }
      cleaned.push(v);
    }
    setSelectedFilters(cleaned);
  }, []); // run once on mount

  // Combine external extraParams with filters managed here
  const extraParams = useMemo(
    () => ({
      ...extraParamsIn,
      filters: selectedFilters,
    }),
    [extraParamsIn, selectedFilters]
  );

  // Force FNBDataTable to refresh when filters change (FNBDataTable listens to `data`)
  const refreshKey = useMemo(
    () => `filters:${(selectedFilters || []).join('|')}`,
    [selectedFilters]
  );

  // Human-readable summary
  const filterSummary = useMemo(() => {
    if (!selectedFilters || selectedFilters.length === 0) {
      return 'This table has no filters selected ';
    }
    const labels = selectedFilters.map((val) => {
      const match = FILTER_OPTIONS.find((o) => o.value === val);
      return match?.label ?? String(val);
    });

    if (labels.length === 1) return `This table has ${labels[0]}`;
    if (labels.length === 2) return `This table has ${labels[0]} and ${labels[1]}`;
    const head = labels.slice(0, -1).join(', ');
    const tail = labels[labels.length - 1];
    return `This table has ${head}, and ${tail}`;
  }, [selectedFilters]);

  const globalFilterSumamry = useMemo(()=>{
    let CorBFilter = localStorage.getItem("CorBFilter");
    let corbfilter = ""
    if(CorBFilter != "All"){
        corbfilter =  `for ${CorBFilter}`
    }
    return ` ${corbfilter}. We are showing all txns between ${localStorage.getItem("start_date")} and ${localStorage.getItem("end_date")}.`
  }, [selectedFilters])

  /**
   * Enforce "radio within group":
   * - Identify added values in this change.
   * - For each added value, remove any other selection from its group.
   */
  const handleChange = (e) => {
    const next = e.value || [];

    // calculate set differences
    const added = next.filter(v => !selectedFilters.includes(v));
    // const removed = selectedFilters.filter(v => !next.includes(v)); // not needed for logic

    let normalized = [...next];

    if (added.length > 0) {
      // If multiple were added (rare with MultiSelect UI), apply rule in order
      for (const v of added) {
        const g = valueToGroup[v];
        if (!g) continue; // not in any group; ignore
        // Keep v, remove any other from the same group
        normalized = normalized.filter(x => valueToGroup[x] !== g || x === v);
      }
    }

    setSelectedFilters(normalized);
    if (typeof onFiltersChange === 'function') {
      onFiltersChange(normalized);
    }
  };

  const clearFilters = () => {
    setSelectedFilters([]);
    if (typeof onFiltersChange === 'function') {
      onFiltersChange([]);
    }
  };

  return (
    <div className="p-fluid" style={{ width: '100%' }}>
      <div className="p-field" style={{ marginBottom: '1rem' }}>
        <label htmlFor="multiFilterSelect" style={{ display: 'block', fontWeight: 600, marginBottom: 6 }}>
          Filters
        </label>

        <div className="p-d-flex p-ai-center" style={{ gap: '.5rem' }}>
          <MultiSelect
            id="multiFilterSelect"
            value={selectedFilters}
            options={FILTER_OPTIONS}
            onChange={handleChange}
            placeholder="Select filters"
            display="chip"
            filter
            showSelectAll={false}          // keep off to avoid selecting conflicting items
            optionLabel="label"
            optionValue="value"
            className="w-full"
            {...multiselectProps}
          />

          <button
            type="button"
            onClick={clearFilters}
            className="p-button p-component p-button-text"
            aria-label="Clear filters"
            title="Clear filters"
          >
            Clear
          </button>
        </div>

        <p style={{ margin: '0 0 .5rem', fontWeight: 500 }}>{filterSummary + globalFilterSumamry}</p>
      </div>

      <FNBDataTable
        key={refreshKey}
        data={'All Filters Table'}
        extraParams={extraParams}
        styleNow={styleNow}
      />
      <hr/>
      <h4>Work In Progress</h4>
      <MultiFilterChart
        key={refreshKey+"-C"}
        serverUrl={(process.env.NODE_ENV ==='production'? (window.location.href+"api"):"http://localhost:5000")+"/chart_builder"}
        data={'All Filters Table'}
        extraParams={extraParams}
        title="Sample Chart"
      />
    </div>
  );
};

export default MultiFilterTable;
