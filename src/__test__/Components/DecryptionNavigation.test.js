import ReportHeaderComponent from '../../Components/reportHeaderComponent';

it('hides Business String Decryption while keeping Key Rotation in the sidebar', () => {
  const setPage = jest.fn();
  const items = ReportHeaderComponent([new Date(), new Date()], jest.fn(), 'All', jest.fn(), setPage);

  expect(items.some(item => item.label === 'Business String Decryption')).toBe(false);
  const apiKey = items.find(item => item.label === 'API Key');
  expect(apiKey).toBeDefined();
  expect(apiKey.section).toBe('Administration');
  apiKey.command();
  expect(setPage).toHaveBeenCalledWith('API Key');
  const rotation = items.find(item => item.label === 'Key Rotation');
  expect(rotation).toBeDefined();
  expect(rotation.section).toBe('Administration');
  rotation.command();
  expect(setPage).toHaveBeenCalledWith('Key Rotation');
});
