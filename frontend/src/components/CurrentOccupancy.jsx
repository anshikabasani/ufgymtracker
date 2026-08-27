function timeAgo(isoString) {
  const seconds = Math.round((Date.now() - new Date(isoString)) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  return `${Math.round(seconds / 60)}m ago`;
}

export function CurrentOccupancy({ reading, error }) {
  if (error) return <p className="error">Can't reach the tracker: {error}</p>;
  if (!reading) return <p className="muted">Loading…</p>;

  return (
    <section>
      <p className="count">
        {reading.people}
        <span>people</span>
      </p>
      <p className="level">{reading.level}</p>
      <p className="muted">Updated {timeAgo(reading.recorded)}</p>
    </section>
  );
}
