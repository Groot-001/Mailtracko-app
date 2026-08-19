const fs = require("fs");
const path = require("path");

let ts;
try {
  ts = require(path.resolve(__dirname, "../frontend/node_modules/typescript"));
} catch {
  try {
    ts = require("typescript");
  } catch {
    const globalCandidates = [
      "/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript",
      "/usr/local/lib/node_modules/typescript",
    ];
    const candidate = globalCandidates.find((item) => fs.existsSync(item));
    if (!candidate) {
      console.error("TypeScript is not installed. Run npm install from the project root first.");
      process.exit(2);
    }
    ts = require(candidate);
  }
}

const sourceRoot = path.resolve(__dirname, "../frontend/src");

function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return walk(fullPath);
    return /\.(ts|tsx)$/.test(entry.name) ? [fullPath] : [];
  });
}

function hasExportModifier(statement) {
  return Boolean(
    statement.modifiers?.some(
      (modifier) =>
        modifier.kind === ts.SyntaxKind.ExportKeyword ||
        modifier.kind === ts.SyntaxKind.DefaultKeyword,
    ),
  );
}

const problems = [];

for (const file of walk(sourceRoot)) {
  const text = fs.readFileSync(file, "utf8");
  const sourceFile = ts.createSourceFile(
    file,
    text,
    ts.ScriptTarget.Latest,
    true,
    file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );

  const counts = new Map();
  const countIdentifiers = (node) => {
    if (ts.isIdentifier(node)) {
      counts.set(node.text, (counts.get(node.text) || 0) + 1);
    }
    ts.forEachChild(node, countIdentifiers);
  };
  countIdentifiers(sourceFile);

  const lineOf = (node) => sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;
  const add = (kind, name, node) => {
    problems.push({
      file: path.relative(sourceRoot, file).replaceAll(path.sep, "/"),
      line: lineOf(node),
      kind,
      name,
    });
  };

  const functionHasBody = (node) =>
    (ts.isFunctionDeclaration(node) ||
      ts.isFunctionExpression(node) ||
      ts.isArrowFunction(node) ||
      ts.isMethodDeclaration(node) ||
      ts.isConstructorDeclaration(node) ||
      ts.isGetAccessor(node) ||
      ts.isSetAccessor(node)) &&
    Boolean(node.body);

  const collectBinding = (name, kind, skip) => {
    if (ts.isIdentifier(name)) {
      if (!skip && counts.get(name.text) === 1 && !name.text.startsWith("_")) {
        add(kind, name.text, name);
      }
      return;
    }
    if (ts.isObjectBindingPattern(name) || ts.isArrayBindingPattern(name)) {
      for (const element of name.elements) {
        if (ts.isBindingElement(element)) collectBinding(element.name, kind, skip);
      }
    }
  };

  const visit = (node) => {
    if (ts.isImportDeclaration(node) && node.importClause) {
      const clause = node.importClause;
      if (clause.name && counts.get(clause.name.text) === 1) {
        add("unused import", clause.name.text, clause.name);
      }
      const bindings = clause.namedBindings;
      if (bindings && ts.isNamespaceImport(bindings) && counts.get(bindings.name.text) === 1) {
        add("unused import", bindings.name.text, bindings.name);
      }
      if (bindings && ts.isNamedImports(bindings)) {
        for (const element of bindings.elements) {
          if (counts.get(element.name.text) === 1) {
            add("unused import", element.name.text, element.name);
          }
        }
      }
    }

    if (
      ts.isParameter(node) &&
      ts.isIdentifier(node.name) &&
      functionHasBody(node.parent) &&
      counts.get(node.name.text) === 1 &&
      !node.name.text.startsWith("_")
    ) {
      add("unused parameter", node.name.text, node.name);
    }

    if (ts.isVariableStatement(node)) {
      const skip = hasExportModifier(node);
      for (const declaration of node.declarationList.declarations) {
        collectBinding(declaration.name, "unused local", skip);
      }
    }

    ts.forEachChild(node, visit);
  };

  visit(sourceFile);
}

if (problems.length) {
  for (const problem of problems) {
    console.error(
      `${problem.file}:${problem.line}: ${problem.kind} '${problem.name}'`,
    );
  }
  console.error(`TypeScript unused-declaration check failed: ${problems.length} problem(s).`);
  process.exit(1);
}

console.log("TypeScript unused-declaration check passed.");
