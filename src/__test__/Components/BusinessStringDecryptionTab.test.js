import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BusinessStringDecryptionTab from '../../Components/BusinessStringDecryptionTab';

const mockDecrypt = jest.fn();
jest.mock('../../Services/DecryptionService', () => {
  return jest.fn().mockImplementation(() => ({ decrypt: (...args) => mockDecrypt(...args) }));
});

const fill = () => {
  fireEvent.change(screen.getByLabelText('Encrypted string'), { target: { value: ' v2:example ' } });
};
beforeEach(() => mockDecrypt.mockReset());

it('renders the dashboard card and prevents empty submissions', () => {
  render(<BusinessStringDecryptionTab />);
  expect(screen.getByRole('heading', { name: 'Business String Decryption' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Decrypt string' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Encrypted string'), { target: { value: 'data' } });
  expect(screen.getByRole('button', { name: 'Decrypt string' })).toBeEnabled();
  expect(screen.queryByLabelText('Tool access token')).not.toBeInTheDocument();
  expect(mockDecrypt).not.toHaveBeenCalled();
});

it('submits trimmed ciphertext, shows read-only Unicode output and preserves the source', async () => {
  mockDecrypt.mockResolvedValueOnce('secret ✅');
  render(<BusinessStringDecryptionTab />);
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Decrypt string' }));
  expect(await screen.findByLabelText('Decrypted string')).toHaveValue('secret ✅');
  expect(screen.getByLabelText('Decrypted string')).toHaveAttribute('readonly');
  expect(screen.getByLabelText('Encrypted string')).toHaveValue(' v2:example ');
  expect(mockDecrypt).toHaveBeenCalledWith('v2:example');
});

it('disables form fields and duplicate submissions while pending', async () => {
  let release;
  mockDecrypt.mockImplementationOnce(() => new Promise(resolve => { release = resolve; }));
  render(<BusinessStringDecryptionTab />);
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Decrypt string' }));
  expect(screen.getByRole('button', { name: 'Decrypting...' })).toBeDisabled();
  expect(screen.getByLabelText('Encrypted string')).toBeDisabled();
  expect(mockDecrypt).toHaveBeenCalledTimes(1);
  release('done');
  expect(await screen.findByLabelText('Decrypted string')).toHaveValue('done');
});

it('does not retain a stale result after failure or edits', async () => {
  mockDecrypt.mockResolvedValueOnce('first secret').mockRejectedValueOnce(new Error('No decryption'));
  render(<BusinessStringDecryptionTab />);
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Decrypt string' }));
  expect(await screen.findByLabelText('Decrypted string')).toHaveValue('first secret');
  fireEvent.click(screen.getByRole('button', { name: 'Decrypt string' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('No decryption');
  expect(screen.queryByLabelText('Decrypted string')).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Encrypted string'), { target: { value: 'new' } });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

it('clears ciphertext and plaintext', async () => {
  mockDecrypt.mockResolvedValueOnce('visible secret');
  render(<BusinessStringDecryptionTab />);
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Decrypt string' }));
  await screen.findByLabelText('Decrypted string');
  fireEvent.click(screen.getByRole('button', { name: 'Clear all' }));
  expect(screen.getByLabelText('Encrypted string')).toHaveValue('');
  expect(screen.queryByLabelText('Decrypted string')).not.toBeInTheDocument();
});

it('copies output only after explicit user action', async () => {
  mockDecrypt.mockResolvedValueOnce('copy secret');
  const writeText = jest.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
  render(<BusinessStringDecryptionTab />);
  fill();
  fireEvent.click(screen.getByRole('button', { name: 'Decrypt string' }));
  await screen.findByLabelText('Decrypted string');
  expect(writeText).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Copy result' }));
  await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Copied'));
  expect(writeText).toHaveBeenCalledWith('copy secret');
});
