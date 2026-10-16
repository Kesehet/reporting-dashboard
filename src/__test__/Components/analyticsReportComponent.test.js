import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { setupJestCanvasMock } from 'jest-canvas-mock';
import AnalyticsReportComponent from './../../Components/analyticsReportComponent';
import transactionsData from './../mocks/data/transactionsData.json';


describe('AnalyticsReportComponent', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    setupJestCanvasMock();
  });

  it('renders the chart component', () => {
    render(<AnalyticsReportComponent transactions={transactionsData} setShowReport='true' />);
    expect(screen.getByText('Single vs. Multi-Product Applications (Exhibit A)'));
  });

});
