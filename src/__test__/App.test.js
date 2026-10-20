import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

jest.mock('../Components/reportLoginComponent', () => () => <div>Login Page</div>);
jest.mock('../Services/AuthorizationService', () => jest.fn().mockImplementation(() => ({
  isLoggedIn: () => false,
})));

test('unauthenticated users see the restored login before reports', () => {
  render(<App />);
  expect(screen.getByText('Login Page')).toBeInTheDocument();
});
