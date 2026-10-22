import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

jest.mock('../Components/reportLoginComponent', () => () => <div>Login Page</div>);

test('unauthenticated users see the restored login before reports', () => {
  localStorage.clear();
  render(<App />);
  expect(screen.getByText('Login Page')).toBeInTheDocument();
});
