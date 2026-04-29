/**
 * Reorder interface fields in generated .ts output so that the source order
 * (which mirrors proto field numbers) cannot be inferred. Sort is alphabetical
 * — deterministic across builds, but unrelated to the wire layout.
 */
import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = resolve(__dirname, '..');
const GEN_DIR = resolve(PKG_ROOT, 'src/generated');

const INTERFACE_RE = /(export interface \w+(?:<[^>]*>)?\s*\{\n)([\s\S]*?)(\n\})/g;

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

/**
 * Group an interface body's lines into "items" — each item is a single field,
 * including any leading JSDoc comment block that belongs to it.
 */
function groupItems(body: string): string[] {
  const lines = body.split('\n');
  const items: string[] = [];
  let buffer: string[] = [];

  const flush = () => {
    if (buffer.length === 0) return;
    items.push(buffer.join('\n'));
    buffer = [];
  };

  for (const line of lines) {
    if (line.trim() === '') {
      flush();
      continue;
    }
    buffer.push(line);
    // A field declaration ends with a semicolon at indent level.
    if (/;\s*$/.test(line)) flush();
  }
  flush();
  return items;
}

function fieldName(item: string): string {
  // Skip leading comment block and pull the first `name:` or `name?:`.
  for (const line of item.split('\n')) {
    const m = line.match(/^\s*(\w+)\??\s*:/);
    if (m) return m[1];
  }
  return item;
}

function shuffleBody(body: string): string {
  const items = groupItems(body);
  if (items.length <= 1) return body;
  items.sort((a, b) => fieldName(a).localeCompare(fieldName(b)));
  return items.join('\n');
}

function processFile(path: string): boolean {
  const original = readFileSync(path, 'utf8');
  const updated = original.replace(INTERFACE_RE, (_, head, body, tail) => {
    return head + shuffleBody(body) + tail;
  });
  if (updated !== original) {
    writeFileSync(path, updated, 'utf8');
    return true;
  }
  return false;
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
