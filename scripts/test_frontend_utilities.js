#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const childProcess = require("child_process");

function loadTypeScript() {
  const candidates = [
    path.resolve(__dirname, "..", "frontend", "node_modules", "typescript"),
  ];
  try {
    const globalRoot = childProcess.execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
    if (globalRoot) candidates.push(path.join(globalRoot, "typescript"));
  } catch {
    // Fall through to well-known installation roots.
  }
  candidates.push(
    "/usr/local/lib/node_modules/typescript",
    "/opt/homebrew/lib/node_modules/typescript",
  );
  for (const candidate of candidates) {
    if (!fs.existsSync(candidate)) continue;
    try { return require(candidate); } catch { /* try next candidate */ }
  }
  try { return require("typescript"); } catch {
    console.error("TypeScript is not installed. Run npm ci in the frontend folder first.");
    process.exit(2);
  }
}

const vm = require("vm");
const ts = loadTypeScript();

const root = path.resolve(__dirname, "..");
const sourcePath = path.join(root, "frontend/src/shared/utils/dateTime.ts");
const source = fs.readFileSync(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  fileName: sourcePath,
}).outputText;
const moduleBox = { exports: {} };
vm.runInNewContext(compiled, {
  module: moduleBox,
  exports: moduleBox.exports,
  require,
  Intl,
  Date,
  console,
});
const { zonedLocalDateTimeToIso } = moduleBox.exports;

const checks = [
  ["2026-08-01T10:15", "Asia/Kathmandu", "2026-08-01T04:30:00.000Z"],
  ["2026-01-15T09:00", "America/New_York", "2026-01-15T14:00:00.000Z"],
  ["2026-07-15T09:00", "America/New_York", "2026-07-15T13:00:00.000Z"],
  ["invalid", "UTC", null],
  ["2026-03-08T02:30", "America/New_York", null],
];

let passed = 0;
for (const [value, zone, expected] of checks) {
  const actual = zonedLocalDateTimeToIso(value, zone);
  if (actual !== expected) {
    throw new Error(`${value} in ${zone}: expected ${expected}, got ${actual}`);
  }
  passed += 1;
}
console.log(`Frontend date/time utility validation passed: ${passed} cases.`);
