# Reporting Dashboard Handbook

## 1. Overview
The eSTORE® Common App Reporting Dashboard brings together the bank's production, deposit, lending, and document insights in one guided workspace. Sidebar groupings such as “Basic,” “Reports,” and “Loans & Deposits Reports” map business roles to the pages they open, while the fixed header keeps the brand and page filters in view for every decision-maker.【F:src/Components/SidebarComponent.jsx†L24-L111】【F:src/App.jsx†L493-L507】

The handbook is written for branch leaders, market executives, analysts, and any business stakeholder who tracks KPI movement without touching SQL or code. Each section below explains the experience these users see and the insight they can gather from the dashboard cards, charts, and tables.

## 2. Login & Access
The landing screen offers two sign-in paths: a form-based username and password workflow plus Microsoft single sign-on (SSO). Both options sit inside a branded welcome panel that acknowledges successful authentication and error conditions in plain language.【F:src/Components/reportLoginComponent.jsx†L22-L218】

* **Standard login** – Credentials post to the `/login` endpoint. Successful validation stores a time-bounded token, the user’s display name, and a calculated expiration timestamp in browser storage so the session persists across page loads.【F:src/Services/AuthorizationService.jsx†L10-L33】
* **Microsoft SSO** – Business users can launch a Microsoft popup, reuse an already cached account, and sign out when done. The flow sets the same display name, token, and expiration markers before refreshing the app so the rest of the dashboard opens immediately.【F:src/Components/reportLoginComponent.jsx†L63-L218】

### Session handling and caching in plain terms
* **What is stored?** The browser keeps your security token, its expiration time, your preferred start/end dates, and whether you filtered for consumer or business metrics, so the dashboard remembers your context the next time you open it.【F:src/App.jsx†L35-L76】【F:src/Services/AuthorizationService.jsx†L26-L58】
* **How long is it valid?** Each login sets a timer based on the configured session timeout minutes. When that timer passes, the token is cleared and you will be prompted to sign in again to protect secure data.【F:src/Services/AuthorizationService.jsx†L26-L58】
* **Why does caching help?** Frequently viewed chart data is temporarily saved on the server for up to 24 hours. That means repeat visits feel fast, while longer refreshes only occur when data is recalculated or filters change.【F:api-server/cache_manager.py†L10-L44】【F:api-server/serve.py†L124-L208】
* **Balancing freshness vs. speed** – When you adjust dates or apply a new branch filter, the system requests a fresh dataset. Otherwise it serves the cached copy, striking a balance between up-to-the-minute numbers and responsive navigation.【F:src/Services/ChartDataService.jsx†L1-L35】【F:api-server/serve.py†L158-L208】

## 3. Dashboard Components
The application shell is assembled in `App.jsx`. Each major component below contributes to the end-user experience.

| Component | Purpose & Experience | Visual Form | Interactions |
| --- | --- | --- | --- |
| **SidebarLayout** | Organizes navigation into business-friendly sections, shows a collapsible menu, and displays welcome text sourced from the signed-in user’s name.【F:src/Components/SidebarComponent.jsx†L4-L138】 | Layout container | Collapse/expand, sectioned buttons, metrics teaser |
| **ReportHeaderComponent** | Supplies the date range picker, consumer vs. business filter, page navigation buttons, and sign-out control that drive the rest of the content.【F:src/Components/reportHeaderComponent.jsx†L1-L138】 | Toolbar widgets | Calendar, dropdown, navigation commands |
| **AnalyticsReportComponent** | Presents the year-to-date, quarterly, and current-quarter application mix in pie, line, and table pairings for quick trend checks.【F:src/Components/analyticsReportComponent.jsx†L1-L78】 | Cards containing charts & tables | Opens detail dialogs via ChartCard |
| **ChartCard** | Wraps any chart/table in a consistent card, opens a larger dialog, and lets users capture a screenshot for reporting decks.【F:src/Utils/Components/ChartCard.jsx†L1-L94】 | Card with dialog | Click to expand, “Take Screenshot” button |
| **FNB* visualization widgets** | Reusable chart components (bar, stacked bar, line, pie, combo, tables, flip cards, multi-tables) normalize colors, legends, and loading states across the dashboard.【F:src/App.jsx†L15-L33】【F:src/Utils/Components/FNBStackedBarChart.jsx†L1-L110】【F:src/Utils/Components/CardReport.jsx†L1-L200】 | Charts, tables, KPI cards | Loading spinners, legends, CSV exports |
| **BORAsync / BOR** | Fetches branch-level abandonment and business deposit detail asynchronously, showing progress, branch selectors, and drill-down dialogs.【F:src/Utils/Components/BORAsync.jsx†L1-L196】【F:src/App.jsx†L97-L142】 | Accordion + tables | Branch filter, dialogs, progress meter |
| **MultiFilterTable** | Offers a self-service filter workspace where users can slice transactions through multi-select filters and view the resulting table immediately.【F:src/App.jsx†L301-L307】 | Interactive table | Column filters, downloadable data |
| **CardReport** | Summarizes KPI cards and exposes underlying detail via export and view buttons, making KPI rollups auditable.【F:src/Utils/Components/CardReport.jsx†L12-L200】 | KPI tiles | Refresh, export CSV, detail dialog |
| **ReportFooterComponent** | Reinforces branding at the bottom of every page to signal the official nature of the dashboard.【F:src/App.jsx†L493-L507】 | Footer | Static |

## 4. Chart Overview
The dashboard relies on a repeatable chart vocabulary:

* **Pie and donut charts** show product mix share for started, submitted, and approved applications—ideal for spotting which offerings drive volume.【F:src/Components/analyticsReportComponent.jsx†L16-L63】
  * 📸 Insert screenshot of “Application Volume By Product (All Started Apps) – Year to Date” here for illustration.
* **Line charts** track trajectories such as monthly application counts or decline rates, helping users see momentum and seasonality.【F:src/Components/analyticsReportComponent.jsx†L32-L77】
  * 📸 Insert screenshot of “Application Volume By Product (All Submitted Apps)” here for illustration.
* **Stacked bar charts** compare categories like new vs. existing customers, secured vs. unsecured commitments, or balance types across channels.【F:src/App.jsx†L150-L339】【F:src/Utils/Components/FNBStackedBarChart.jsx†L1-L110】
  * 📸 Insert screenshot of “New vs Existing Customer Report” here for illustration.
* **Bar charts** support ranking views (top multi-product combinations, abandonment reasons) so teams can quickly identify leaders and outliers.【F:src/App.jsx†L113-L270】
  * 📸 Insert screenshot of “Top 10 Multi-Product Combinations” here for illustration.
* **Combo bar + line charts** show counts alongside rate lines for loan commitments, blending two KPIs in one panel.【F:src/App.jsx†L343-L392】
  * 📸 Insert screenshot of “Loan Accounts and Commitments” here for illustration.
* **KPI card grids** provide quick totals and averages with one-click exports for deeper audit trails.【F:src/Utils/Components/CardReport.jsx†L90-L174】
  * 📸 Insert screenshot of “Spot & Current Balance Account Insights” cards here for illustration.
* **Detailed tables** translate every chart into sortable rows ready for export, ensuring quantitative validation is available.【F:src/App.jsx†L423-L486】【F:src/Utils/Components/CardReport.jsx†L175-L200】
  * 📸 Insert screenshot of “Monthly Business Deposits” table here for illustration.

## 5. Chart-by-Chart Explanation
This section mirrors the navigation pages. Every bullet highlights the business question, metric, reading guide, and interactivity.

### Analytics (Graphs)
* **Application Volume by Product – Year to Date**: Three pie/table pairs cover started, submitted, and opened applications, showing product mix share and raw counts. Review the legend to see which offerings dominate the funnel; hover or open the dialog for table-level numbers.【F:src/Components/analyticsReportComponent.jsx†L16-L36】
  * 📸 Insert screenshot of “Application Volume By Product (All Started Apps) – Year to Date” here.
* **Application Volume by Product – Rolling Trends**: Line charts plot monthly activity for each stage, helping analysts identify surges or dips in specific product lines.【F:src/Components/analyticsReportComponent.jsx†L37-L63】
  * 📸 Insert screenshot of “Application Volume By Product (All Submitted Apps)” here.
* **Quarterly Mix Views**: Quarterly pies and tables summarize segment share for leadership scorecards, while quarter-by-quarter line charts reveal seasonality.【F:src/Components/analyticsReportComponent.jsx†L64-L78】
  * 📸 Insert screenshot of “Application Volume By Product Quarterly (All Started Apps)” here.
* **Current Quarter Spotlight**: Current-quarter pies and tables spotlight the latest activity to monitor goal attainment mid-quarter.【F:src/Components/analyticsReportComponent.jsx†L69-L78】
  * 📸 Insert screenshot of “Application Volume by Product Current Quarter (All Submitted Apps)” here.

### In-Branch Originated & Business Deposit Reports
* **In-Branch Originated Report**: Accordion-driven tables reveal branch-by-branch totals for started, submitted, and opened apps with interactive dialogs for deeper cell data. Use the branch selector to focus on a region or the entire network.【F:src/App.jsx†L97-L111】【F:src/Utils/Components/BORAsync.jsx†L1-L196】
  * 📸 Insert screenshot of “In-Branch Originated Report” here.
* **Business Deposit Reports**: Mirrors the BOR experience but filters to deposit-specific metrics and offers an application-type toggle for banker-assisted vs. online views.【F:src/App.jsx†L103-L111】【F:src/Utils/Components/BORAsync.jsx†L1-L83】
  * 📸 Insert screenshot of “Business Deposit Reports” here.

### Multi Product Reports
* **Top 10 Multi-Product Combinations / Cross Sell / Single Product + Cross Sell**: Ranked bars and paired tables surface the most common product bundles. Use the dialog view for full data exports and apply other dashboard filters to see how mix shifts by timeframe.【F:src/App.jsx†L113-L142】
  * 📸 Insert screenshot of “Top 10 Cross Sell Products” here.

### Customer & Product Reports
* **New vs Existing Customer Report**: A stacked bar chart compares new vs. existing customers, backed by a table for precise counts and percentages. Read the x-axis as the timeframe and each bar segment as customer status.【F:src/App.jsx†L150-L162】
  * 📸 Insert screenshot of “New vs Existing Customer Report” here.
* **Declined Report**: Line and bar views display decline trends and root reasons, with downloadable tables for audit follow-up. Examine the line chart for trajectory and the bar chart for categorical comparisons.【F:src/App.jsx†L163-L188】
  * 📸 Insert screenshot of “Declined Report” here.
* **Funding Type Report**: Combines a line chart and detailed table with million-dollar subheaders, highlighting funding sources over time. Use the table to pivot by category and the line to monitor trends.【F:src/App.jsx†L282-L299】
  * 📸 Insert screenshot of “Funding Type Report” here.
* **Lending & Deposit Control Report**: A multi-table canvas capturing lending and deposit compliance metrics with consistent column widths for readability. Export sections for regulatory reviews.【F:src/App.jsx†L277-L280】
  * 📸 Insert screenshot of “Lending & Deposit Control Report” here.
* **Loan Commitments**: KPI cards summarize started, submitted, and approved volumes. Flip cards reveal alternate time horizons, while combo and stacked charts split secured vs. unsecured commitments with supportive tables for averages and totals.【F:src/App.jsx†L343-L392】【F:src/Utils/Components/CardReport.jsx†L90-L174】
  * 📸 Insert screenshot of “Loan Accounts and Commitment – Quarterly Analysis” here.
* **Spot & Current Balance Amounts**: KPI cards feed into stacked charts for both online and in-branch applications, showing opening deposits vs. current balances by channel.【F:src/App.jsx†L308-L339】
  * 📸 Insert screenshot of “Spot & Current Balance Amounts” here.

### Operational Tables
* **All Transactions**: Full-detail table of every transaction in scope, ready for export and additional filtering offline.【F:src/App.jsx†L190-L197】
  * 📸 Insert screenshot of “All Transactions” here.
* **All Filters Table**: Interactive sandbox for analysts to mix filters and instantly view results, ideal for custom what-if questions.【F:src/App.jsx†L301-L307】
  * 📸 Insert screenshot of “All Filters Table” here.
* **Monthly Report Tables**: Dropdown-controlled tables cover in-branch, consumer-facing, business deposits, BPM/CRIF entries, and eCA vs. BPM comparisons for year-to-date monitoring.【F:src/App.jsx†L400-L476】
  * 📸 Insert screenshot of “Monthly Report – Common App (In Branch)” here.
* **Customer Document Center**: Two tables summarize document center activity and monthly insights, highlighting adoption of digital document workflows.【F:src/App.jsx†L480-L486】
  * 📸 Insert screenshot of “Customer Document Center” here.

### Abandonment Suite
* **Abandonment Report**: The main card surfaces abandonment summaries with branch-level drill-downs. Additional cards break down abandonment by week, month, year, type, and zero-product follow-up, all responsive to the application-type selector at the top.【F:src/App.jsx†L200-L270】
  * 📸 Insert screenshot of “Abandonment Report by Week” here.

## 6. Chart Generation Logic (Business Explanation)
Each chart follows the same flow:
1. **User context** – The calendar, consumer/business toggle, and page settings store your chosen filters in local storage so they travel with every data request.【F:src/App.jsx†L35-L76】【F:src/Services/ChartDataService.jsx†L1-L35】
2. **Chart request** – The front-end service appends dates, branch IDs, and other parameters to the `/charts/<name>` endpoint using the saved token for secure access.【F:src/Services/ChartDataService.jsx†L1-L35】
3. **Server orchestration** – The Flask service checks whether a matching chart is already cached. If not, it coordinates one “owner” request to fetch fresh numbers while others wait, ensuring accuracy without duplicate workloads.【F:api-server/serve.py†L124-L208】【F:api-server/helper/chat_serve.py†L1-L73】
4. **Standardized output** – `charts.py` assembles responses through helper builders (pie, line, tables) so each visualization receives predictable labels, datasets, and rows.【F:api-server/charts.py†L1-L33】
5. **Caching** – Results are saved with a 24-hour lifetime, giving fast responses until filters change or the cache expires.【F:api-server/cache_manager.py†L10-L44】

### Accuracy, freshness, and reliability
* Shared helper functions in `charts.py` reuse filters and calculations across reports, reducing the risk of inconsistent numbers.【F:api-server/charts.py†L1-L33】
* Cache coordination prevents partially computed charts from leaking into the UI and automatically retries if a prior attempt failed.【F:api-server/serve.py†L158-L208】【F:api-server/helper/chat_serve.py†L1-L73】
* Build deployments or manual cache clears regenerate stored results, guaranteeing that new data or fixes reach business users promptly.【F:api-server/cache_manager.py†L45-L121】

## 7. Overall Flow of the App
1. **Log in** via standard credentials or Microsoft SSO to unlock the dashboard workspace.【F:src/Components/reportLoginComponent.jsx†L22-L218】
2. **Set filters** using the header calendar and consumer/business toggle; preferences persist until changed.【F:src/Components/reportHeaderComponent.jsx†L1-L138】【F:src/App.jsx†L35-L76】
3. **Fetch data** as you navigate pages—each view triggers chart API calls with your chosen filters and stored token.【F:src/Services/ChartDataService.jsx†L1-L35】【F:src/App.jsx†L86-L486】
4. **Review visuals** inside ChartCards, tables, and KPI tiles. Expand any card for fullscreen review or export snapshots for presentations.【F:src/Utils/Components/ChartCard.jsx†L65-L94】【F:src/Utils/Components/CardReport.jsx†L90-L174】
5. **Stay current** as caching keeps performance high while nightly refreshes and manual cache clears ensure data accuracy. Logout resets the session when you are done.【F:api-server/cache_manager.py†L10-L121】【F:src/Services/AuthorizationService.jsx†L61-L68】

## 8. `chart.py` – Business Perspective
`chart.py` is the dashboard’s chart library. It pulls in domain-specific modules (BOR, abandonment, funding type, monthly reports, new vs. existing customers, and more) and outputs standardized chart shapes so every visualization on the dashboard is consistent.【F:api-server/charts.py†L1-L33】

* **What it does** – Converts raw transaction results into pie slices, line series, stacked bars, or table rows depending on the chart name requested.
* **How it works conceptually** – When the server calls `getChartData`, the function checks which chart is needed, applies the same filters you set in the UI, and packages the results with clear labels and headers.【F:api-server/charts.py†L1-L33】
* **Supported visualizations** – Pie charts for product mix, line charts for trends, bar and stacked bar charts for comparisons, tables for detail, and KPI structures for card reports, mirroring what you see in the dashboard pages.【F:src/App.jsx†L86-L486】
* **Business benefits** – Because each chart uses the same builders, numbers stay consistent across pages, and new charts can reuse established logic. For example, loan commitment KPIs and tables use shared helpers to ensure totals, averages, and secured vs. unsecured splits reconcile automatically.【F:src/App.jsx†L343-L392】【F:api-server/charts.py†L1-L33】

> Example: “chart.py automatically converts raw application counts into the ‘Application Volume by Product’ pies and tables, so leaders see updated product share without touching the underlying SQL.”

## 9. Maintenance and Updates
* **Refresh cadence** – Charts refresh instantly when you change filters or when the 24-hour cache expires. KPI cards include a Refresh button to pull the latest numbers on demand.【F:src/Utils/Components/CardReport.jsx†L90-L111】【F:api-server/cache_manager.py†L10-L44】
* **Knowing data is current** – Loading spinners, progress bars, and “No data” messages inform you when data is fetching or if the selection returns zero results, signaling that the system is working and simply awaiting results.【F:src/Utils/Components/BORAsync.jsx†L19-L96】【F:src/Utils/Components/FNBStackedBarChart.jsx†L7-L56】
* **When something looks wrong** – If a chart stays blank or shows outdated numbers, first try the refresh/export controls, then reach out to the analytics support contact. Support can trigger cache clears or review the chart builder logs via the `/clear_cache` and logging utilities on the server.【F:api-server/serve.py†L209-L280】【F:api-server/cache_manager.py†L45-L121】

## 10. Optional Enhancements
* **Screenshot appendix** – Use the built-in “Take Screenshot” button inside each ChartCard to capture current-state images for a visual appendix that stays aligned with the live dashboard.【F:src/Utils/Components/ChartCard.jsx†L65-L94】
* **Chart legend glossary** – Document the color legends used by stacked bars and pies so business teams interpret colors consistently across reports.【F:src/Utils/Components/FNBStackedBarChart.jsx†L58-L109】
* **Mini FAQ suggestions**:
  * *Why does a chart show “No data”?* – It means no records met the selected criteria; try broadening the date range or removing filters.【F:src/Utils/Components/FNBStackedBarChart.jsx†L32-L56】
  * *What if an export button does nothing?* – Ensure the card’s detail dialog opens; export buttons rely on the same data service that feeds the dialog view.【F:src/Utils/Components/CardReport.jsx†L56-L170】
  * *How do I confirm my filters applied?* – The header dropdowns and branch selectors display the active choice, and cards like BORAsync summarize the selected branches above the results.【F:src/Components/reportHeaderComponent.jsx†L90-L138】【F:src/Utils/Components/BORAsync.jsx†L70-L119】

---
Use this handbook as the quick-reference companion for day-to-day dashboard use. Pair it with fresh screenshots and quarterly KPI notes to keep leadership briefings current and actionable.
