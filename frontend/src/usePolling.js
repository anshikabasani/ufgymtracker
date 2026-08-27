import { useEffect, useState } from "react";

/**
 * Calls `fetcher` immediately, then every `intervalMs`.
 * Returns { data, error, loading } — re-rendering the component each
 * time new data lands.
 */
export function usePolling(fetcher, intervalMs) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // If the component unmounts mid-request, the response still arrives
    // later — this flag stops us calling setState on a dead component.
    let active = true;

    async function load() {
      try {
        const result = await fetcher();
        if (!active) return;
        setData(result);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    const timer = setInterval(load, intervalMs);

    // Cleanup: React runs this when the component unmounts (or before
    // re-running the effect). Without it, every remount would start
    // another interval and they'd stack up forever.
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [fetcher, intervalMs]);

  return { data, error, loading };
}
