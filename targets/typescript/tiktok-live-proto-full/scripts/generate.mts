import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { load as loadYaml } from 'js-yaml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = resolve(__dirname, '..');
const PROTO_ROOT = resolve(PKG_ROOT, '../../../src/full');
const TMP_DIR = resolve(PKG_ROOT, 'tmp');
const GEN_DIR = resolve(PKG_ROOT, 'src/generated');

const HEADER = `syntax = "proto3";\npackage TikTok;\n\n`;
const LEGACY_VERSIONS = new Set(['v1', 'v2']);

const TARGETS = { node: 'node', web: 'browser' } as const;
type Target = keyof typeof TARGETS;

const TS_PROTO_OPTS = [
  '--ts_proto_opt=forceLong=string',
  '--ts_proto_opt=outputPartialMethods=false',
  '--ts_proto_opt=outputJsonMethods=false',
  '--ts_proto_opt=esModuleInterop=true',
  '--ts_proto_opt=snakeToCamel=true',
  '--ts_proto_opt=importSuffix=.js',
];

function listProtos(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listProtos(full));
    else if (entry.isFile() && entry.name.endsWith('.proto')) out.push(full);
  }
  return out.sort();
}

function stripHeaderLines(content: string): string {
  return content
    .split('\n')
    .filter((line) => !/^\s*(syntax|import|package)\b/.test(line))
    .join('\n')
    .trim();
}

function mergeVersion(version: string): { outDir: string; outFile: string } {
  const srcDir = resolve(PROTO_ROOT, version);
  const protos = listProtos(srcDir);
  if (protos.length === 0) throw new Error(`No .proto files under ${srcDir}`);
  const merged = HEADER + protos.map((p) => stripHeaderLines(readFileSync(p, 'utf8'))).join('\n\n') + '\n';
  const outDir = resolve(TMP_DIR, version);
  mkdirSync(outDir, { recursive: true });
  const outFile = resolve(outDir, 'tiktok-schema.proto');
  writeFileSync(outFile, merged, 'utf8');
  return { outDir, outFile };
}

function resolvePlugin(): string {
  const binName = process.platform === 'win32' ? 'protoc-gen-ts_proto.cmd' : 'protoc-gen-ts_proto';
  const candidates = [
    resolve(PKG_ROOT, 'node_modules/.bin', binName),
    resolve(PKG_ROOT, '../../../node_modules/.bin', binName),
  ];
  for (const c of candidates) if (existsSync(c)) return c;
  throw new Error('protoc-gen-ts_proto not found — run `npm install` in the package first.');
}

/** Legacy path: merge all .proto files into one synthetic schema (v1, v2). */
function generateLegacy(args: {
  version: string;
  target: Target;
  env: string;
  pluginPath: string;
}): void {
  const { version, target, env, pluginPath } = args;
  const { outDir: protoDir, outFile: protoFile } = mergeVersion(version);
  const outGen = resolve(GEN_DIR, target, version);
  mkdirSync(outGen, { recursive: true });

  const cmd = [
    'protoc',
    `--plugin=protoc-gen-ts_proto=${pluginPath}`,
    `--ts_proto_out=${outGen}`,
    `--ts_proto_opt=env=${env}`,
    ...TS_PROTO_OPTS,
    `-I=${protoDir}`,
    protoFile,
  ].join(' ');

  console.log(`[${version}/${target}] protoc legacy (env=${env}) ...`);
  execSync(cmd, { stdio: 'inherit' });

  const schemaFile = resolve(outGen, 'tiktok-schema.ts');
  if (!existsSync(schemaFile)) throw new Error(`ts-proto did not emit ${schemaFile}`);
}

/** Modern path: run protoc against the version dir directly, preserving package + dir layout. */
function generateModern(args: {
  version: string;
  target: Target;
  env: string;
  pluginPath: string;
}): void {
  const { version, target, env, pluginPath } = args;
  const versionDir = resolve(PROTO_ROOT, version);
  const protos = listProtos(versionDir);
  if (protos.length === 0) throw new Error(`No .proto files under ${versionDir}`);

  const outGen = resolve(GEN_DIR, target, version);
  mkdirSync(outGen, { recursive: true });

  const cmd = [
    'protoc',
    `--plugin=protoc-gen-ts_proto=${pluginPath}`,
    `--ts_proto_out=${outGen}`,
    `--ts_proto_opt=env=${env}`,
    ...TS_PROTO_OPTS,
    `-I=${versionDir}`,
    ...protos,
  ].join(' ');

  console.log(`[${version}/${target}] protoc modern (env=${env}, ${protos.length} files) ...`);
  execSync(cmd, { stdio: 'inherit' });
  dedupeDuplicateDeclarations(outGen);
}

const TOP_LEVEL_DECL_RE = /^export (enum|interface|class|type) ([A-Z][A-Za-z0-9_]*)/;
function dedupeDuplicateDeclarations(dir: string): void {
  for (const rel of listGeneratedTs(dir)) {
    const path = resolve(dir, rel);
    const original = readFileSync(path, 'utf8');
    const lines = original.split('\n');
    const seen = new Set<string>();
    let renamed = 0;
    for (let i = 0; i < lines.length; i++) {
      const m = lines[i].match(TOP_LEVEL_DECL_RE);
      if (!m) continue;
      const [, kind, name] = m;
      if (!seen.has(name)) {
        seen.add(name);
        continue;
      }
      let n = 2;
      while (seen.has(`${name}_${n}`)) n++;
      const newName = `${name}_${n}`;
      seen.add(newName);
      lines[i] = lines[i].replace(`export ${kind} ${name}`, `export ${kind} ${newName}`);
      renamed++;
      console.warn(`  [dedupe] ${rel}: renamed duplicate \`${kind} ${name}\` → \`${newName}\``);
    }
    if (renamed > 0) writeFileSync(path, lines.join('\n'), 'utf8');
  }
}

function listGeneratedTs(dir: string, root = dir): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...listGeneratedTs(full, root));
    else if (entry.isFile() && entry.name.endsWith('.ts')) out.push(relative(root, full));
  }
  return out.sort();
}

const SKIP_EXPORTS = new Set(['MessageFns']);
const EXPORT_RE = /^export (?:interface|enum|class|type) ([A-Z][A-Za-z0-9_]*)/gm;

function listSchemaExports(filePath: string): string[] {
  const content = readFileSync(filePath, 'utf8');
  const seen = new Set<string>();
  const out: string[] = [];
  for (const m of content.matchAll(EXPORT_RE)) {
    const name = m[1];
    if (SKIP_EXPORTS.has(name)) continue;
    if (seen.has(name)) continue;
    seen.add(name);
    out.push(name);
  }
  return out;
}

type DisambigRules = Map<string, Map<string, string>>;

function loadDisambiguation(version: string): DisambigRules {
  const yamlPath = resolve(PKG_ROOT, 'disambiguation.yaml');
  const result: DisambigRules = new Map();
  if (!existsSync(yamlPath)) return result;
  const config = loadYaml(readFileSync(yamlPath, 'utf8')) as Record<string, Record<string, Record<string, string>>> | null;
  const versionRules = config?.[version];
  if (!versionRules) return result;
  for (const [file, renames] of Object.entries(versionRules)) {
    result.set(file.replace(/\\/g, '/'), new Map(Object.entries(renames ?? {})));
  }
  return result;
}

function buildBarrel(versionGenDir: string, importPrefix: string, rules: DisambigRules): string {
  const files = listGeneratedTs(versionGenDir);
  const fileExports = new Map<string, Array<{ orig: string; final: string }>>();
  const finalNameToLocations = new Map<string, string[]>();

  for (const f of files) {
    const fileKey = f.replace(/\\/g, '/');
    const fileRules = rules.get(fileKey);
    const items: Array<{ orig: string; final: string }> = [];
    for (const orig of listSchemaExports(resolve(versionGenDir, f))) {
      const final = fileRules?.get(orig) ?? orig;
      items.push({ orig, final });
      const arr = finalNameToLocations.get(final) ?? [];
      arr.push(`${fileKey}::${orig}`);
      finalNameToLocations.set(final, arr);
    }
    fileExports.set(fileKey, items);
  }

  const unresolved = [...finalNameToLocations.entries()].filter(([, locs]) => locs.length > 1);
  if (unresolved.length > 0) {
    const lines = ['Unresolved name collisions across modules:'];
    for (const [name, locs] of unresolved) {
      lines.push(`  ${name}:`);
      for (const loc of locs) lines.push(`    ${loc}`);
    }
    lines.push('Add entries to disambiguation.yaml to rename one of each pair.');
    throw new Error(lines.join('\n'));
  }

  const out: string[] = [];
  for (const [file, items] of fileExports) {
    if (items.length === 0) continue;
    const importPath = `${importPrefix}/${file.replace(/\.ts$/, '.js')}`;
    const list = items.map((it) => (it.orig === it.final ? it.orig : `${it.orig} as ${it.final}`));
    out.push(`export { ${list.join(', ')} } from '${importPath}';`);
  }
  return out.join('\n') + '\n';
}

function writeEntries(versions: string[]): void {
  for (const target of Object.keys(TARGETS) as Target[]) {
    const dir = resolve(PKG_ROOT, 'src', target);
    mkdirSync(dir, { recursive: true });
    for (const v of versions) {
      const entryPath = resolve(dir, `${v}.ts`);
      if (LEGACY_VERSIONS.has(v)) {
        writeFileSync(
          entryPath,
          `export * from '../generated/${target}/${v}/tiktok-schema.js';\n`,
          'utf8',
        );
      } else {
        const versionGenDir = resolve(GEN_DIR, target, v);
        const rules = loadDisambiguation(v);
        const barrel = buildBarrel(versionGenDir, `../generated/${target}/${v}`, rules);
        writeFileSync(entryPath, barrel, 'utf8');
      }
    }
  }
}

function main(): void {
  rmSync(TMP_DIR, { recursive: true, force: true });
  rmSync(GEN_DIR, { recursive: true, force: true });
  mkdirSync(GEN_DIR, { recursive: true });
  const pluginPath = resolvePlugin();

  const versions = readdirSync(PROTO_ROOT)
    .filter((name) => /^v\d+$/.test(name))
    .filter((name) => {
      try { return statSync(resolve(PROTO_ROOT, name)).isDirectory(); }
      catch { return false; }
    })
    .sort();
  if (versions.length === 0) throw new Error(`No version directories found under ${PROTO_ROOT}`);

  for (const version of versions) {
    for (const [target, env] of Object.entries(TARGETS) as [Target, string][]) {
      if (LEGACY_VERSIONS.has(version)) {
        generateLegacy({ version, target, env, pluginPath });
      } else {
        generateModern({ version, target, env, pluginPath });
      }
    }
  }

  writeEntries(versions);
  rmSync(TMP_DIR, { recursive: true, force: true });
  console.log('Done.');
}

main();
