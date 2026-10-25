import type { TownEvent } from '../types';

export function EventLog({ events }: { events: TownEvent[] }) {
  const recent = events.slice(-20).reverse();
  return <section className="event-log" aria-label="Town activity">
    <div className="panel-heading"><h2>Town activity</h2><span>LATEST {recent.length} EVENTS</span></div>
    {recent.length === 0 ? <p className="empty-log">The town is ready. Advance a turn to start its story.</p> :
      <ol>{recent.map((event) => <li key={event.event_id}>
        <span className={`outcome ${event.outcome}`}>Turn {event.tick} · {event.outcome}</span>
        <span>{event.text}</span>
      </li>)}</ol>}
  </section>;
}
