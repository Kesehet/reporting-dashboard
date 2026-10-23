import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import ApiKeyTab from '../../Components/ApiKeyTab';

const today = new Date().toISOString().slice(0, 10);

beforeEach(() => {
  localStorage.clear();
  global.fetch = jest.fn();
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: jest.fn().mockResolvedValue(undefined) },
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

test("gets today's key using the normal login header and copies it", async () => {
  localStorage.setItem('token', 'ldap-signed-token');
  localStorage.setItem('login_method', 'ldap');
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ api_key: 'ak1.sample.signed', date: today, timezone: 'UTC' }),
  });
  render(<ApiKeyTab />);
  await screen.findByText('ak1.sample.signed');
  const [url, opts] = fetch.mock.calls[0];
  expect(url).toContain('/api-key/current');
  expect(opts.headers.Authorization).toBe('ldap-signed-token');
  expect(opts.headers['X-API-KEY']).toBeUndefined();
  expect(opts.cache).toBe('no-store');
  expect(opts.credentials).toBe('same-origin');
  fireEvent.click(screen.getByRole('button', { name: /Copy API key/i }));
  await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledWith('ak1.sample.signed'));
  expect(screen.getByRole('status')).toHaveTextContent('Copied');
});

test('uses unchanged Microsoft SSO header', async () => {
  localStorage.setItem('token', 'msal-signed-token');
  localStorage.setItem('login_method', 'msal');
  fetch.mockResolvedValue({ ok: true, json: async () => ({ api_key: 'ak1.signed', date: today }) });
  render(<ApiKeyTab />);
  await screen.findByText('ak1.signed');
  expect(fetch.mock.calls[0][1].headers['X-MSAL-ID-Token']).toBe('msal-signed-token');
  expect(fetch.mock.calls[0][1].credentials).toBe('same-origin');
});

test('never shows or copies a key when endpoint refuses access', async () => {
  fetch.mockResolvedValue({ ok: false, json: async () => ({ error: 'Unauthorized' }) });
  render(<ApiKeyTab />);
  await screen.findByRole('alert');
  expect(screen.getByRole('button', { name: /Copy API key/i })).toBeDisabled();
  expect(navigator.clipboard.writeText).not.toHaveBeenCalled();
});

test('does not copy yesterday\'s key after midnight UTC', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ api_key: 'expired-key', date: '2000-01-01' }) });
  render(<ApiKeyTab />);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  expect(screen.queryByText('expired-key')).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Copy API key/i })).toBeDisabled();
});
