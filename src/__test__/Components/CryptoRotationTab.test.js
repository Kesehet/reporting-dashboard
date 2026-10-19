import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import CryptoRotationTab from '../../Components/CryptoRotationTab';
import { cryptoRequest } from '../../Services/CryptoRotationService';

jest.mock('../../Services/CryptoRotationService', () => ({ cryptoRequest: jest.fn() }));

const state = {
  keyring: { current_id: 'current-kid', keys: [
    { id: 'historic-key', algorithm: 'AES_ECB_PKCS7', active: false },
    { id: 'current-kid', algorithm: 'AES_GCM', active: true },
  ] },
  job: { state: 'idle', processed: 0, updated: 0 },
};

const authorize = async () => {
  fireEvent.change(screen.getByLabelText('Administrator token'), {
    target: { value: 'A'.repeat(36) },
  });
  await waitFor(() => expect(screen.getByText('Connected')).toBeInTheDocument(), { timeout: 2000 });
};

describe('CryptoRotationTab', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? state : { plaintext: 'Secret customer' });
  });

  it('keeps admin access in memory and hides keys', async () => {
    render(<CryptoRotationTab />);
    expect(screen.getByText(/token stays in this tab/i)).toBeInTheDocument();
    await authorize();
    expect(screen.getByText('historic-key')).toBeInTheDocument();
    expect(screen.getByText('AES_ECB_PKCS7 · Historical')).toBeInTheDocument();
    expect(screen.queryByText('Secret customer')).not.toBeInTheDocument();
  });

  it('decrypts using admin API but masks plaintext until operator reveals it', async () => {
    render(<CryptoRotationTab />);
    await authorize();
    fireEvent.change(screen.getByLabelText('Encrypted value'), { target: { value: 'v2:example' } });
    fireEvent.click(screen.getByText('Decrypt value'));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith(
      '/decrypt', 'A'.repeat(36), { value: 'v2:example' }
    ));
    await waitFor(() => expect(screen.getByText('••••••••••••••••')).toBeInTheDocument());
    expect(screen.queryByText('Secret customer')).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Reveal'));
    expect(screen.getByText('Secret customer')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Encrypted value'), { target: { value: 'other' } });
    expect(screen.queryByText('Secret customer')).not.toBeInTheDocument();
  });

  it('requires successful preflight and exact confirmation before migrating', async () => {
    cryptoRequest.mockImplementation(async (path) => {
      if (path === '/status') return state;
      if (path === '/preflight') return { ready: true, scanned: 10, values_to_rotate: 12, failures: 0 };
      if (path === '/start') return { run_id: 'a'.repeat(32), state: 'starting' };
      return {};
    });
    render(<CryptoRotationTab />);
    await authorize();
    expect(screen.getByText('Migrate now')).toBeDisabled();
    fireEvent.click(screen.getByText('Check compatibility'));
    await waitFor(() => expect(screen.getByText(/10 rows scanned/)).toBeInTheDocument());
    expect(screen.getByText('Migrate now')).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Confirmation/), { target: { value: 'MIGRATE_PII' } });
    expect(screen.getByText('Migrate now')).toBeEnabled();
    fireEvent.click(screen.getByText('Migrate now'));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith(
      '/start', 'A'.repeat(36), { confirm: 'MIGRATE_PII' }
    ));
  });

  it('blocks migration on a failed preflight', async () => {
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? state : {
      ready: false, scanned: 4, values_to_rotate: 0, failures: 1,
      examples: [{ table: 'Transactions', column: 'PrimarySSN', error: 'Missing key' }]
    });
    render(<CryptoRotationTab />);
    await authorize();
    fireEvent.click(screen.getByText('Check compatibility'));
    await waitFor(() => expect(screen.getByText(/Missing key/)).toBeInTheDocument());
    fireEvent.change(screen.getByLabelText(/Confirmation/), { target: { value: 'MIGRATE_PII' } });
    expect(screen.getByText('Migrate now')).toBeDisabled();
  });

  it('requires exact confirmation and a completed run before restoration', async () => {
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? {
      ...state, job: { state: 'completed', run_id: 'c'.repeat(32), processed: 100, updated: 90 }
    } : { state: 'starting' });
    render(<CryptoRotationTab />);
    await authorize();
    expect(screen.getByText('Restore previous encryption')).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Confirmation/), { target: { value: 'RESTORE_ORIGINAL' } });
    fireEvent.click(screen.getByText('Restore previous encryption'));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith(
      '/rollback', 'A'.repeat(36), { run_id: 'c'.repeat(32), confirm: 'RESTORE_ORIGINAL' }
    ));
  });
});
