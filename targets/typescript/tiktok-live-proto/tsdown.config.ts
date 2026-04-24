import { defineConfig } from 'tsdown';

const outExtensions = () => ({ js: '.js', dts: '.d.ts' });

export default defineConfig([
  {
    entry: ['src/node/v1.ts', 'src/node/v2.ts'],
    outDir: 'dist/node',
    platform: 'node',
    format: ['esm'],
    dts: true,
    clean: true,
    outExtensions,
  },
  {
    entry: ['src/web/v1.ts', 'src/web/v2.ts'],
    outDir: 'dist/web',
    platform: 'browser',
    format: ['esm'],
    dts: true,
    clean: true,
    outExtensions,
  },
]);
