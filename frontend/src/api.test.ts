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

  it('sends an operator key only on mutations and uses the real shortage route', async () => {
    const { townApi, setOperatorKey } = await import('./api');
    setOperatorKey('operator-test-key');
    const signal = new AbortController().signal;
    await townApi.state(signal);
    expect(fetch).toHaveBeenLastCalledWith(expect.stringContaining('/state'),expect.objectContaining({headers:undefined}));
    const state = {run_id:'r',revision:3} as import('./types').WorldState;
    await townApi.shortage!(state,'unique-id',signal);
    expect(fetch).toHaveBeenLastCalledWith(expect.stringContaining('/scenario/shortage'),expect.objectContaining({
      method:'POST',headers:{'Content-Type':'application/json','X-Operator-Token':'operator-test-key'},
      body:JSON.stringify({run_id:'r',expected_revision:3,request_id:'unique-id'}),
    }));
    setOperatorKey('');
  });
});
