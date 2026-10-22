import { generateLineChartData } from '../../Utils/Components/Utils';

describe('line chart response safety', () => {
  test('valid datasets retain labels and numeric values', () => {
    expect(generateLineChartData({
      labels: ['Jan', 'Feb'],
      datasetMap: { Started: ['1,200', '15'] },
    })).toEqual(expect.objectContaining({
      labels: ['Jan', 'Feb'],
      datasets: [expect.objectContaining({ label: 'Started', data: [1200, 15] })],
    }));
  });

  test.each([null, undefined, {}, { labels: ['Jan'] }, { labels: ['Jan'], datasetMap: null }])(
    'missing datasets do not crash reporting page: %s', response => {
      expect(generateLineChartData(response)).toEqual({ labels: response?.labels || [], datasets: [] });
    }
  );

  test('non-array dataset values do not crash renderer', () => {
    expect(generateLineChartData({ labels: ['Jan'], datasetMap: { Started: null } }).datasets[0].data).toEqual([]);
  });
});
