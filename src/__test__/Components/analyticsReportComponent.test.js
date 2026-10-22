import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnalyticsReportComponent from './../../Components/analyticsReportComponent';

// Test report composition, not live requests or chart.js canvas internals.
// Endpoint payloads are separately covered by the chart-contract suite.
jest.mock('../../Utils/Components/FNBPieChart', () => () => null);
jest.mock('../../Utils/Components/FNBTable', () => () => null);
jest.mock('../../Utils/Components/FNBLineChart', () => () => null);

describe('AnalyticsReportComponent', () => {
  test('keeps year-to-date, quarterly and custom report sections visible', () => {
    render(<AnalyticsReportComponent />);
    expect(screen.getByText('Application Volume By Product (All Started Apps) - Year to Date')).toBeInTheDocument();
    expect(screen.getByText('Application Volume By Product (All Submitted Apps) - Year to Date')).toBeInTheDocument();
    expect(screen.getByText('Application Volume By Product (All Approved Apps) - Year to Date')).toBeInTheDocument();
    expect(screen.getAllByText('Application Volume By Product Quarterly (All Started Apps)').length).toBeGreaterThan(0);
    expect(screen.getByText('Custom Quarterly Analytics Table')).toBeInTheDocument();
  });
});
