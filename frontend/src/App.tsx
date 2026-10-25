import { useState } from 'react';
import { Controls } from './components/Controls';
import { TownMap } from './components/TownMap';
import { ResidentInspector } from './components/ResidentInspector';
import { EventLog } from './components/EventLog';
import { useTown } from './hooks/useTown';
import './styles.css';

export default function App() {
  const town = useTown();
  const [seed, setSeed] = useState(11);
  const [selectedId, setSelectedId] = useState('ethan');
  const state = town.state;
  const selected = state?.agents.find((agent) => agent.id === selectedId);
  return <main>
    <header className="masthead">
      <a className="wordmark" href="/">✳ MiniDavis</a>
      <span className="edition">A little town in motion</span>
      <span className="mode"><span className="status-dot" /> Baseline</span>
    </header>
    <section className="intro">
      <div><p className="eyebrow">FIVE RESIDENTS. ONE SHARED WORLD.</p>
        <h1>Small town.<br /><em>New possibilities.</em></h1>
        <p className="lede">Meet the neighbors. Set the town in motion.<br />Watch each little decision become the next step.</p>
      </div>
      <div className="turn"><span>Town turn</span><strong data-testid="tick">{state?.tick ?? '—'}</strong>
        <span>{town.running ? 'Town is moving' : town.busy ? 'Connecting…' : state ? 'Ready when you are' : 'Waiting for the town'}</span>
      </div>
    </section>
    {town.error && <div className="error" role="alert">{town.error} <button onClick={town.reconnect}>Reconnect</button></div>}
    <div className="workspace">
      <section className="map-panel" aria-label="Town">
        <div className="panel-heading"><h2>The neighborhood</h2><span>12 × 12</span></div>
        {state ? <TownMap state={state} selectedId={selectedId} onSelect={setSelectedId} /> : <div className="map-loading">{town.error ? 'Your town is offline.' : 'Opening the town…'}</div>}
        <div className="map-legend"><span>♠ Forest</span><span>✿ Farm</span><span>▤ Market</span><span>⚑ Town hall</span><span>⌂ Homes</span></div>
        <Controls {...town} ready={!!state && !town.error} seed={seed} setSeed={setSeed} />
        <p className="control-note">Pause finishes the current turn. Reset starts a new town.</p>
      </section>
      <aside className="neighbors" aria-label="Town residents">
        <div className="panel-heading"><h2>Meet the residents</h2><span>05</span></div>
        {state?.agents.map((agent) => <article className="neighbor" key={agent.id}>
          <div className={`avatar resident-${agent.id}`}>{agent.name[0]}</div>
          <div className="neighbor-content"><h3><button className="resident-select" aria-label={`Select ${agent.name}`}
            aria-pressed={selectedId === agent.id} onClick={() => setSelectedId(agent.id)}>{agent.name}</button></h3><p>{agent.goal}</p>
            <div className="inventory"><span title="Food">Food {agent.food}</span><span title="Wood">Wood {agent.wood}</span><span>Energy {agent.energy}</span></div>
          </div>
        </article>)}
        <div className="resources"><h3>Town supplies</h3>{state?.resources.map((resource) =>
          <div key={resource.id}><span>{resource.kind === 'food' ? 'Farm food' : 'Forest wood'}</span><strong>{resource.stock}</strong></div>)}</div>
        <p className="baseline-note">Select a resident to inspect its decision and retrieved history. Baseline rules are active; live AI is pending.</p>
      </aside>
      {selected && <ResidentInspector agent={selected} decision={state?.decisions?.[selected.id]} />}
      <EventLog events={state?.events ?? []} />
    </div>
    <footer><span>MiniDavis · Built together, one turn at a time.</span><span>{state ? `Seed ${state.seed} · ${state.agents.length} residents` : 'Connect the backend to begin'}</span></footer>
  </main>;
}
