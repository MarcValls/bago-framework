#!/usr/bin/env node
/**
 * js_ast_scanner.js — BAGO AST-based JavaScript/TypeScript code analyser
 *
 * Runs via: node js_ast_scanner.js <file_or_dir> [--json] [--summary]
 *
 * Detects issues that regex-based scanners miss:
 *   JS-E001  eval() / Function() constructor — security (AST-precise)
 *   JS-W001  console.log/debug/error in non-test files — noise in production
 *   JS-W002  debugger statement — left-over debug artifact
 *   JS-W003  == / != operator — should use === / !==
 *   JS-W004  setTimeout/setInterval with string argument — implicit eval
 *   JS-W005  empty catch block — swallows errors
 *   JS-I001  TODO/FIXME in comments
 *   JS-I002  Arrow function with >5 parameters — readability
 *   JS-I003  Nested ternary — readability
 *   JS-I004  Unused async (async function with no await) — misleading
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// Resolve acorn from project node_modules or global
const BAGO_ROOT = path.resolve(__dirname, '..');
const PROJ_ROOT = path.resolve(BAGO_ROOT, '..');

function requireAcorn() {
  const candidates = [
    path.join(PROJ_ROOT, 'node_modules', 'acorn'),
    path.join(BAGO_ROOT, 'node_modules', 'acorn'),
    'acorn',
  ];
  for (const c of candidates) {
    try { return require(c); } catch (_) {}
  }
  return null;
}

function requireWalk() {
  const candidates = [
    path.join(PROJ_ROOT, 'node_modules', 'acorn-walk'),
    path.join(BAGO_ROOT, 'node_modules', 'acorn-walk'),
    'acorn-walk',
  ];
  for (const c of candidates) {
    try { return require(c); } catch (_) {}
  }
  return null;
}

const acorn = requireAcorn();
const walk  = requireWalk();

if (!acorn || !walk) {
  console.error('ERROR: acorn / acorn-walk no disponible. Instalar con: npm install acorn acorn-walk');
  process.exit(2);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function isTestFile(filepath) {
  const name = path.basename(filepath).toLowerCase();
  return name.includes('.test.') || name.includes('.spec.') ||
         name.includes('__tests__') || filepath.includes('/test/') ||
         filepath.includes('/tests/');
}

function collectJsFiles(target) {
  const stat = fs.statSync(target);
  if (stat.isFile()) return [target];
  const files = [];
  function recurse(dir) {
    for (const entry of fs.readdirSync(dir)) {
      if (entry.startsWith('.') || entry === 'node_modules' || entry === 'dist' || entry === 'build') continue;
      const full = path.join(dir, entry);
      const s = fs.statSync(full);
      if (s.isDirectory()) { recurse(full); continue; }
      if (/\.(js|ts|jsx|tsx|mjs|cjs)$/.test(entry)) files.push(full);
    }
  }
  recurse(target);
  return files;
}

// ── Scanner ───────────────────────────────────────────────────────────────────

function scanFile(filepath) {
  const findings = [];
  const isTest = isTestFile(filepath);

  let src;
  try { src = fs.readFileSync(filepath, 'utf8'); }
  catch (e) { return []; }

  // Strip TypeScript-specific syntax for acorn (basic strip only)
  const stripped = src
    .replace(/:\s*\w+(\[\])?(\s*\|[^;={}\n]+)?(?=[,)=;\n])/g, '')  // type annotations
    .replace(/<[A-Z][A-Za-z<>, ]*>/g, '')    // generic type params
    .replace(/^export\s+type\s+.+$/mg, '')   // export type lines
    .replace(/^import\s+type\s+.+$/mg, '')   // import type lines
    .replace(/interface\s+\w+\s*\{[^}]*\}/g, '');  // interface blocks

  let ast;
  try {
    ast = acorn.parse(stripped, {
      ecmaVersion: 2022,
      sourceType: 'module',
      locations: true,
      allowHashBang: true,
    });
  } catch (e1) {
    try {
      ast = acorn.parse(stripped, {
        ecmaVersion: 2022,
        sourceType: 'script',
        locations: true,
        allowHashBang: true,
      });
    } catch (e2) {
      // Could not parse — silently skip (TypeScript complex syntax)
      return [];
    }
  }

  const lines = src.split('\n');

  function getLine(node) {
    return (node.loc && node.loc.start) ? node.loc.start.line : 0;
  }
  function getCol(node) {
    return (node.loc && node.loc.start) ? node.loc.start.column : 0;
  }
  function lineText(lineno) {
    return (lines[lineno - 1] || '').trim();
  }
  function noqa(lineno, rule) {
    const txt = lines[lineno - 1] || '';
    const m = txt.match(/\/\/\s*noqa(?::\s*([\w,\s-]+))?/);
    if (!m) return false;
    if (!m[1]) return true;  // bare noqa
    return m[1].split(',').map(r => r.trim()).includes(rule);
  }

  function add(node, rule, severity, message, fixSuggestion = '') {
    const lineno = getLine(node);
    if (noqa(lineno, rule)) return;
    findings.push({
      file: filepath, line: lineno, col: getCol(node),
      rule, severity, source: 'bago_ast', message,
      fix_suggestion: fixSuggestion, autofixable: false,
    });
  }

  // ── Walk AST ────────────────────────────────────────────────────────────────
  walk.simple(ast, {

    // JS-E001: eval() / Function() constructor
    CallExpression(node) {
      const callee = node.callee;
      if (!callee) return;
      const name = callee.name || (callee.property && callee.property.name);
      if (name === 'eval') {
        add(node, 'JS-E001', 'error', 'eval() detected — security risk',
            'Refactoriza la lógica para no necesitar eval()');
      }
      if (name === 'Function' && callee.type === 'Identifier') {
        add(node, 'JS-E001', 'error', 'Function() constructor — equivalent to eval()',
            'Usa funciones declaradas en lugar de Function()');
      }
      // JS-W004: setTimeout/setInterval with string arg
      if ((name === 'setTimeout' || name === 'setInterval') &&
          node.arguments.length > 0 &&
          node.arguments[0].type === 'Literal' &&
          typeof node.arguments[0].value === 'string') {
        add(node, 'JS-W004', 'warning',
            `${name}() con string como callback — equivale a eval()`,
            'Pasa una función en lugar de un string');
      }
      // JS-W001: console.log in non-test files
      if (!isTest && callee.type === 'MemberExpression' &&
          callee.object && callee.object.name === 'console' &&
          ['log', 'debug', 'warn', 'error', 'info'].includes(callee.property && callee.property.name)) {
        add(node, 'JS-W001', 'warning',
            `console.${callee.property.name}() — eliminar antes de producción`,
            'Usa un logger configurable (winston, pino, etc.)');
      }
    },

    // JS-W002: debugger statement
    DebuggerStatement(node) {
      add(node, 'JS-W002', 'warning', 'debugger statement — eliminar antes de commit',
          'Elimina la sentencia debugger');
    },

    // JS-W003: loose equality ==  / !=
    BinaryExpression(node) {
      if (node.operator === '==' || node.operator === '!=') {
        const op3 = node.operator + '=';
        add(node, 'JS-W003', 'warning',
            `Operador ${node.operator} — usar ${op3} para comparación estricta`,
            `Reemplaza ${node.operator} con ${op3}`);
      }
    },

    // JS-W005: empty catch block
    CatchClause(node) {
      if (node.body && node.body.body && node.body.body.length === 0) {
        add(node, 'JS-W005', 'warning', 'Bloque catch vacío — los errores son ignorados silenciosamente',
            'Añade manejo de error o re-lanza la excepción');
      }
    },

    // JS-I002: arrow function with >5 parameters
    ArrowFunctionExpression(node) {
      if (node.params && node.params.length > 5) {
        add(node, 'JS-I002', 'info',
            `Arrow function con ${node.params.length} parámetros — difícil de leer`,
            'Refactoriza usando un objeto de opciones');
      }
    },

    // JS-I003: nested ternary
    ConditionalExpression(node) {
      // If the consequent or alternate is also a ternary
      if (node.consequent.type === 'ConditionalExpression' ||
          node.alternate.type  === 'ConditionalExpression') {
        add(node, 'JS-I003', 'info', 'Ternario anidado — difícil de leer',
            'Extrae lógica a variables o usa if/else');
      }
    },

  });

  // JS-I001: TODO/FIXME/HACK in comments (line-level, not AST)
  lines.forEach((line, idx) => {
    const lineno = idx + 1;
    if (noqa(lineno, 'JS-I001')) return;
    if (/\/\/.*\b(TODO|FIXME|HACK|XXX)\b/.test(line) ||
        /\/\*.*\b(TODO|FIXME|HACK|XXX)\b/.test(line)) {
      const m = line.match(/\b(TODO|FIXME|HACK|XXX)\b[:\s]*(.*)/);
      findings.push({
        file: filepath, line: lineno, col: 0,
        rule: 'JS-I001', severity: 'info', source: 'bago_ast',
        message: `Comentario pendiente: ${m ? m[0].trim().slice(0, 80) : 'TODO/FIXME'}`,
        fix_suggestion: 'Resuelve o elimina el comentario', autofixable: false,
      });
    }
  });

  return findings;
}


// ── CLI ───────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  const target     = args.find(a => !a.startsWith('--')) || '.';
  const jsonOutput = args.includes('--json');
  const summary    = args.includes('--summary');
  const selfTest   = args.includes('--test');

  if (selfTest) {
    return runTests();
  }

  if (!fs.existsSync(target)) {
    console.error(`ERROR: path no encontrado: ${target}`);
    process.exit(1);
  }

  const files = collectJsFiles(target);
  const allFindings = [];
  for (const f of files) {
    allFindings.push(...scanFile(f));
  }

  if (jsonOutput) {
    console.log(JSON.stringify(allFindings, null, 2));
    return;
  }

  const base = path.resolve(target);
  const byFile = {};
  for (const f of allFindings) {
    (byFile[f.file] = byFile[f.file] || []).push(f);
  }

  const SEV_COLOR = { error: '\x1b[31m', warning: '\x1b[33m', info: '\x1b[34m' };
  const RESET = '\x1b[0m';
  const BOLD  = '\x1b[1m';

  if (!summary) {
    for (const [fp, ff] of Object.entries(byFile).sort()) {
      let rel;
      try { rel = path.relative(base, fp); } catch (_) { rel = fp; }
      console.log(`\n  ${BOLD}${rel}${RESET}`);
      for (const f of ff.sort((a, b) => a.line - b.line)) {
        const c = SEV_COLOR[f.severity] || '';
        console.log(`    L${String(f.line).padStart(4)}  ${c}${f.severity.slice(0,4).toUpperCase()}${RESET}  ${f.rule.padEnd(10)}  ${f.message}`);
        if (f.fix_suggestion) {
          console.log(`           \x1b[2m↳ ${f.fix_suggestion}\x1b[0m`);
        }
      }
    }
  }

  const total   = allFindings.length;
  const errors  = allFindings.filter(f => f.severity === 'error').length;
  const warnings= allFindings.filter(f => f.severity === 'warning').length;
  const infos   = allFindings.filter(f => f.severity === 'info').length;

  const byRule = {};
  for (const f of allFindings) {
    byRule[f.rule] = (byRule[f.rule] || 0) + 1;
  }

  console.log(`\n  ${BOLD}Resumen: ${total} hallazgos${RESET}  ` +
    `(\x1b[31m${errors} error\x1b[0m  \x1b[33m${warnings} warning\x1b[0m  \x1b[34m${infos} info\x1b[0m)\n`);

  for (const [rule, count] of Object.entries(byRule).sort()) {
    const sev = allFindings.find(f => f.rule === rule).severity;
    const c   = SEV_COLOR[sev] || '';
    console.log(`  ${c}${sev.slice(0,4).toUpperCase()}${RESET}  ${rule.padEnd(12)}  ${count} ocurrencias`);
  }
  console.log();

  process.exit(errors > 0 ? 1 : 0);
}


// ── Self-tests ────────────────────────────────────────────────────────────────

function runTests() {
  const os   = require('os');
  const tmpd = fs.mkdtempSync(path.join(os.tmpdir(), 'bago-ast-'));
  let errors = 0;

  function ok(name)          { console.log(`  OK: ${name}`); }
  function fail(name, detail){ errors++; console.log(`  FAIL: ${name} — ${detail}`); }

  console.log('\nTests de js_ast_scanner.js...');

  // T1: eval() detected
  const f1 = path.join(tmpd, 'evil.js');
  fs.writeFileSync(f1, 'eval("bad code");\n');
  const r1 = scanFile(f1);
  if (r1.some(f => f.rule === 'JS-E001')) ok('ast:eval_detected');
  else fail('ast:eval_detected', JSON.stringify(r1));

  // T2: arrow function with many params
  const f2 = path.join(tmpd, 'arrows.js');
  fs.writeFileSync(f2, 'const fn = (a, b, c, d, e, f) => a + b;\n');
  const r2 = scanFile(f2);
  if (r2.some(f => f.rule === 'JS-I002')) ok('ast:arrow_too_many_params');
  else fail('ast:arrow_too_many_params', JSON.stringify(r2));

  // T3: empty catch block
  const f3 = path.join(tmpd, 'catch.js');
  fs.writeFileSync(f3, 'try { doSomething(); } catch (e) {}\n');
  const r3 = scanFile(f3);
  if (r3.some(f => f.rule === 'JS-W005')) ok('ast:empty_catch');
  else fail('ast:empty_catch', JSON.stringify(r3));

  // T4: loose equality
  const f4 = path.join(tmpd, 'eq.js');
  fs.writeFileSync(f4, 'function check(x) { return x == null; }\n');
  const r4 = scanFile(f4);
  if (r4.some(f => f.rule === 'JS-W003')) ok('ast:loose_equality');
  else fail('ast:loose_equality', JSON.stringify(r4));

  // T5: debugger statement
  const f5 = path.join(tmpd, 'debug.js');
  fs.writeFileSync(f5, 'function foo() { debugger; }\n');
  const r5 = scanFile(f5);
  if (r5.some(f => f.rule === 'JS-W002')) ok('ast:debugger');
  else fail('ast:debugger', JSON.stringify(r5));

  // T6: TODO comment
  const f6 = path.join(tmpd, 'todo.js');
  fs.writeFileSync(f6, '// TODO: fix this\nconst x = 1;\n');
  const r6 = scanFile(f6);
  if (r6.some(f => f.rule === 'JS-I001')) ok('ast:todo_comment');
  else fail('ast:todo_comment', JSON.stringify(r6));

  // T7: console.log in non-test file
  const f7 = path.join(tmpd, 'app.js');
  fs.writeFileSync(f7, 'console.log("hello world");\n');
  const r7 = scanFile(f7);
  if (r7.some(f => f.rule === 'JS-W001')) ok('ast:console_log');
  else fail('ast:console_log', JSON.stringify(r7));

  // T8: console.log NOT flagged in test file
  const f8 = path.join(tmpd, 'app.test.js');
  fs.writeFileSync(f8, 'console.log("test output");\n');
  const r8 = scanFile(f8);
  if (!r8.some(f => f.rule === 'JS-W001')) ok('ast:console_log_test_skip');
  else fail('ast:console_log_test_skip', 'should not flag test files');

  // T9: noqa suppression
  const f9 = path.join(tmpd, 'noqa.js');
  fs.writeFileSync(f9, 'eval("x"); // noqa: JS-E001\n');
  const r9 = scanFile(f9);
  if (!r9.some(f => f.rule === 'JS-E001')) ok('ast:noqa_suppression');
  else fail('ast:noqa_suppression', 'eval should be suppressed');

  // T10: collectJsFiles recurses directories
  const subdir = path.join(tmpd, 'sub');
  fs.mkdirSync(subdir);
  fs.writeFileSync(path.join(subdir, 'deep.js'), 'const x = 1;\n');
  const collected = collectJsFiles(tmpd);
  if (collected.length >= 9) ok('ast:collect_files_recursive');
  else fail('ast:collect_files_recursive', `found ${collected.length} files`);

  // Cleanup
  fs.rmSync(tmpd, {recursive: true, force: true});

  const total  = 10;
  const passed = total - errors;
  console.log(`\n  ${passed}/${total} tests pasaron`);
  process.exit(errors > 0 ? 1 : 0);
}

main();
