import type { DecisionRecord, Resident, TownEvent } from '../types';

function Sources({ title, events }: { title: string; events: TownEvent[] }) {
  return <section className="memory-sources" aria-label={title}>
    <h3>{title}</h3>
    {events.length === 0 ? <p>No matching past events yet.</p> : <ul>{events.map((event) =>
      <li key={event.event_id} data-source-id={event.event_id}>
        <span className={`outcome ${event.outcome}`}>Turn {event.tick} · {event.outcome}</span>
        <p>{event.text}</p><code>{event.event_id}</code>
      </li>)}</ul>}
  </section>;
}

export function ResidentInspector({ agent, decision }: { agent: Resident; decision?: DecisionRecord }) {
  return <section className="inspector" aria-label="Resident inspector">
    <div className="panel-heading"><h2>{agent.name}’s inspector</h2>
      <span>{decision ? `DECISION AT TURN ${decision.tick}` : 'NO DECISION YET'}</span></div>
    <div className="inspector-grid">
      <section className="decision-summary">
        <h3>Goal & current state</h3><p>{agent.goal}</p>
        <p>Position ({agent.x}, {agent.y}) · Energy {agent.energy}</p>
        <p>Food {agent.food} · Wood {agent.wood} · Coins {agent.coins}</p>
        <h3>Latest decision</h3><p>{decision?.explanation ?? 'Advance a turn to see the first decision.'}</p>
        {decision && <>
          <p><strong>Mode:</strong> {{ baseline: 'Baseline rules', custom: 'Custom planner', live: 'Live Groq plan', cached: 'Cached Groq plan', waiting: 'Waiting for Groq', fallback: 'Baseline fallback' }[decision.planner_mode]}</p>
          <p><strong>Memory retrieval:</strong> {{ semantic: 'MiniLM meaning search', lexical: 'Keyword search', 'recent-only': 'Recent history only' }[decision.memory.mode]}</p>
          <p>Memory includes events through turn {decision.memory.as_of_tick}, before this decision.</p>
          <details><summary>Retrieval query</summary><p>{decision.memory.query}</p></details>
          {decision.planner_mode === 'baseline' && <p className="baseline-note">Memory reaches the planner, but baseline actions still follow fixed rules.</p>}
        </>}
      </section>
      <Sources title="Recent memories" events={decision?.memory.recent ?? []} />
      <Sources title="Relevant memories" events={decision?.memory.relevant ?? []} />
    </div>
  </section>;
}
