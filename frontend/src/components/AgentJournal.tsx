import { useState } from 'react';
import type { DecisionRecord, Resident, TownEvent } from '../types';

const socialActions = new Set(['talk', 'offer_trade', 'accept_trade', 'reject_trade', 'trade', 'gift']);
export function interactionsFor(events: TownEvent[], agentId: string): TownEvent[] {
  return events.filter((event) => socialActions.has(event.action)
    && (event.agent_id === agentId || event.target_agent_id === agentId || event.participants?.includes(agentId))).slice(-20).reverse();
}

function MemoryCard({ event, name, relevant = false }: { event: TownEvent; name: string; relevant?: boolean }) {
  return <article className="terminal-entry memory-entry" data-source-id={event.event_id}>
    <div className="entry-heading"><span className="entry-glyph" aria-hidden="true">▧</span><strong>[ {name} ]</strong><span>{relevant ? 'RELEVANT MEMORY' : 'MEMORY'}</span><time>T{String(event.tick).padStart(2, '0')}</time></div>
    <p><span className="entry-branch" aria-hidden="true">└↳</span>{event.text}</p>
    <details><summary>Source event</summary><code>{event.event_id}</code><span className="source-outcome">{event.outcome}</span></details>
  </article>;
}

function EventEntry({ event, name }: { event: TownEvent; name: string }) {
  return <article className={`terminal-entry ${event.outcome === 'rejected' ? 'rejected-entry' : ''}`}>
    <div className="entry-heading"><span className="entry-glyph" aria-hidden="true">▪</span><strong>[ {name} ]</strong>
      <span>{socialActions.has(event.action) ? 'INTERACTION' : 'ACTION'} / {event.action.replaceAll('_', ' ')}</span><time>T{String(event.tick).padStart(2, '0')}</time></div>
    <p><span className="entry-branch" aria-hidden="true">└↳</span>{event.text}</p>
    {event.outcome === 'rejected' && <small>Rejected by the world rules</small>}
  </article>;
}

export function AgentJournal({ agent, decision, events, agents = [agent] }: {
  agent: Resident; decision?: DecisionRecord; events: TownEvent[]; agents?: Resident[];
}) {
  const [tab, setTab] = useState<'feed' | 'decision' | 'memory' | 'interactions'>('feed');
  const interactions = interactionsFor(events, agent.id);
  const recent = decision?.memory.recent ?? [];
  const relevant = decision?.memory.relevant ?? [];
  const nameFor = (id: string) => agents.find((resident) => resident.id === id)?.name ?? id;
  const feed = [...events.slice(-15).map((event) => ({ event, memory: false })),
    ...recent.slice(-1).map((event) => ({ event, memory: true }))]
    .sort((a, b) => b.event.tick - a.event.tick);
  const tabs = ['feed', 'decision', 'memory', 'interactions'] as const;
  return <section className="agent-journal" aria-label="Resident inspector">
    <div className="journal-person"><div><span className="eyebrow">INSPECTING</span><h2>{agent.name}</h2></div>
      <span className="journal-turn">{decision ? `TURN ${String(decision.tick).padStart(2, '0')}` : 'WAITING FOR FIRST TURN'}<span className="terminal-cursor" aria-hidden="true">▋</span></span>
    </div>
    <div className="journal-tabs" role="tablist" aria-label="Resident information">
      {tabs.map((name, index) => <button key={name} role="tab" tabIndex={tab === name ? 0 : -1}
        id={`tab-${name}`} aria-selected={tab === name} aria-controls={`panel-${name}`} onClick={() => setTab(name)}
        onKeyDown={(event) => {
          const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : undefined;
          if (next === undefined) return;
          event.preventDefault(); setTab(tabs[next]);
          event.currentTarget.parentElement?.querySelector<HTMLButtonElement>(`#tab-${tabs[next]}`)?.focus();
        }}>
        {name === 'feed' ? 'All activity' : name === 'decision' ? 'Decision' : name === 'memory' ? 'Memories' : 'Interactions'}
      </button>)}
    </div>
    <div className="journal-content" id={`panel-${tab}`} role="tabpanel" tabIndex={0} aria-labelledby={`tab-${tab}`}>
      {tab === 'feed' && <>
        <p className="feed-note">Town-wide actions + {agent.name}’s latest memory</p>
        {feed.length ? feed.map(({ event, memory }) => memory
          ? <MemoryCard key={`memory:${event.event_id}`} event={event} name={agent.name} />
          : <EventEntry key={event.event_id} event={event} name={nameFor(event.agent_id)} />)
          : <div className="terminal-empty"><span aria-hidden="true">&gt;_</span><h3>The town is ready.</h3><p>Press Play or Next Turn to follow the residents. Their actions, memories and interactions will appear here.</p></div>}
      </>}
      {tab === 'decision' && <>
        <article className="terminal-entry decision-entry"><div className="entry-heading"><span className="entry-glyph" aria-hidden="true">◆</span><strong>[ {agent.name} ]</strong><span>DECISION</span></div>
          <p className="decision-text"><span className="entry-branch" aria-hidden="true">└↳</span>{decision?.explanation ?? 'My day is just beginning. Advance a turn to see my first action.'}</p>
        </article>
        <div className="resident-summary"><h3>GOAL</h3><p>{agent.goal}</p><dl><div><dt>Food</dt><dd>{agent.food}</dd></div><div><dt>Wood</dt><dd>{agent.wood}</dd></div><div><dt>Coins</dt><dd>{agent.coins}</dd></div><div><dt>Energy</dt><dd>{agent.energy}/100</dd></div></dl></div>
        <div className="section-label"><h3>LATEST MEMORY</h3><button className="text-button" onClick={() => setTab('memory')}>View all →</button></div>
        {recent.length ? <MemoryCard event={recent[recent.length - 1]} name={agent.name} /> : <p className="journal-empty">No memories in this run yet.</p>}
      </>}
      {tab === 'memory' && <>
        <p className="feed-note">History supplied before {agent.name}’s latest decision. {decision?.memory.mode === 'lexical' ? 'Retrieved with keyword search.' : 'Recent history only.'}</p>
        <h3 className="section-label">RELEVANT MEMORIES</h3>{relevant.length ? relevant.map((event) => <MemoryCard key={event.event_id} event={event} name={agent.name} relevant />) : <p className="journal-empty">No matching memories yet.</p>}
        <h3 className="section-label">RECENT MEMORIES</h3>{recent.length ? recent.slice().reverse().map((event) => <MemoryCard key={event.event_id} event={event} name={agent.name} />) : <p className="journal-empty">No memories in this run yet.</p>}
      </>}
      {tab === 'interactions' && <>
        <p className="feed-note">Conversations & trades involving {agent.name} · {interactions.length} recorded</p>
        {interactions.length ? interactions.map((event) => <EventEntry key={event.event_id} event={event} name={nameFor(event.agent_id)} />)
          : <div className="terminal-empty"><span aria-hidden="true">&gt;_</span><h3>No interactions yet</h3><p>Conversations and trades between residents will appear here when the simulation records them.</p></div>}
      </>}
    </div>
    <p className="journal-footnote"><span aria-hidden="true">●</span> Baseline rules · Keyword memory</p>
  </section>;
}
