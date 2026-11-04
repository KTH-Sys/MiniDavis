import { useState } from 'react';
import type { AgentRuntime, DecisionRecord, Resident, TownEvent, TradeOffer } from '../types';

const socialActions = new Set(['talk', 'offer_trade', 'accept_trade', 'reject_trade', 'trade', 'gift', 'trade_completed']);
const retrievalNames = { semantic: 'MiniLM meaning search', lexical: 'Keyword search', 'recent-only': 'Recent history only' };
export function interactionsFor(events: TownEvent[], agentId: string): TownEvent[] {
  // The engine writes the actor's event before the listener's memory copy.
  // Keep the original so its heading names the speaker, not the listener.
  const unique = new Map<string, TownEvent>();
  for (const event of events) {
    if (!socialActions.has(event.action) || !(event.agent_id === agentId
      || event.target_agent_id === agentId || event.participants?.includes(agentId))) continue;
    const id = event.interaction_id ?? event.event_id;
    if (!unique.has(id)) unique.set(id, event);
  }
  return [...unique.values()].reverse().slice(0, 20);
}

function MemoryCard({ event, name, relevant = false }: { event: TownEvent; name: string; relevant?: boolean }) {
  const label = event.interaction_label ?? event.classification?.label ?? event.label;
  const confidence = event.confidence ?? event.classification?.confidence;
  return <article className="terminal-entry memory-entry" data-source-id={event.event_id}>
    <div className="entry-heading"><span className="entry-glyph" aria-hidden="true">▧</span><strong>[ {name} ]</strong><span>{relevant ? 'RELEVANT MEMORY' : 'MEMORY'}</span><time>T{String(event.tick).padStart(2, '0')}</time></div>
    <p><span className="entry-branch" aria-hidden="true">└↳</span>{event.text}</p>
    {label && <p className="interaction-label" data-testid="memory-interaction-label">
      <span className="entry-branch" aria-hidden="true">└↳</span>
      <span className="label-prefix">Interaction label:</span>{' '}
      <strong className={`label-badge label-${label.toLowerCase()}`}>{label}</strong>
      {confidence != null && <span className="label-confidence"> ({typeof confidence === 'number' && confidence <= 1 ? `${(confidence * 100).toFixed(1)}%` : confidence} confidence)</span>}
    </p>}
    <details><summary>Source event</summary><code>{event.event_id}</code><span className="source-outcome">{event.outcome}</span></details>
  </article>;
}

function EventEntry({ event, name }: { event: TownEvent; name: string }) {
  const isSocial = socialActions.has(event.action);
  const label = event.interaction_label ?? event.classification?.label ?? event.label;
  const confidence = event.confidence ?? event.classification?.confidence;
  return <article className={`terminal-entry ${event.outcome === 'rejected' ? 'rejected-entry' : ''}`} data-event-id={event.event_id}>
    <div className="entry-heading"><span className="entry-glyph" aria-hidden="true">▪</span><strong>[ {name} ]</strong>
      <span>{isSocial ? 'INTERACTION' : 'ACTION'} / {event.action.replaceAll('_', ' ')}</span><time>T{String(event.tick).padStart(2, '0')}</time></div>
    <p><span className="entry-branch" aria-hidden="true">└↳</span>{event.text}</p>
    {(label || isSocial) && <p className={`interaction-label ${!label ? 'unclassified' : ''}`} data-testid="interaction-label">
      <span className="entry-branch" aria-hidden="true">└↳</span>
      <span className="label-prefix">Interaction label:</span>{' '}
      {label ? <>
        <strong className={`label-badge label-${label.toLowerCase()}`}>{label}</strong>
        {confidence != null && <span className="label-confidence"> ({typeof confidence === 'number' && confidence <= 1 ? `${(confidence * 100).toFixed(1)}%` : confidence} confidence)</span>}
      </> : <em className="label-none">unclassified</em>}
    </p>}
    {event.outcome === 'rejected' && <small>Rejected by the world rules</small>}
  </article>;
}

export function AgentJournal({ agent, decision, events, agents = [agent], runtime, tradeOffers = [] }: {
  agent: Resident; decision?: DecisionRecord; events: TownEvent[]; agents?: Resident[]; runtime?: AgentRuntime; tradeOffers?: TradeOffer[];
}) {
  const [tab, setTab] = useState<'feed' | 'decision' | 'memory' | 'interactions'>('feed');
  const interactions = interactionsFor(events, agent.id);
  const residentTrades = tradeOffers.filter((t) => t.proposer_id === agent.id || t.recipient_id === agent.id);
  const recent = decision?.memory.recent ?? [];
  const relevant = decision?.memory.relevant ?? [];
  const nameFor = (id: string) => agents.find((resident) => resident.id === id)?.name ?? id;
  const seenActions = new Set<string>();
  const actionEvents = events.filter((event) => {
    const id = event.interaction_id ?? event.event_id;
    if (seenActions.has(id)) return false;
    seenActions.add(id); return true;
  });
  const feed = [...actionEvents.slice(-15).map((event) => ({ event, memory: false })),
    ...recent.slice(-1).map((event) => ({ event, memory: true }))]
    .sort((a, b) => b.event.tick - a.event.tick);
  const tabs = ['feed', 'decision', 'memory', 'interactions'] as const;
  return <section className="agent-journal" aria-label="Resident inspector">
    <div className="journal-person"><div><span className="eyebrow">INSPECTING</span><h2>{agent.name}</h2></div>
      <span className="journal-turn">{decision ? `TURN ${String(decision.tick).padStart(2, '0')}` : 'WAITING FOR FIRST TURN'}<span className="terminal-cursor" aria-hidden="true">▋</span></span>
    </div>
    <p className={`planner-status mode-${runtime?.status ?? 'baseline'}`} role="status">{(runtime?.status ?? 'baseline').toUpperCase()}{runtime?.pending ? ' · request in progress' : ''} · {runtime?.detail ?? 'Baseline rules'}</p>
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
          {decision && <small>Executed with: {decision.planner_mode}</small>}
          {decision?.model_explanation && <p className="model-explanation">Model’s explanation: {decision.model_explanation}</p>}
          {decision?.model_observation_revision != null && <small>Model observed revision {decision.model_observation_revision}</small>}
        </article>
        <div className="resident-summary"><h3>GOAL</h3><p>{agent.goal}</p><dl><div><dt>Food</dt><dd>{agent.food}</dd></div><div><dt>Wood</dt><dd>{agent.wood}</dd></div><div><dt>Coins</dt><dd>{agent.coins}</dd></div><div><dt>Energy</dt><dd>{agent.energy}/100</dd></div></dl></div>
        <div className="resident-summary"><h3>RELATIONSHIPS</h3><p>{Object.entries(agent.relationships ?? {}).filter(([,score]) => score !== 0).map(([id,score]) => `${nameFor(id)}: ${score > 0 ? '+' : ''}${score}`).join(' · ') || 'No relationship changes yet.'}</p><small>Updated by completed exchanges, independently of the classifier.</small></div>
        <div className="section-label"><h3>LATEST MEMORY</h3><button className="text-button" onClick={() => setTab('memory')}>View all →</button></div>
        {recent.length ? <MemoryCard event={recent[recent.length - 1]} name={agent.name} /> : <p className="journal-empty">No memories in this run yet.</p>}
      </>}
      {tab === 'memory' && <>
        <p className="feed-note">History supplied before {agent.name}’s latest decision. {decision ? `Retrieved with ${retrievalNames[decision.memory.mode].toLowerCase()}.` : 'No retrieval yet.'}</p>
        {decision && <p className="feed-note">Sources through turn {decision.memory.as_of_tick}. Query: {decision.memory.query}</p>}
        <h3 className="section-label">RELEVANT MEMORIES</h3>{relevant.length ? relevant.map((event) => <MemoryCard key={event.event_id} event={event} name={agent.name} relevant />) : <p className="journal-empty">No matching memories yet.</p>}
        <h3 className="section-label">RECENT MEMORIES</h3>{recent.length ? recent.slice().reverse().map((event) => <MemoryCard key={event.event_id} event={event} name={agent.name} />) : <p className="journal-empty">No memories in this run yet.</p>}
      </>}
      {tab === 'interactions' && <>
        <p className="feed-note">Conversations & trades involving {agent.name} · {interactions.length} recorded</p>
        {residentTrades.length > 0 && <div className="trade-offers-block" aria-label="Trade offers">
          <h3 className="section-label">TRADE OFFERS & TRANSFERS</h3>
          <ul className="trade-offers-list">
            {residentTrades.map((trade) => <li key={trade.offer_id} className={`trade-item status-${trade.status}`}>
              <div className="entry-heading">
                <span className="entry-glyph" aria-hidden="true">⇄</span>
                <strong>[ {nameFor(trade.proposer_id)} → {nameFor(trade.recipient_id)} ]</strong>
                <span className={`trade-status-pill status-${trade.status}`}>{trade.status.toUpperCase()}</span>
              </div>
              <p className="trade-terms">Offers {trade.give_amount} {trade.give_resource} for {trade.receive_amount} {trade.receive_resource}</p>
              <code>{trade.offer_id}</code>
            </li>)}
          </ul>
        </div>}
        {interactions.length ? interactions.map((event) => <EventEntry key={event.event_id} event={event} name={nameFor(event.agent_id)} />)
          : !residentTrades.length ? <div className="terminal-empty"><span aria-hidden="true">&gt;_</span><h3>No interactions yet</h3><p>{runtime?.status === 'baseline'
            ? 'Baseline residents only move, gather, eat and rest. Start a live AI town for possible conversations, or load the labelled sample run to inspect a trade.'
            : 'Residents must be nearby and choose to interact. Conversations are not guaranteed each turn. Load the labelled sample run to inspect a trade.'}</p></div> : null}
      </>}
    </div>
    <p className="journal-footnote"><span aria-hidden="true">●</span> {runtime?.status === 'replay' ? 'Recorded replay · No AI calls' : runtime?.status === 'live' ? 'Groq plan' : runtime?.status === 'waiting' ? 'Queued for Groq' : runtime?.status === 'fallback' ? 'Baseline fallback' : 'Baseline rules'} · {decision ? retrievalNames[decision.memory.mode] : 'No memory used yet'}</p>
  </section>;
}
