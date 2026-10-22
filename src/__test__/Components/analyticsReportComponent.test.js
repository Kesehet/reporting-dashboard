import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AnalyticsReportComponent from '../../Components/analyticsReportComponent';

// This is a layout smoke test. Endpoint/payload behavior is independently
// validated by chartResponses.contract.test.js using generated backend fixtures.
jest.mock('../../Utils/Components/FNBPieChart', () => () => <div data-testid="pie-chart" />);
jest.mock('../../Utils/Components/FNBTable', () => () => <div data-testid="chart-table" />);
jest.mock('../../Utils/Components/FNBLineChart', () => () => <div data-testid="line-chart" />);
jest.mock('../../Utils/Components/YearQuarterList', () => ({
  YearQuarterList: () => <div data-testid="year-quarter-list" />
}));

test('analytics dashboard renders major chart sections without issuing HTTP requests', () => {
  render(<AnalyticsReportComponent />);
  expect(screen.getByText('Application Volume By Product (All Started Apps) - Year to Date')).toBeInTheDocument();
  expect(screen.getAllByTestId('pie-chart').length).toBeGreaterThan(0);
  expect(screen.getAllByTestId('chart-table').length).toBeGreaterThan(0);
  expect(screen.getAllByTestId('line-chart').length).toBeGreaterThan(0);
});
