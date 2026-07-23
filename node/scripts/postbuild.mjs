#!/usr/bin/env node
import { readdirSync, renameSync, statSync, rmSync, existsSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { join, dirname } from 'node:path';

const cjsRoot = 'dist/cjs';
const distRoot = 'dist';

function moveTree(srcDir, destDir) {
  if (!existsSync(srcDir)) return;
  for (const entry of readdirSync(srcDir)) {
    const srcPath = join(srcDir, entry);
    const stat = statSync(srcPath);
    if (stat.isDirectory()) {
      const nestedDest = join(destDir, entry);
      mkdirSync(nestedDest, { recursive: true });
      moveTree(srcPath, nestedDest);
    } else if (entry.endsWith('.js')) {
      const renamed = entry.replace(/\.js$/, '.cjs');
      mkdirSync(destDir, { recursive: true });
      renameSync(srcPath, join(destDir, renamed));
    } else {
      mkdirSync(destDir, { recursive: true });
      renameSync(srcPath, join(destDir, entry));
    }
  }
}

if (existsSync(cjsRoot)) {
  moveTree(cjsRoot, distRoot);
  rmSync(cjsRoot, { recursive: true, force: true });
  writeFileSync(join(distRoot, 'package.cjs.json'), JSON.stringify({ type: 'commonjs' }, null, 2));
}
