import React from 'react';
import { render, screen } from '@testing-library/react';
import ReportLoginComponent from '../../Components/reportLoginComponent';

jest.mock('../../Services/msalInstance', () => ({
  bootMsalActiveAccount: jest.fn(async () => null),
  msalLoginPopup: jest.fn(async () => null),
  msalLogoutPopup: jest.fn(async () => null),
}));

test('original LDAP and Microsoft login choices appear together', async () => {
  localStorage.clear();
  render(<ReportLoginComponent />);
  expect(screen.getByPlaceholderText('User Name')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /SSO Sign In/i })).toBeInTheDocument();
});
