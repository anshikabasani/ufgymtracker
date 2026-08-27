import { useCallback, useState } from "react";

import "./App.css";
import { fetchSnapshot, frameUrl, isStaticMode } from "./api";
import { usePolling } from "./usePolling";
import { CurrentOccupancy } from "./components/CurrentOccupancy";
import { HistoryChart } from "./components/HistoryChart";

// Deployed, new readings land every ~10-15 minutes, so polling faster
// than that just re-downloads the same file.
const REFRESH_MS = isStaticMode ? 120000 : 10000;

export default function App() {
  // useCallback keeps this function's identity stable across renders.
  // usePolling lists it as an effect dependency, and a fresh function
  // object each render would restart the interval before it ever fired.
  const load = useCallback(() => fetchSnapshot(), []);
  const { data, error } = usePolling(load, REFRESH_MS);

  const [showFrame, setShowFrame] = useState(false);
  // The deployed site has no /api/frame, so the button hides itself if
  // the image fails to load rather than showing a broken thumbnail.
  const [frameAvailable, setFrameAvailable] = useState(!isStaticMode);

  return (
    <main>
      <header>
        <h1>SRFC Weight Room</h1>
        <p className="muted">UF Student Rec Center</p>
      </header>

      <CurrentOccupancy reading={data?.current} error={error} />

      <HistoryChart readings={data?.readings} />

      <p className="note">
        Counts come from the public gym camera and are approximate — people
        hidden behind equipment aren&apos;t counted.
      </p>

      {frameAvailable && (
        <section className="frame">
          <button onClick={() => setShowFrame((shown) => !shown)}>
            {showFrame ? "Hide" : "Show"} detection view
          </button>
          {showFrame && (
            <img
              // The timestamp makes each URL unique, so the browser
              // fetches a fresh frame instead of the cached one.
              src={`${frameUrl()}?t=${data?.current?.recorded ?? ""}`}
              alt="Latest camera frame with detected people boxed"
              onError={() => setFrameAvailable(false)}
            />
          )}
        </section>
      )}
    </main>
  );
}
