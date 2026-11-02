import type { AgentRuntime, DecisionRecord, Resident, TownEvent } from '../types';

function Sources({ title, events }: { title: string; events: TownEvent[] }) {
  return <section className="memory-sources" aria-label={title}>
    <h3>{title}</h3>
    {events.length === 0 ? <p>No matching past events yet.</p> : <ul>{events.map((event) => {
      const label = event.interaction_label ?? event.classification?.label ?? event.label;
      const confidence = event.confidence ?? event.classification?.confidence;
      return <li key={event.event_id} data-source-id={event.event_id}>
        <span className={`outcome ${event.outcome}`}>Turn {event.tick} · {event.outcome}</span>
        <p>{event.text}</p>
        {label && <p className="interaction-label" data-testid="interaction-label">
          <span className="label-prefix">Interaction label:</span>{' '}
          <strong className={`label-badge label-${label.toLowerCase()}`}>{label}</strong>
          {confidence != null && <span className="label-confidence"> ({typeof confidence === 'number' && confidence <= 1 ? `${(confidence * 100).toFixed(1)}%` : confidence} confidence)</span>}
        </p>}
        <code>{event.event_id}</code>
      </li>;
    })}</ul>}
  </section>;
}

export function ResidentInspector({ agent, decision, runtime }: {
  agent: Resident;
  decision?: DecisionRecord;
  runtime?: AgentRuntime;
}) {
  return <section className="inspector" aria-label="Resident inspector">
    <div className="panel-heading"><h2>{agent.name}’s inspector</h2>
      <span>{decision ? `DECISION AT TURN ${decision.tick}` : 'NO DECISION YET'}</span></div>
    <p className={`planner-status mode-${runtime?.status ?? 'baseline'}`} role="status">
      {(runtime?.status ?? 'baseline').toUpperCase()}{runtime?.pending ? ' · request in progress' : ''} · {runtime?.detail ?? 'Baseline rules'}
    </p>
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
          {decision.model_explanation && <p className="model-explanation">Model’s explanation: {decision.model_explanation}</p>}
          {decision.model_observation_revision != null && <small>Model observed revision {decision.model_observation_revision}</small>}
        </>}
      </section>
      <Sources title="Recent memories" events={decision?.memory.recent ?? []} />
      <Sources title="Relevant memories" events={decision?.memory.relevant ?? []} />
    </div>
  </section>;
}
