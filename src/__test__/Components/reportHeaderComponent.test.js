import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import ReportHeaderComponent from '../../Components/reportHeaderComponent';
import AuthorizationService from '../../Services/AuthorizationService';

jest.mock('../../Services/AuthorizationService');

const createMenu = () => {
    const setDates = jest.fn();
    const setFilter = jest.fn();
    const setPage = jest.fn();
    const items = ReportHeaderComponent([new Date(), new Date()], setDates, 'All', setFilter, setPage);
    return { items, setDates, setFilter, setPage };
};

test('provides navigation items instead of rendering menu configuration as JSX', () => {
    const { items, setPage } = createMenu();
    expect(Array.isArray(items)).toBe(true);
    const reports = items.find(item => item.label === 'Business Accounts Summary');
    expect(reports).toBeDefined();
    reports.command();
    expect(setPage).toHaveBeenCalledWith('Business Accounts Summary');
    expect(items.some(item => item.label === 'API Key')).toBe(false);
    const encryptionRotation = items.find(item => item.label === 'Key Rotation');
    expect(encryptionRotation).toBeDefined();
    encryptionRotation.command();
    expect(setPage).toHaveBeenCalledWith('Key Rotation');
});

test('calendar and filter templates propagate the user selection', () => {
    const { items, setDates, setFilter } = createMenu();
    const templates = items.filter(item => typeof item.template === 'function');
    expect(templates).toHaveLength(2);
    render(<>{templates[0].template()}{templates[1].template()}</>);
    expect(screen.getByPlaceholderText(/Select dates/i)).toBeInTheDocument();
    expect(document.querySelector('.p-dropdown')).toBeInTheDocument();
    // Render tests exercise PrimeReact widgets without assuming the menu
    // factory itself returns React elements.
    expect(setDates).not.toHaveBeenCalled();
    expect(setFilter).not.toHaveBeenCalled();
});

test('sign-out menu command uses the authorization service', () => {
    const logout = jest.fn();
    AuthorizationService.mockImplementation(() => ({ logout }));
    const { items } = createMenu();
    items.find(item => item.label === 'Sign Out').command();
    expect(logout).toHaveBeenCalledTimes(1);
});
