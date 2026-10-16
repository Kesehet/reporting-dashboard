import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import ReportHeaderComponent from '../../Components/reportHeaderComponent';
import AuthorizationService from '../../Services/AuthorizationService';

jest.mock('../../Services/AuthorizationService');

const mockLogout = jest.fn();
AuthorizationService.mockImplementation(() => {
    return {
        logout: mockLogout,
    };
});

test('renders ReportHeaderComponent and checks elements', () => {
    const dates = [new Date(), new Date()];
    const setDates = jest.fn();

    render(<ReportHeaderComponent dates={dates} setDates={setDates} />);

    // Check for logo rendering
    const logo = screen.getByAltText(/First National Bank, Pennsylvania Logo/i);
    expect(logo).toBeInTheDocument();

    // Check if the title is rendered
    const title = screen.getByText((content, element) => {
        return element.tagName.toLowerCase() === 'p' && content.includes('eStore® Common App Reporting Dashboard');
    });
    expect(title).toBeInTheDocument();

    // Check if menubar is rendering
    const menubar = screen.getByRole('menubar');
    expect(menubar).toBeInTheDocument();

    // Check if the Calendar is rendering
    const calendar = screen.getByPlaceholderText(/Select dates/i);
    expect(calendar).toBeInTheDocument();
});

test('handles menu interactions', async () => {
    const dates = [new Date(), new Date()];
    const setDates = jest.fn();

    render(<ReportHeaderComponent dates={dates} setDates={setDates} />);

    const calendar = screen.getByPlaceholderText(/Select dates/i);
    fireEvent.change(calendar, {target: {value: '2024-06-28'}});
       
    // Simulate clicking on the Profile menu
    const profileMenu = screen.getByText(/Profile/i);
    fireEvent.click(profileMenu);

    const preferences = screen.getByText(/Preferences/i);
    expect(preferences).toBeInTheDocument();

    const account = screen.getByText(/Account/i);
    fireEvent.click(account);

    const signOut = screen.getByText(/Sign Out/i);
    expect(signOut).toBeInTheDocument();
    fireEvent.click(signOut);
    
});
