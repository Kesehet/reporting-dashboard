
import TransactionService from '../../Services/TransactionService';

describe('TransactionService', () => {

  it('TransactionService json should not be empty after data fetch', async () => {
    const transactionService = new TransactionService(null, '2024-04-09', '2024-04-11');
    await transactionService.fetchData();
    expect(transactionService.json).not.toBeNil();
    expect(transactionService.json.size > 0);
  });  

});

