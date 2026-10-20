import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import CryptoRotationTab from '../../Components/CryptoRotationTab';
import { cryptoRequest } from '../../Services/CryptoRotationService';

jest.mock('../../Services/CryptoRotationService', () => ({ cryptoRequest: jest.fn() }));

const initial = {
  keyring: { current_id: 'current-kid', keys: [
    { id: 'historic-key', algorithm: 'AES_ECB_PKCS7', active: false },
    { id: 'current-kid', algorithm: 'AES_GCM', active: true },
  ] },
  job: { state: 'idle', processed: 0, updated: 0 },
};

describe('CryptoRotationTab', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? initial : {});
  });

  it('offers exactly two actions, with no manual confirmation or decryption fields', async () => {
    render(<CryptoRotationTab />);
    await screen.findByText('historic-key');
    expect(screen.getAllByRole('button')).toHaveLength(2);
    expect(screen.getByRole('button', { name: 'Rotate' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Restore' })).toBeDisabled();
    expect(screen.queryByLabelText('Confirmation')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Administrator token')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Encrypted value')).not.toBeInTheDocument();
    expect(screen.getByText('AES_ECB_PKCS7 · Historical')).toBeInTheDocument();
  });

  it('starts the entire server-managed rotation with one click', async () => {
    cryptoRequest.mockImplementation(async (path) => {
      if (path === '/status') return initial;
      if (path === '/rotate') return { run_id: 'a'.repeat(32), state: 'starting' };
      throw new Error('Unexpected manual operation');
    });
    render(<CryptoRotationTab />);
    await screen.findByText('historic-key');
    fireEvent.click(screen.getByRole('button', { name: 'Rotate' }));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith('/rotate', {}));
    await waitFor(() => expect(screen.getByTestId('crypto-job-state')).toHaveTextContent('starting'));
    expect(screen.getByText('Recovery run ID:').textContent).toContain('a'.repeat(32));
    expect(screen.getByRole('button', { name: 'Rotate' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Restore' })).toBeDisabled();
    expect(cryptoRequest).not.toHaveBeenCalledWith('/keys/rotate', expect.anything());
    expect(cryptoRequest).not.toHaveBeenCalledWith('/start', expect.anything());
  });

  it('restores a completed rotation using the current recovery run id', async () => {
    cryptoRequest.mockImplementation(async (path) => path === '/status' ? {
      ...initial,
      job: { state: 'completed', run_id: 'c'.repeat(32), processed: 100, updated: 90, preflight: { scanned: 100, failures: 0 } },
    } : { state: 'starting', run_id: 'c'.repeat(32) });
    render(<CryptoRotationTab />);
    await screen.findByText('historic-key');
    expect(screen.getByRole('button', { name: 'Restore' })).toBeEnabled();
    expect(screen.getByText('Preflight failures').nextElementSibling).toHaveTextContent('0');
    fireEvent.click(screen.getByRole('button', { name: 'Restore' }));
    await waitFor(() => expect(cryptoRequest).toHaveBeenCalledWith(
      '/rollback', { run_id: 'c'.repeat(32), confirm: 'RESTORE_ORIGINAL' }
    ));
    await waitFor(() => expect(screen.getByTestId('crypto-job-state')).toHaveTextContent('restoring'));
  });

  it('blocks both actions while a worker runs', async () => {
    cryptoRequest.mockResolvedValue({ ...initial, job: { state: 'committing', run_id: 'b'.repeat(32) } });
    render(<CryptoRotationTab />);
    await screen.findByText('historic-key');
    expect(screen.getByRole('button', { name: 'Rotate' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Restore' })).toBeDisabled();
  });

  it('only offers recovery when reconciliation is required', async () => {
    cryptoRequest.mockResolvedValue({
      ...initial,
      job: { state: 'reconciliation_required', run_id: 'd'.repeat(32), error: 'SQL commit outcome needs reconciliation' },
    });
    render(<CryptoRotationTab />);
    await screen.findByText('historic-key');
    expect(screen.getByRole('button', { name: 'Rotate' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Restore' })).toBeEnabled();
    expect(screen.getByRole('alert')).toHaveTextContent('reconciliation');
  });

  it('displays a failed preflight without creating an extra action', async () => {
    cryptoRequest.mockResolvedValue({
      ...initial,
      job: {
        state: 'failed', run_id: 'e'.repeat(32), error: 'Migration aborted; SQL transaction rolled back',
        preflight: { scanned: 4, values_to_rotate: 0, failures: 1,
          examples: [{ table: 'Transactions', column: 'PrimarySSN', error: 'Missing key' }] },
      },
    });
    render(<CryptoRotationTab />);
    await screen.findByText('historic-key');
    expect(screen.getByText(/Missing key/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Rotate' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Restore' })).toBeDisabled();
  });
});
