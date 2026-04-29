import { defineConfig } from 'tsdown';

const outExtensions = () => ({ js: '.js', dts: '.d.ts' });

export default defineConfig({
  entry: ['src/v1.ts', 'src/v2.ts'],
  outDir: 'dist',
  platform: 'neutral',
  format: ['esm'],
  dts: true,
  clean: true,
  outExtensions,
});
