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

const loadStatus = async () => {
  await waitFor(() => expect(screen.getByText('historic-key')).toBeInTheDocument());
};

describe('CryptoRotationTab', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? state : { plaintext: 'Secret customer' });
  });

  it('keeps the key rotation screen compact and focused', () => {
    render(<CryptoRotationTab />);
    expect(screen.getByRole('heading', { level: 1, name: 'Key Rotation' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Key Rotation' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Check compatibility' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Migrate now' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Restore previous encryption' })).toBeDisabled();
    expect(screen.queryByText('Production migration')).not.toBeInTheDocument();
    expect(screen.queryByText('Prepare')).not.toBeInTheDocument();
    expect(screen.queryByText('Verify / restore')).not.toBeInTheDocument();
  });

  it('loads key metadata automatically without operator tokens', async () => {
    render(<CryptoRotationTab />);
    expect(screen.queryByLabelText('Administrator token')).not.toBeInTheDocument();
    await loadStatus();
    expect(screen.getByText('historic-key')).toBeInTheDocument();
    expect(screen.getByText('AES_ECB_PKCS7 · Historical')).toBeInTheDocument();
    expect(screen.queryByText('Secret customer')).not.toBeInTheDocument();
  });

  it('keeps manual decryption out of the key rotation screen', () => {
    render(<CryptoRotationTab />);
    expect(screen.queryByRole('heading', { name: 'Decrypt string' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Encrypted value')).not.toBeInTheDocument();
  });

  it('requires successful preflight and exact confirmation before migrating', async () => {
    cryptoRequest.mockImplementation(async (path) => {
      if (path === '/status') return state;
      if (path === '/preflight') return { ready: true, scanned: 10, values_to_rotate: 12, failures: 0 };
      if (path === '/start') return { run_id: 'a'.repeat(32), state: 'starting' };
      return {};
    });
    render(<CryptoRotationTab />);
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith('/status', undefined, expect.anything()));
    expect(screen.getByText('Migrate now')).toBeDisabled();
    fireEvent.click(screen.getByText('Check compatibility'));
    await waitFor(() => expect(screen.getByText(/10 rows scanned/)).toBeInTheDocument());
    expect(screen.getByText('Rows scanned').nextElementSibling).toHaveTextContent('10');
    expect(screen.getByText('Migrate now')).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Confirmation/), { target: { value: 'MIGRATE_PII' } });
    expect(screen.getByText('Migrate now')).toBeEnabled();
    fireEvent.click(screen.getByText('Migrate now'));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith(
      '/start', { confirm: 'MIGRATE_PII' }
    ));
  });

  it('blocks migration on a failed preflight', async () => {
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? state : {
      ready: false, scanned: 4, values_to_rotate: 0, failures: 1,
      examples: [{ table: 'Transactions', column: 'PrimarySSN', error: 'Missing key' }]
    });
    render(<CryptoRotationTab />);
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith('/status', undefined, expect.anything()));
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
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith('/status', undefined, expect.anything()));
    expect(screen.getByText('Restore previous encryption')).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Confirmation/), { target: { value: 'RESTORE_ORIGINAL' } });
    fireEvent.click(screen.getByText('Restore previous encryption'));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith(
      '/rollback', { run_id: 'c'.repeat(32), confirm: 'RESTORE_ORIGINAL' }
    ));
  });
});
