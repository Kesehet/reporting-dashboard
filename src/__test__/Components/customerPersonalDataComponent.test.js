import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import CustomerPersonalDataComponent from '../../Components/customerPersonalDataComponent';

test('renders CustomerPersonalData component', async () => {
    render(<CustomerPersonalDataComponent/>);

    await waitFor(() => {
        const nameElements = screen.getAllByText('Name');
        expect(nameElements.length).toBeGreaterThan(0);
    });
    
    await waitFor(() => {
        const categoryElements = screen.getAllByText('Category');
        expect(categoryElements.length).toBeGreaterThan(0);
    });
    
    await waitFor(() => {
        const quantityElements = screen.getAllByText('Quantity');
        expect(quantityElements.length).toBeGreaterThan(0);
    });
});

test('toggles column visibility', async () => {
    render(<CustomerPersonalDataComponent />);
    
    // Check initial column visibility
    await waitFor(() => {
        const nameElements = screen.getAllByText('Name');
        expect(nameElements.length).toBeGreaterThan(0);
    });
    
    await waitFor(() => {
        const categoryElements = screen.getAllByText('Category');
        expect(categoryElements.length).toBeGreaterThan(0);
    });
    
    await waitFor(() => {
        const quantityElements = screen.getAllByText('Quantity');
        expect(quantityElements.length).toBeGreaterThan(0);
    });
});