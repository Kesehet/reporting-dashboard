import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import App from '../App';
import { MockServerHandler } from '../__test__/mocks/MockServerHandler';


// Mock the services
jest.mock('../Services/TransactionService');

// Mock the child components
jest.mock('../Components/reportHeaderComponent', () => () => <div>ReportHeaderComponent</div>);
jest.mock('../Components/reportFooterComponent', () => () => <div>ReportFooterComponent</div>);
jest.mock('../Components/tableComponent', () => () => <div>TableComponent</div>);
jest.mock('../Components/analyticsReportComponent', () => () => <div>AnalyticsReportComponent</div>);

test('renders dashboard without an authentication check', () => {

    render(<App />);

    expect(screen.getByText('ReportHeaderComponent')).toBeInTheDocument();
    expect(screen.getByText('ReportFooterComponent')).toBeInTheDocument();
});
