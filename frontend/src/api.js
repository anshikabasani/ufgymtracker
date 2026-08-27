// Two ways to get the same data:
//
// Deployed  — VITE_DATA_BASE points at the repo's data/ directory on
//             GitHub. There's no server; a scheduled job commits readings
//             and the page just reads the file.
// Local dev — falls back to the FastAPI server, proxied by Vite.
//
// Both return the same shape, so the components don't know the difference.
const DATA_BASE = import.meta.env.VITE_DATA_BASE;

async function getJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }
  return response.json();
}

async function fetchStatic() {
  // raw.githubusercontent.com caches for a few minutes; no-cache asks
  // the browser not to add its own staleness on top of that.
  return getJson(`${DATA_BASE}/recent.json`, { cache: "no-cache" });
}

async function fetchFromApi() {
  const [current, history] = await Promise.all([
    getJson("/api/current"),
    getJson("/api/history?hours=48"),
  ]);
  return { current, readings: history.readings };
}

export const fetchSnapshot = () => (DATA_BASE ? fetchStatic() : fetchFromApi());

export const isStaticMode = Boolean(DATA_BASE);
export const frameUrl = () => "/api/frame";
