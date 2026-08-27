import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function formatClock(isoString) {
  return new Date(isoString).toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}

export function HistoryChart({ readings }) {
  if (!readings?.length) return <p className="muted">No history yet.</p>;

  const data = readings.map((reading) => ({
    time: formatClock(reading.recorded),
    people: reading.people,
  }));

  return (
    <section>
      <h2>Last 24 hours</h2>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -24 }}>
          <CartesianGrid stroke="#eee" vertical={false} />
          <XAxis dataKey="time" stroke="#666" fontSize={12} minTickGap={40} />
          <YAxis stroke="#666" fontSize={12} allowDecimals={false} />
          <Tooltip />
          <Line type="monotone" dataKey="people" stroke="#111" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  );
}
