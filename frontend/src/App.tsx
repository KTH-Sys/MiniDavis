import { useState } from 'react';
import { Controls } from './components/Controls';
import { RunTools } from './components/RunTools';
import { TownMap } from './components/TownMap';
import { AgentJournal } from './components/AgentJournal';
import { loadSampleTrace } from './api';
import { useTown } from './hooks/useTown';
import './styles.css';

export default function App() {
  const town = useTown();
  const [seed, setSeed] = useState(11);
  const [selectedId, setSelectedId] = useState('ethan');
  const [showGrid, setShowGrid] = useState(false);
  const [showTools,setShowTools] = useState(false);
  const [loadingExample,setLoadingExample] = useState(false);
  const [exampleError,setExampleError] = useState('');
  const state = town.state;
  const selected = state?.agents.find((agent) => agent.id === selectedId);
  const modeName = state?.mode === 'replay' ? 'Recorded example' : state?.mode === 'llm' ? 'Live town' : 'Practice run';
  const disabled = !state || town.busy || town.running || !!town.error;
  async function showExample() {
    setLoadingExample(true);setExampleError('');
    try { town.replay(await loadSampleTrace()); }
    catch (error) {setExampleError(error instanceof Error ? error.message : 'Could not load the example.');}
    finally {setLoadingExample(false);}
  }
  return <main className={showTools ? 'tools-visible' : 'demo-mode'}>
    <header className="masthead"><a className="wordmark" href="/"><span aria-hidden="true">✳</span> MiniDavis</a>
      <span className="edition">A tiny town for AI agents.</span>
      <div className="town-status"><span className={`status-dot ${town.running ? 'active' : ''}`} />
        <span>{town.running ? 'RUNNING' : 'PAUSED'}</span><span className="status-divider">/</span>
        <span>TURN <strong data-testid="tick">{state?.tick ?? '—'}</strong></span>
      </div>
    </header>
    {town.error && <div className="error" role="alert">{town.error} <button onClick={town.reconnect}>Reconnect</button></div>}
    <div className="workspace">
      <section className="map-panel" aria-label="Town">
        <div className="map-heading"><span>01 / THE TOWN</span><span className="demo-mode-label">{modeName}</span></div>
        <div className="scene-frame">{state ? <TownMap state={state} selectedId={selectedId} onSelect={setSelectedId} running={town.running} showGrid={showGrid && showTools} />
          : <div className="map-loading">{town.error ? 'Your town is offline.' : 'Opening the gates…'}</div>}</div>
        <div className="scene-caption"><span>Choose a resident to follow their story.</span><div className="supply-chips">{state?.resources.map((resource) => <span key={resource.id} className={resource.stock <= 5 ? 'shortage' : ''}>{resource.kind === 'food' ? 'Farm' : 'Forest'} <strong>{resource.stock}</strong>{resource.stock <= 5 && <span className="shortage-badge"> LOW</span>}</span>)}</div></div>
        <Controls {...town} ready={!!state && state.mode !== 'replay' && !town.error} seed={seed} setSeed={setSeed} compact={!showTools}
          planning={state?.mode === 'llm' && Object.values(state.agent_runtime ?? {}).some((agent) => agent.pending)} />
        {!showTools && <div className="demo-actions"><button disabled={disabled || loadingExample} onClick={()=>void showExample()}>Recorded example</button>
          <button className="text-button" aria-expanded={false} onClick={()=>setShowTools(true)}>Presenter tools</button></div>}
        {exampleError && <p role="alert" className="control-note">{exampleError}</p>}
        <p className="control-note">{state?.mode === 'replay' ? 'A scripted trade and conversation. Reset to return to a fresh town.' : 'Pause finishes the current turn. AI replies can take a moment.'}</p>
        {showTools && <section className="presenter-tools" aria-label="Presenter tools">
          <div className="presenter-tools-heading"><h2>Presenter tools</h2><button className="text-button" aria-expanded={true} onClick={()=>setShowTools(false)}>Close tools</button></div>
          <label className="grid-toggle"><input type="checkbox" checked={showGrid} onChange={(event) => setShowGrid(event.target.checked)} /> Show grid</label>
          <RunTools disabled={disabled} replaying={state?.mode === 'replay'} shortage={town.shortage} replay={town.replay} reconnect={town.reconnect}
            mode={state?.mode} readiness={town.readiness} startMode={(mode) => town.reset(seed, mode)} />
        </section>}
      </section>
      <aside className="story-panel" aria-label="Town residents">
        <div className="console-heading"><span>02 / RESIDENT STORIES</span><span className="console-signal">● <span>{town.error ? 'TOWN OFFLINE' : state ? modeName.toUpperCase() : 'CONNECTING'}</span></span></div>
        <div className="resident-picker" aria-label="Choose a resident">{state?.agents.map((agent) => <button key={agent.id}
          className="resident-choice" aria-label={`Select ${agent.name}`} aria-pressed={selectedId === agent.id} onClick={() => setSelectedId(agent.id)}>
          <span aria-hidden="true">[</span>{agent.name}<span aria-hidden="true">]</span>
          {showTools && <small className={`resident-mode mode-${state?.agent_runtime?.[agent.id]?.status ?? 'baseline'}`}>{state?.agent_runtime?.[agent.id]?.status ?? 'baseline'}</small>}
        </button>)}</div>
        {selected && <AgentJournal agent={selected} decision={state?.decisions?.[selected.id]} events={state?.events ?? []} agents={state?.agents}
          runtime={state?.agent_runtime?.[selected.id]} tradeOffers={state?.trade_offers} presentation={!showTools} />}
        {showTools && state?.mode === 'llm' && <p className="provider-budget">Groq calls: {state.provider_usage?.calls_run ?? 0} this run · {state.provider_usage?.calls_day ?? 0} today</p>}
      </aside>
    </div>
    <footer><span>MINIDAVIS / FIVE RESIDENTS. ONE LITTLE WORLD.</span><span>{state ? modeName : 'Connecting to town'}</span></footer>
  </main>;
}
