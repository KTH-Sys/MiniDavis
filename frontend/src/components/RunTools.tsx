import { useState } from 'react';
import { setOperatorKey, townApi } from '../api';
import type { RunTrace } from '../types';

export function RunTools({ disabled, replaying, shortage, replay, reconnect }: {
  disabled: boolean; replaying: boolean; shortage: () => void;
  replay: (trace: RunTrace) => void; reconnect: () => void;
}) {
  const [message, setMessage] = useState('');
  const [key, setKey] = useState('');
  const [saving, setSaving] = useState(false);
  async function saveRun() {
    setSaving(true);
    try {
      if (!townApi.trace) throw new Error('Run export is unavailable.');
      const trace = await townApi.trace(new AbortController().signal);
      const url = URL.createObjectURL(new Blob([JSON.stringify(trace, null, 2)], { type: 'application/json' }));
      const link = document.createElement('a'); link.href = url; link.download = 'minidavis-run.json'; link.click();
      URL.revokeObjectURL(url); setMessage('Run saved.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not save run.'); }
    finally { setSaving(false); }
  }
  return <div className="run-tools">
    <div className="controls">
      <button disabled={disabled || replaying} onClick={shortage}>Food shortage</button>
      <button disabled={disabled || saving} onClick={() => void saveRun()}>Save run</button>
      <label>Replay saved run <input aria-label="Replay saved run" type="file" accept="application/json,.json"
        disabled={disabled} onChange={async (event) => {
          const file = event.target.files?.[0]; if (!file) return;
          try {
            if (file.size > 5_000_000) throw new Error('Choose a run file smaller than 5 MB.');
            replay(JSON.parse(await file.text()) as RunTrace); setMessage('');
          } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not open run.'); }
          event.target.value = '';
        }} /></label>
    </div>
    {replaying && <p className="control-note">Replaying saved actions. Reset to start a new town.</p>}
    <details><summary>Operator access</summary>
      <p className="control-note">For a shared preview, use the operator key provided by Eric.</p>
      <form onSubmit={(event) => { event.preventDefault(); setOperatorKey(key); setKey('');
        setMessage('Key set for this tab.'); reconnect(); }}>
        <input aria-label="Operator key" type="password" autoComplete="off" value={key} onChange={(e) => setKey(e.target.value)} />
        <button type="submit">Apply key</button>
      </form>
    </details>
    {message && <p role="status">{message}</p>}
  </div>;
}
