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

const ts = loadTypeScript();

const frontend = path.resolve(__dirname, "..", "frontend");
const files = [];
function walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    if (["node_modules", "dist"].includes(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) walk(target);
    else if (/\.(ts|tsx)$/.test(entry.name)) files.push(target);
  }
}
walk(path.join(frontend, "src"));
files.push(path.join(frontend, "vite.config.ts"));

const failures = [];
for (const file of files) {
  const source = fs.readFileSync(file, "utf8");
  const result = ts.transpileModule(source, {
    fileName: file,
    compilerOptions: {
      target: ts.ScriptTarget.ES2022,
      module: ts.ModuleKind.ESNext,
      jsx: ts.JsxEmit.ReactJSX,
    },
    reportDiagnostics: true,
  });
  for (const diagnostic of result.diagnostics || []) {
    if (diagnostic.category !== ts.DiagnosticCategory.Error) continue;
    const location = diagnostic.file && diagnostic.start != null
      ? diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start)
      : null;
    failures.push(
      `${path.relative(frontend, file)}${location ? `:${location.line + 1}:${location.character + 1}` : ""} ` +
      `TS${diagnostic.code} ${ts.flattenDiagnosticMessageText(diagnostic.messageText, " ")}`,
    );
  }
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log(`Frontend syntax check passed: ${files.length} TypeScript/TSX files.`);
