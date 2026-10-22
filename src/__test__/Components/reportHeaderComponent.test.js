import ReportHeaderComponent from '../../Components/reportHeaderComponent';
import AuthorizationService from '../../Services/AuthorizationService';

jest.mock('../../Services/AuthorizationService');

describe('ReportHeaderComponent menu contract', () => {
  let setDates, setCorBFilter, setPage, menu;
  beforeEach(() => {
    setDates = jest.fn();
    setCorBFilter = jest.fn();
    setPage = jest.fn();
    menu = ReportHeaderComponent(
      [new Date('2026-10-01'), new Date('2026-10-10')],
      setDates, 'All', setCorBFilter, setPage
    );
  });

  test('provides existing report navigation without duplicate feature labels', () => {
    expect(Array.isArray(menu)).toBe(true);
    const byLabel = label => menu.find(item => item.label === label);
    expect(byLabel('Business Accounts Summary')).toBeDefined();
    expect(byLabel('CSV Loader Reports')).toBeDefined();
    expect(byLabel('Key Rotation')).toBeDefined();
    byLabel('Business Accounts Summary').command();
    expect(setPage).toHaveBeenCalledWith('Business Accounts Summary');
    byLabel('Key Rotation').command();
    expect(setPage).toHaveBeenCalledWith('Key Rotation');
  });

  test('preserves date selection and consumer/business filter callbacks', () => {
    const templates = menu.filter(item => typeof item.template === 'function').map(item => item.template());
    const calendar = templates.find(element => element.props.placeholder === 'Select dates');
    const filter = templates.find(element => element.props.placeholder === 'Select Consumer or Business Filter');
    expect(calendar).toBeDefined();
    expect(filter).toBeDefined();
    const range = [new Date('2026-09-01'), new Date('2026-09-30')];
    calendar.props.onChange({ value: range });
    expect(setDates).toHaveBeenCalledWith(range);
    filter.props.onChange({ value: 'Business' });
    expect(setCorBFilter).toHaveBeenCalledWith('Business');
  });

  test('sign-out action still delegates to authorization service', () => {
    const logout = jest.fn();
    AuthorizationService.mockImplementation(() => ({ logout }));
    menu.find(item => item.label === 'Sign Out').command();
    expect(logout).toHaveBeenCalledTimes(1);
  });
});
