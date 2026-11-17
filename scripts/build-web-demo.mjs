import assert from "node:assert/strict";
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const root = resolve(dirname(fileURLToPath(import.meta.url)), ".."), output = resolve(root, "web-dist");
const recording = JSON.parse(readFileSync(resolve(root, "demo/recording.json"), "utf8"));
assert.equal(recording.mode, "recorded-synthetic-replay"); assert.ok(recording.frames.length >= 40);
// Publish only a static replay, never the Python service or its local database.
rmSync(output, { recursive: true, force: true }); mkdirSync(resolve(output, "demo"), { recursive: true });
for (const file of ["app.js", "replay.js", "styles.css"]) copyFileSync(resolve(root, "dashboard", file), resolve(output, file));
const html = readFileSync(resolve(root, "dashboard/index.html"), "utf8").replace("</head>", '<meta name="sentinel-mode" content="recorded-replay">\n</head>');
assert.ok(html.includes('id="data-notice"') && html.includes('type="module"'));
writeFileSync(resolve(output, "index.html"), html);
copyFileSync(resolve(root, "demo/recording.json"), resolve(output, "demo/recording.json"));
console.log(`Static Vercel replay built: ${recording.frames.length} recorded synthetic events. No Python runtime or live ingestion required.`);
