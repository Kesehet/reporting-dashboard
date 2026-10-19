import ReportHeaderComponent from '../../Components/reportHeaderComponent';
it('registers Business String Decryption among normal sidebar tools', () => {
  const setPage = jest.fn();
  const items = ReportHeaderComponent([new Date(), new Date()], jest.fn(), 'All', jest.fn(), setPage);
  const item = items.find(x => x.label === 'Business String Decryption');
  expect(item.section).toBe('Tools');
  item.command();
  expect(setPage).toHaveBeenCalledWith('Business String Decryption');
});
