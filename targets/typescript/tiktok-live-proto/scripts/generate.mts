import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG_ROOT = resolve(__dirname, '..');
const PROTO_ROOT = resolve(PKG_ROOT, '../../../src');
const TMP_DIR = resolve(PKG_ROOT, 'tmp');
const GEN_DIR = resolve(PKG_ROOT, 'src/generated');

const HEADER = `syntax = "proto3";\npackage TikTok;\n\n`;

/** Map from an output directory name to the ts-proto `env=` value. */
const TARGETS = { node: 'node', web: 'browser' } as const;
type Target = keyof typeof TARGETS;

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
  if (!existsSync(srcDir)) throw new Error(`Missing proto source dir: ${srcDir}`);
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

function runTsProto(args: {
  version: string;
  target: Target;
  env: string;
  protoDir: string;
  protoFile: string;
  pluginPath: string;
}): void {
  const { version, target, env, protoDir, protoFile, pluginPath } = args;
  const outGen = resolve(GEN_DIR, target, version);
  mkdirSync(outGen, { recursive: true });

  const cmd = [
    'protoc',
    `--plugin=protoc-gen-ts_proto=${pluginPath}`,
    `--ts_proto_out=${outGen}`,
    `--ts_proto_opt=env=${env}`,
    '--ts_proto_opt=forceLong=string',
    '--ts_proto_opt=outputPartialMethods=false',
    '--ts_proto_opt=outputJsonMethods=false',
    '--ts_proto_opt=esModuleInterop=true',
    '--ts_proto_opt=snakeToCamel=true',
    '--ts_proto_opt=importSuffix=.js',
    `-I=${protoDir}`,
    protoFile,
  ].join(' ');

  console.log(`[${version}/${target}] protoc (env=${env}) ...`);
  execSync(cmd, { stdio: 'inherit' });

  const schemaFile = resolve(outGen, 'tiktok-schema.ts');
  if (!existsSync(schemaFile)) throw new Error(`ts-proto did not emit ${schemaFile}`);
}

function writeEntries(versions: string[]): void {
  for (const target of Object.keys(TARGETS) as Target[]) {
    const dir = resolve(PKG_ROOT, 'src', target);
    mkdirSync(dir, { recursive: true });
    for (const v of versions) {
      writeFileSync(
        resolve(dir, `${v}.ts`),
        `export * from '../generated/${target}/${v}/tiktok-schema.js';\n`,
        'utf8',
      );
    }
  }
}

function main(): void {
  rmSync(TMP_DIR, { recursive: true, force: true });
  rmSync(GEN_DIR, { recursive: true, force: true });
  mkdirSync(GEN_DIR, { recursive: true });
  const pluginPath = resolvePlugin();

  const versions = readdirSync(PROTO_ROOT, { withFileTypes: true })
    .filter((e) => e.isDirectory() && /^v\d+$/.test(e.name))
    .map((e) => e.name)
    .sort();
  if (versions.length === 0) throw new Error(`No version directories found under ${PROTO_ROOT}`);

  for (const version of versions) {
    const { outDir: protoDir, outFile: protoFile } = mergeVersion(version);
    for (const [target, env] of Object.entries(TARGETS) as [Target, string][]) {
      runTsProto({ version, target, env, protoDir, protoFile, pluginPath });
    }
  }

  writeEntries(versions);
  rmSync(TMP_DIR, { recursive: true, force: true });
  console.log('Done.');
}

main();
