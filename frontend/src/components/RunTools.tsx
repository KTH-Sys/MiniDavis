import { useEffect, useState } from 'react';
import { setOperatorKey, townApi } from '../api';
import type { Readiness, RunTrace } from '../types';
import { ClassifierProbe } from './ClassifierProbe';

function readTrace(value: unknown): RunTrace {
  if (!value || typeof value !== 'object' || !('version' in value) || value.version !== 1
      || !('operations' in value) || !Array.isArray(value.operations)) {
    throw new Error('Choose a MiniDavis run saved with Save run.');
  }
  return value as RunTrace; // The backend validates every action and checksum.
}

export function RunTools({ disabled, replaying, shortage, replay, reconnect, mode, readiness, startMode }: {
  disabled: boolean; replaying: boolean; shortage: () => void;
  replay: (trace: RunTrace) => void; reconnect: () => void;
  mode?: 'baseline' | 'llm' | 'replay'; readiness?: Readiness | null;
  startMode?: (mode: 'baseline' | 'llm') => void;
}) {
  const [message, setMessage] = useState('');
  const [key, setKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [chosenMode, setChosenMode] = useState<'baseline' | 'llm'>('baseline');
  useEffect(() => { if (mode && mode !== 'replay') setChosenMode(mode); }, [mode]);
  async function sampleRun() {
    setLoading(true);
    try {
      const response = await fetch('/demo/sample-run.json');
      if (!response.ok) throw new Error('Sample run is unavailable. Use Replay saved run instead.');
      replay(readTrace(await response.json())); setMessage('Sample loaded: scripted actions, no AI calls.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not load sample.'); }
    finally { setLoading(false); }
  }
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
    {mode && <div className="setup-status" aria-label="Town setup">
      <p><strong>{mode === 'llm' ? 'LIVE AI' : mode === 'replay' ? 'RECORDED REPLAY' : 'BASELINE RULES'}</strong>{' · '}
        {mode === 'llm' ? 'AI chooses; world rules check every action.' : mode === 'replay'
          ? 'Saved actions, no new AI decisions.' : 'Fixed rules: move, gather, eat and rest.'}</p>
      {readiness && <p>AI service: {readiness.groq_configured ? 'key configured' : 'key missing'} · Memory: {readiness.memory_requested === 'semantic' ? 'meaning search requested' : 'keyword search'} · Classifier: {readiness.classifier === 'loaded' ? 'loaded' : 'not loaded'}</p>}
      {startMode && <div className="mode-controls">
        <label>Town mode <select value={chosenMode} onChange={(e) => setChosenMode(e.target.value as 'baseline' | 'llm')}>
          <option value="baseline">Baseline rules</option><option value="llm">Live AI (Groq)</option>
        </select></label>
        <button disabled={disabled || (chosenMode === 'llm' && readiness?.groq_configured === false)}
          onClick={() => { setMessage(''); startMode(chosenMode); }}>Start new town</button>
      </div>}
      <p className="control-note">Starting a new town clears this run. Save it first. Live AI needs a server API key and advances about every 15 seconds.</p>
      {readiness?.groq_configured === false && <p className="control-note">To use live AI, add LLM_API_KEY to backend/.env and restart the backend. Keep that key out of this page.</p>}
    </div>}
    <div className="controls">
      <button disabled={disabled || replaying} onClick={shortage}>Food shortage</button>
      <button disabled={disabled || saving} onClick={() => void saveRun()}>Save run</button>
      <button disabled={disabled || loading} onClick={() => void sampleRun()}>Load sample run</button>
      <label>Replay saved run <input aria-label="Replay saved run" type="file" accept="application/json,.json"
        disabled={disabled} onChange={async (event) => {
          const input = event.currentTarget;
          const file = input.files?.[0]; if (!file) return;
          try {
            if (file.size > 5_000_000) throw new Error('Choose a run file smaller than 5 MB.');
            replay(readTrace(JSON.parse(await file.text()))); setMessage('');
          } catch (error) { setMessage(error instanceof Error ? error.message : 'Could not open run.'); }
          input.value = '';
        }} /></label>
    </div>
    <p className="control-note">Sample run: a scripted trade, conversation and shortage. It demonstrates the town mechanics, not autonomous AI performance. Loading it replaces this run.</p>
    {replaying && <p className="control-note">Replaying saved actions. Start a new town to resume simulation.</p>}
    {readiness?.operator_protected !== false ? <details><summary>Shared preview access</summary>
      <p className="control-note">Only for a protected shared town: enter its operator password, not your Groq API key.</p>
      <form onSubmit={(event) => { event.preventDefault(); setOperatorKey(key); setKey('');
        setMessage('Operator password set for this tab.'); reconnect(); }}>
        <input aria-label="Operator key" type="password" autoComplete="off" value={key} onChange={(e) => setKey(e.target.value)} />
        <button type="submit">Apply key</button>
      </form>
    </details> : <p className="control-note">Local controls are open. No operator password is needed.</p>}
    {readiness?.classifier === 'loaded' && <ClassifierProbe />}
    {message && <p role="status">{message}</p>}
  </div>;
}
