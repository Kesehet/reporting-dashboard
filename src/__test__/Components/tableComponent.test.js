import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import TableComponent from '../../Components/tableComponent';
import { write, utils } from "xlsx"
import fetchMock from 'jest-fetch-mock';
import { __esModule } from 'quill';
import FileSaver from 'file-saver';


jest.mock('xlsx', () => ({
    __esModule: true,
    
        utils: {
          json_to_sheet: jest.fn(),
        },
        write: jest.fn(),
    }

))



jest.mock('file-saver', () => ({ saveAs: jest.fn()}));

describe('TableComponent', () => {
    const mockTransactions = [
      { id: 1, name: 'Transaction 1', amount: 100 },
      { id: 2, name: 'Transaction 2', amount: 200 }
    ];
    const mockColumns = [
      { field: 'name', header: 'Name' },
      { field: 'amount', header: 'Amount' }
    ];
    const mockVisibleColumns = ['name', 'amount'];
    const mockColumnGroups = {
      'Group 1': ['name'],
      'Group 2': ['amount']
    };

    let setVisibleColumns;
    let setShowReport;

    beforeEach(() => {
      setVisibleColumns = jest.fn();
      setShowReport = jest.fn();
    });

    test('renders TableComponent with transactions', async () => {
      render(
        <TableComponent
          transactions={mockTransactions}
          loading={false}
          columns={mockColumns}
          visibleColumns={mockVisibleColumns}
          setVisibleColumns={setVisibleColumns}
          setShowReport={setShowReport}
          columnGroups={mockColumnGroups}
        />
      );

      expect(screen.getByTestId('menubar-container')).toBeInTheDocument();
      expect(screen.getByTestId('datatable-container')).toBeInTheDocument();
    //  expect(screen.getAllByTestId('Column')).toHaveLength(2);
    });

    test('export to Excel functionality', async () => {
     // await waitFor(() =>
        render(
          <TableComponent
            transactions={mockTransactions}
            loading={false}
            columns={mockColumns}
            visibleColumns={mockVisibleColumns}
            setVisibleColumns={setVisibleColumns}
            setShowReport={setShowReport}
            columnGroups={mockColumnGroups}
          />
      //  ),
      );

      const exportButton = await screen.findByLabelText('Export');
      fireEvent.click(exportButton);
    
      expect(utils.json_to_sheet).toHaveBeenCalled();
      expect(write).toHaveBeenCalled();
      expect(FileSaver.saveAs).toHaveBeenCalled();
    });

    test('renders Menubar with correct items', () => {
      render(
        <TableComponent
          transactions={mockTransactions}
          loading={false}
          columns={mockColumns}
          visibleColumns={mockVisibleColumns}
          setVisibleColumns={setVisibleColumns}
          setShowReport={setShowReport}
          columnGroups={mockColumnGroups}
        />
      );
      const menubar = screen.getByTestId('menubar-container') 
      expect(menubar).toBeInTheDocument();
      const AnalyticsButton = screen.getByLabelText('Analytics');
      expect(AnalyticsButton).toBeInTheDocument();
      const ExportButton = screen.getByLabelText('Export');
      expect(ExportButton).toBeInTheDocument();
    });

    test('renders MultiSelect', () => {
      render(
        <TableComponent
          transactions={mockTransactions}
          loading={false}
          columns={mockColumns}
          visibleColumns={mockVisibleColumns}
          setVisibleColumns={setVisibleColumns}
          setShowReport={setShowReport}
          columnGroups={mockColumnGroups}
        />
      );
      
      expect(screen.getByTestId('multiselect-container')).toBeInTheDocument();

    });
});