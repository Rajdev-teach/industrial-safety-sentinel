import { snapshotAt } from "./replay.js";

const $ = id => document.getElementById(id);
const replayMode = document.querySelector('meta[name="sentinel-mode"]')?.content === "recorded-replay";
let history = [], recording, position = 40, paused = false, refreshing = false;
function setConnection(label, healthy) {
  $("connection-status").textContent = label;
  $("connection-status").className = healthy ? "healthy" : "disconnected";
  $("feed-label").textContent = healthy ? (replayMode ? "RECORDED REPLAY" : "SIMULATED LIVE") : "DISCONNECTED";
  $("feed-state").classList.toggle("offline", !healthy);
  if (healthy) $("data-notice").textContent = replayMode ? "Recorded synthetic replay. Model scores and alerts were computed offline; no live sensors, camera stream, or model inference runs on Vercel." : "Synthetic portfolio demonstration. Events are simulated, not connected to live workplace sensors.";
}
function conditions(row) {
  if (!row) { $("visionText").textContent = "Waiting for synthetic events"; return; }
  $("zone").textContent = `${row.zone} · ${row.device_id}`;
  const values = [["Temperature", `${row.temperature_c} °C`], ["Vibration", `${row.vibration_mm_s} mm/s`], ["Forklift speed", `${row.forklift_speed_mph} mph`], ["Noise", `${row.noise_db} dB`]];
  $("conditions").replaceChildren(...values.map(([label, value]) => {
    const card = document.createElement("div"); card.className = "condition";
    const name = document.createElement("small"); name.textContent = label;
    const reading = document.createElement("b"); reading.textContent = value;
    card.append(name, reading); return card;
  }));
  const worker = Boolean(row.worker_present);
  $("visionText").textContent = !worker ? "No worker detected in this synthetic event" : row.restricted_zone ? "Restricted-zone violation detected" : (!row.helmet_detected || !row.vest_detected) ? "PPE violation detected" : "PPE and zone checks passed for this synthetic event";
  const outline = $("visionBox").querySelector(".person"); outline.hidden = !worker;
  outline.classList.toggle("unsafe", worker && Boolean(row.restricted_zone || !row.helmet_detected || !row.vest_detected));
}
function renderAlerts(rows) {
  const nodes = rows.slice(0, 7).map(alert => {
    const node = document.createElement("div"); node.className = "alert";
    const severity = document.createElement("span"); severity.className = `sev ${alert.severity === "CRITICAL" ? "CRITICAL" : "WARNING"}`; severity.textContent = alert.severity;
    const text = document.createElement("p"); text.append(document.createTextNode(alert.message), document.createElement("br"));
    const detail = document.createElement("small"); detail.textContent = `${alert.zone} · ${alert.alert_type}`; text.append(detail);
    const time = document.createElement("small"); time.textContent = alert.timestamp.slice(11, 19);
    node.append(severity, text, time); return node;
  });
  if (!nodes.length) { const empty = document.createElement("p"); empty.textContent = "No alerts in the displayed data"; nodes.push(empty); }
  $("alerts").replaceChildren(...nodes);
}
function chart(rows) {
  const canvas = $("chart"), ratio = devicePixelRatio || 1, width = canvas.clientWidth, height = canvas.clientHeight;
  canvas.width = width * ratio; canvas.height = height * ratio;
  const context = canvas.getContext("2d"); if (!context || width < 60) return;
  context.scale(ratio, ratio); context.clearRect(0, 0, width, height); context.strokeStyle = "#1f3549";
  for (let i = 0; i < 5; i++) { const y = 24 + i * (height - 48) / 4; context.beginPath(); context.moveTo(35, y); context.lineTo(width - 10, y); context.stroke(); }
  const series = [["temperature_c", "#22d3ee", 110], ["noise_db", "#a78bfa", 120], ["vibration_mm_s", "#fb7185", 20]];
  series.forEach(([key, color, max]) => { context.strokeStyle = color; context.lineWidth = 2; context.beginPath(); rows.forEach((row, i) => { const x = 35 + i * (width - 50) / Math.max(rows.length - 1, 1), y = height - 24 - row[key] / max * (height - 48); i ? context.lineTo(x, y) : context.moveTo(x, y); }); context.stroke(); });
  context.font = "10px monospace";
  [["TEMP / 110 °C", "#22d3ee", 35], ["NOISE / 120 dB", "#a78bfa", 155], ["VIB / 20 mm/s", "#fb7185", 285]].forEach(([label, color, x]) => { context.fillStyle = color; context.fillText(label, x, 13); });
}
async function json(url) { const response = await fetch(url, { cache: "no-store" }); if (!response.ok) throw new Error(`Data request failed (${response.status})`); return response.json(); }
async function refresh() {
  if (refreshing || (replayMode && paused)) return; refreshing = true;
  try {
    let metrics, readings, alerts;
    if (replayMode) {
      recording ??= await json("./demo/recording.json"); if (position > recording.frames.length) position = 1;
      ({ metrics, readings, alerts } = snapshotAt(recording, position++));
      $("replay-position").textContent = `${metrics.readings} / ${recording.frames.length} events · recorded ${readings.at(-1).timestamp.slice(0, 10)}`;
    } else [metrics, readings, alerts] = await Promise.all(["/api/metrics", "/api/readings", "/api/alerts"].map(json));
    ["readings", "open", "critical"].forEach(key => { $(key).textContent = metrics[key]; });
    history = readings; conditions(readings.at(-1)); renderAlerts(alerts); chart(readings); setConnection(replayMode ? "REPLAY" : "ONLINE", true);
  } catch (error) { setConnection("OFFLINE", false); $("data-notice").textContent = "Data unavailable. Displayed values may be stale. Check the service and try again."; console.error(error); }
  finally { refreshing = false; }
}
if (replayMode) {
  $("data-notice").textContent = "Recorded synthetic replay. Model scores and alerts were computed offline; no live sensors, camera stream, or model inference runs on Vercel.";
  $("chart-title").textContent = "Recorded Sensor Telemetry"; $("replay-controls").hidden = false;
  $("pause-replay").addEventListener("click", () => { paused = !paused; $("pause-replay").textContent = paused ? "Resume replay" : "Pause replay"; $("connection-status").textContent = paused ? "PAUSED" : "REPLAY"; });
  $("restart-replay").addEventListener("click", () => { position = 1; paused = false; $("pause-replay").textContent = "Pause replay"; void refresh(); });
}
$("retry-data").addEventListener("click", () => void refresh());
void refresh(); setInterval(() => void refresh(), 2000); addEventListener("resize", () => chart(history));
