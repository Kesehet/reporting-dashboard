import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

jest.mock('../Components/reportLoginComponent', () => () => <div>Login Page</div>);
jest.mock('../Services/AuthorizationService', () => ({
  __esModule: true,
  default: class MockAuthorizationService {
    isLoggedIn() { return false; }
  }
}));

test('unauthenticated users see login before any reporting page', () => {
  render(<App />);
  expect(screen.getByText('Login Page')).toBeInTheDocument();
});
