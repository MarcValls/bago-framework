#!/usr/bin/env node
/**
 * ts_ast.js — Parse TypeScript/TSX files to ESTree-compatible JSON using
 * @typescript-eslint/typescript-estree.
 *
 * Usage: node ts_ast.js <filepath>
 *
 * Outputs compact JSON to stdout with the same top-level shape as acorn's AST,
 * making it compatible with hotspot.py's _count_js_ast_nodes().
 * Exits 1 on parse error (Python falls back to regex).
 */

"use strict";

const path = require("path");
const fs   = require("fs");

const filePath = process.argv[2];
if (!filePath) {
  process.stderr.write("Usage: node ts_ast.js <filepath>\n");
  process.exit(1);
}

let parse;
try {
  ({ parse } = require("@typescript-eslint/typescript-estree"));
} catch (e) {
  process.stderr.write(`typescript-estree not available: ${e.message}\n`);
  process.exit(1);
}

const src = fs.readFileSync(filePath, "utf8");
const isTsx = filePath.endsWith(".tsx");

let ast;
try {
  ast = parse(src, {
    jsx:           isTsx,
    loc:           false,
    range:         false,
    comment:       false,
    tokens:        false,
    errorOnUnknownASTType: false,
  });
} catch (e) {
  process.stderr.write(`parse error: ${e.message}\n`);
  process.exit(1);
}

process.stdout.write(JSON.stringify(ast));
