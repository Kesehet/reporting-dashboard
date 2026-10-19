import DecryptionService from '../../Services/DecryptionService';
import fetchMock from 'jest-fetch-mock';

describe('DecryptionService API contract', () => {
  beforeEach(() => { fetchMock.enableMocks(); fetchMock.resetMocks(); });

  it('uses only a POST body for ciphertext without an access token', async () => {
    fetch.mockResponseOnce(JSON.stringify({ plaintext: 'hello 🌙' }));
    expect(await new DecryptionService().decrypt('v2:encoded')).toBe('hello 🌙');
    const [url, options] = fetch.mock.calls[0];
    expect(url).toMatch(/\/tools\/decrypt$/);
    expect(url).not.toContain('encoded');
    expect(options).toMatchObject({
      method: 'POST', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ciphertext: 'v2:encoded' }),
    });
    expect(options.headers['X-Decrypt-Access-Key']).toBeUndefined();
  });

  it.each([
    [422, 'Unable to decrypt'],
    [503, 'not available'], [413, 'too large'], [500, 'request failed'],
  ])('hides unsafe server error body on HTTP %i', async (status, expected) => {
    fetch.mockResponseOnce(JSON.stringify({ error: 'private-key-value debug stack' }), { status });
    await expect(new DecryptionService().decrypt('x')).rejects.toThrow(expected);
  });

  it('rejects missing and malformed plaintext payloads', async () => {
    fetch.mockResponseOnce(JSON.stringify({ plaintext: null }));
    await expect(new DecryptionService().decrypt('x')).rejects.toThrow('Invalid decryption response');
    fetch.mockResponseOnce('not json');
    await expect(new DecryptionService().decrypt('x')).rejects.toThrow('Invalid decryption response');
  });

  it('does not persist or print sensitive data', async () => {
    const setItem = jest.spyOn(Storage.prototype, 'setItem');
    const log = jest.spyOn(console, 'log').mockImplementation(() => {});
    fetch.mockResponseOnce(JSON.stringify({ plaintext: 'sensitive' }));
    await new DecryptionService().decrypt('v2:blob');
    expect(setItem).not.toHaveBeenCalled();
    expect(log).not.toHaveBeenCalled();
    setItem.mockRestore();
    log.mockRestore();
  });
});
