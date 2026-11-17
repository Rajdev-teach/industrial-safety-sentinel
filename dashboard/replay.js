// Precomputed synthetic output only; no live sensor feed or model inference.
export function snapshotAt(recording, index) {
  if (!Array.isArray(recording.frames) || !recording.frames.length) throw new Error("The demo recording is empty.");
  if (!Number.isFinite(index)) throw new Error("Invalid replay position.");
  const count = Math.min(recording.frames.length, Math.max(1, Math.floor(index)));
  const frames = recording.frames.slice(0, count);
  const allAlerts = frames.flatMap(frame => frame.alerts);
  return {
    metrics: { readings: count, alerts: allAlerts.length, open: allAlerts.filter(a => a.status === "OPEN").length, critical: allAlerts.filter(a => a.severity === "CRITICAL").length },
    readings: frames.slice(-40).map(frame => frame.reading),
    alerts: [...allAlerts].reverse().slice(0, 20),
  };
}
