import TransactionService from '../../Services/TransactionService';

describe('TransactionService', () => {
  it('fetches transaction rows and formats the date fields', async () => {
    const responseRows = [{
      AppStartDate: '2024-04-09T12:00:00Z',
      AppSubmitDate: '2024-04-09T12:30:00Z',
      AppUpdateDate: '2024-04-10T12:00:00Z',
      eCATrackingCode: 'SYNTHETIC-001',
    }];
    const fetchSpy = jest.spyOn(global, 'fetch').mockResolvedValue({
      status: 200,
      json: async () => responseRows,
    });
    const onload = jest.fn();

    try {
      const transactionService = new TransactionService(onload, '2024-04-09', '2024-04-11');
      await transactionService.fetchData();

      expect(Array.isArray(transactionService.json)).toBe(true);
      expect(transactionService.json.length).toBeGreaterThan(0);
      expect(transactionService.json[0].eCATrackingCode).toBe('SYNTHETIC-001');
      for (const dateField of ['AppStartDate', 'AppSubmitDate', 'AppUpdateDate']) {
        expect(transactionService.json[0][dateField]).toMatch(
          /^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2} (AM|PM)$/
        );
      }
      expect(onload).toHaveBeenCalledWith(transactionService.json);
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const requestUrl = new URL(fetchSpy.mock.calls[0][0], 'http://localhost');
      expect(requestUrl.searchParams.get('start_date')).toBe('2024-04-09');
      expect(requestUrl.searchParams.get('end_date')).toBe('2024-04-11');
    } finally {
      fetchSpy.mockRestore();
    }
  });
});
