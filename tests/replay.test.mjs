import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { snapshotAt } from "../dashboard/replay.js";
const recording = JSON.parse(readFileSync(new URL("../demo/recording.json", import.meta.url), "utf8"));
test("replay reveals no future events", () => {
  const early = snapshotAt(recording, 12), later = snapshotAt(recording, 70);
  assert.equal(early.metrics.readings, 12); assert.equal(later.metrics.readings, 70);
  assert.ok(early.readings.every(r => r.id <= 12)); assert.ok(early.alerts.every(a => a.reading_id <= 12));
  assert.ok(later.readings.every(r => r.id > 30 && r.id <= 70)); assert.equal(later.readings.length, 40);
});
test("totals count actual recorded alerts and preserve severity", () => {
  const full = snapshotAt(recording, 160), alerts = recording.frames.flatMap(f => f.alerts);
  assert.equal(full.metrics.alerts, alerts.length); assert.equal(full.metrics.open, alerts.filter(a => a.status === "OPEN").length);
  assert.equal(full.metrics.critical, alerts.filter(a => a.severity === "CRITICAL").length);
  assert.ok(full.metrics.critical > 0); assert.equal(full.alerts.length, 20);
  assert.ok(full.alerts.every((a, i, arr) => i === 0 || a.reading_id <= arr[i - 1].reading_id));
});
test("replay positions are bounded and reading does not modify the recording", () => {
  const before = JSON.stringify(recording); assert.equal(snapshotAt(recording, 999).metrics.readings, 160);
  assert.equal(snapshotAt(recording, 0).metrics.readings, 1); assert.equal(JSON.stringify(recording), before);
  assert.throws(() => snapshotAt({ frames: [] }, 1), /empty/); assert.throws(() => snapshotAt(recording, NaN), /Invalid/);
});
test("the recording has explicit synthetic labels and precomputed model scores", () => {
  assert.equal(recording.mode, "recorded-synthetic-replay");
  assert.ok(recording.frames.every(f => Number.isFinite(f.reading.anomaly_score) && [0, 1].includes(f.reading.is_anomaly)));
  assert.ok(recording.frames.some(f => f.alerts.length > 0));
});
