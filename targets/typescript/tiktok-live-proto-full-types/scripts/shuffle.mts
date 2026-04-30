/**
 * Reorder interface fields in generated .ts output so that the source order
 * (which mirrors proto field numbers) cannot be inferred. Sort is alphabetical
 * — deterministic across builds, but unrelated to the wire layout.
 *
 * Implementation: parse with `@babel/parser` (TypeScript plugin), sort each
 * `TSInterfaceDeclaration` body by property name, regenerate with
 * `@babel/generator`. AST-based, so it can't accidentally fracture interface
 * boundaries the way a regex/line-based pass can.
 */
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';
import _generate from '@babel/generator';
import * as t from '@babel/types';

const generate = ((_generate as unknown) as { default: typeof _generate }).default ?? _generate;

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = resolve(__dirname, '..');
const GEN_DIR = resolve(PKG_ROOT, 'src/generated');

function listTsFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) out.push(...listTsFiles(full));
    else if (st.isFile() && full.endsWith('.ts')) out.push(full);
  }
  return out;
}

function memberKey(node: t.TSTypeElement): string {
  if (t.isTSPropertySignature(node) || t.isTSMethodSignature(node)) {
    if (t.isIdentifier(node.key)) return node.key.name;
    if (t.isStringLiteral(node.key)) return node.key.value;
    if (t.isNumericLiteral(node.key)) return String(node.key.value);
  }
  // Index signatures and call signatures: keep them at the end, stably.
  return '~';
}

function shuffleAst(ast: t.File): boolean {
  let changed = false;
  for (const stmt of ast.program.body) {
    const decl = t.isExportNamedDeclaration(stmt) ? stmt.declaration : stmt;
    if (!decl || !t.isTSInterfaceDeclaration(decl)) continue;
    const body = decl.body.body;
    if (body.length <= 1) continue;
    const before = body.map(memberKey).join('|');
    body.sort((a, b) => memberKey(a).localeCompare(memberKey(b)));
    const after = body.map(memberKey).join('|');
    if (before !== after) changed = true;
  }
  return changed;
}

function processFile(path: string): boolean {
  const original = readFileSync(path, 'utf8');
  const ast = parse(original, {
    sourceType: 'module',
    plugins: ['typescript'],
    attachComment: true,
  });
  if (!shuffleAst(ast)) return false;
  const { code } = generate(ast, { retainLines: false, jsescOption: { quotes: 'single' } });
  writeFileSync(path, code.endsWith('\n') ? code : code + '\n', 'utf8');
  return true;
}

function main(): void {
  const files = listTsFiles(GEN_DIR);
  let changed = 0;
  for (const file of files) {
    if (processFile(file)) changed++;
  }
  console.log(`shuffle: rewrote ${changed} of ${files.length} files`);
}

main();
