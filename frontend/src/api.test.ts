import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('frontend API configuration compatibility', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ tick: 0 }) }));
  });
  afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); });

  it.each([
    ['defaults to the local backend', '', '', 'http://127.0.0.1:8000'],
    ['accepts the original frontend setting', '', 'http://127.0.0.1:8001/', 'http://127.0.0.1:8001'],
    ['prefers the shared setting when both exist', 'http://127.0.0.1:8002/', 'http://127.0.0.1:8001', 'http://127.0.0.1:8002'],
  ])('%s', async (_description, current, legacy, expected) => {
    vi.stubEnv('VITE_API_BASE_URL', current);
    vi.stubEnv('VITE_API_URL', legacy);
    const { townApi } = await import('./api');
    await townApi.state(new AbortController().signal);
    expect(fetch).toHaveBeenCalledWith(`${expected}/state`, expect.objectContaining({ method: 'GET' }));
  });
});
