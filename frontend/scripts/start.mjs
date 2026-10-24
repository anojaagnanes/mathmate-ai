import { cp, mkdir } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
// Next standalone output excludes static assets; copy them without deleting existing files.
await mkdir(path.join(root, '.next/standalone/.next'), {recursive: true});
await cp(path.join(root, '.next/static'), path.join(root, '.next/standalone/.next/static'), {recursive: true});
await cp(path.join(root, 'public'), path.join(root, '.next/standalone/public'), {recursive: true});
const server = spawn(process.execPath, ['.next/standalone/server.js'], {
  cwd: root,
  stdio: 'inherit',
  env: {...process.env, HOSTNAME: process.env.HOSTNAME || '127.0.0.1', PORT: process.env.PORT || '3000'},
});
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => server.kill(signal));
server.on('exit', code => {process.exitCode = code ?? 0;});
