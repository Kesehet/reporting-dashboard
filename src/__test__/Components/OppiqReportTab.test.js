import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import OppiqReportTab from '../../Components/OppiqReportTab';
import { downloadOppiqReport, getOppiqReport } from '../../Services/OppiqReportService';

jest.mock('../../Services/OppiqReportService', () => ({
    getOppiqReport: jest.fn(),
    downloadOppiqReport: jest.fn(),
}));

describe('OppiqReportTab', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        getOppiqReport.mockResolvedValue({
            headers: ['Banker_Name', 'Customer_Name', 'Lead_Status'],
            rows: [['Banker One', 'Customer One', 'Open']],
            total: 1,
        });
        downloadOppiqReport.mockResolvedValue();
    });

    it('loads a paginated report and displays SQL columns', async () => {
        render(<OppiqReportTab />);
        expect(await screen.findByText('Banker One')).toBeInTheDocument();
        expect(screen.getByText('Customer One')).toBeInTheDocument();
        expect(screen.getByText('Lead Status')).toBeInTheDocument();
        expect(getOppiqReport).toHaveBeenCalledWith(1, 50, expect.anything());
    });

    it('exports the complete report through the report service', async () => {
        render(<OppiqReportTab />);
        await screen.findByText('Banker One');
        fireEvent.click(screen.getByRole('button', { name: /Export as CSV/i }));
        await waitFor(() => expect(downloadOppiqReport).toHaveBeenCalledTimes(1));
    });

    it('shows an error if the backend fails', async () => {
        getOppiqReport.mockRejectedValueOnce(new Error('OPPIQ database is unavailable.'));
        render(<OppiqReportTab />);
        expect(await screen.findByRole('alert')).toHaveTextContent('OPPIQ database is unavailable.');
    });

    it('reloads the report on refresh', async () => {
        render(<OppiqReportTab />);
        await screen.findByText('Banker One');
        fireEvent.click(screen.getByRole('button', { name: /Refresh/i }));
        await waitFor(() => expect(getOppiqReport).toHaveBeenCalledTimes(2));
    });
});
