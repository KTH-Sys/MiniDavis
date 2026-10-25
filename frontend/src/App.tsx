import { useState } from 'react';
import { Controls } from './components/Controls';
import { TownMap } from './components/TownMap';
import { AgentJournal } from './components/AgentJournal';
import { useTown } from './hooks/useTown';
import './styles.css';

export default function App() {
  const town = useTown();
  const [seed, setSeed] = useState(11);
  const [selectedId, setSelectedId] = useState('ethan');
  const [showGrid, setShowGrid] = useState(false);
  const state = town.state;
  const selected = state?.agents.find((agent) => agent.id === selectedId);
  return <main>
    <header className="masthead"><a className="wordmark" href="/"><span aria-hidden="true">✳</span> MiniDavis</a>
      <span className="edition">Five residents. One little world.</span>
      <div className="town-status"><span className={`status-dot ${town.running ? 'active' : ''}`} />
        <span>{town.running ? 'RUNNING' : 'PAUSED'}</span><span className="status-divider">/</span>
        <span>TURN <strong data-testid="tick">{state?.tick ?? '—'}</strong></span>
      </div>
    </header>
    {town.error && <div className="error" role="alert">{town.error} <button onClick={town.reconnect}>Reconnect</button></div>}
    <div className="workspace">
      <section className="map-panel" aria-label="Town">
        <div className="map-heading"><span>01 / THE TOWN</span>
          <label className="grid-toggle"><input type="checkbox" checked={showGrid} onChange={(event) => setShowGrid(event.target.checked)} /> Show grid</label></div>
        <div className="scene-frame">{state ? <TownMap state={state} selectedId={selectedId} onSelect={setSelectedId} running={town.running} showGrid={showGrid} />
          : <div className="map-loading">{town.error ? 'Your town is offline.' : 'Opening the gates…'}</div>}</div>
        <div className="scene-caption"><span>Click a resident to inspect their story.</span><div className="supply-chips">{state?.resources.map((resource) => <span key={resource.id}>{resource.kind === 'food' ? 'Farm' : 'Forest'} <strong>{resource.stock}</strong></span>)}</div></div>
        <Controls {...town} ready={!!state && !town.error} seed={seed} setSeed={setSeed} />
        <p className="control-note">Pause finishes the current turn. Reset starts a new town.</p>
      </section>
      <aside className="story-panel" aria-label="Town residents">
        <div className="console-heading"><span>02 / AGENT FEED</span><span className="console-signal">● <span>{town.error ? 'TOWN OFFLINE' : state ? 'CONNECTED TO TOWN' : 'CONNECTING'}</span></span></div>
        <div className="resident-picker" aria-label="Choose a resident">{state?.agents.map((agent) => <button key={agent.id}
          className="resident-choice" aria-label={`Select ${agent.name}`} aria-pressed={selectedId === agent.id} onClick={() => setSelectedId(agent.id)}>
          <span aria-hidden="true">[</span>{agent.name}<span aria-hidden="true">]</span>
        </button>)}</div>
        {selected && <AgentJournal agent={selected} decision={state?.decisions?.[selected.id]} events={state?.events ?? []} agents={state?.agents} />}
      </aside>
    </div>
    <footer><span>MINIDAVIS / A SHARED WORLD IN MOTION</span><span>Baseline rules · Five autonomous residents</span></footer>
  </main>;
}
