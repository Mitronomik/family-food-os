import assert from 'node:assert/strict';
import { once } from 'node:events';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import test from 'node:test';

const frontendOrigin = 'http://127.0.0.1:5173';
const defaultProxyTarget = 'http://127.0.0.1:8000';
const devServerScript = fileURLToPath(
  new URL('../scripts/dev-server.mjs', import.meta.url),
);

async function startFrontend(extraEnvironment = {}) {
  const staticRoot = await mkdtemp(join(tmpdir(), 'family-food-frontend-test-'));
  await writeFile(join(staticRoot, 'index.html'), '<!doctype html><title>test</title>');
  const environment = { ...process.env };
  delete environment.FAMILY_FOOD_API_PROXY_TARGET;
  delete environment.COSMETIC_WORKSHOP_API_PROXY_TARGET;
  Object.assign(environment, extraEnvironment);

  const child = spawn(process.execPath, [devServerScript, staticRoot], {
    env: environment,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let stdout = '';
  let stderr = '';
  child.stdout.setEncoding('utf8');
  child.stderr.setEncoding('utf8');
  child.stdout.on('data', (chunk) => {
    stdout += chunk;
  });
  child.stderr.on('data', (chunk) => {
    stderr += chunk;
  });

  try {
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(
        () => reject(new Error(`frontend server did not start; stdout=${stdout}; stderr=${stderr}`)),
        5000,
      );
      const checkReady = () => {
        if (!stdout.includes('API proxy target:')) return;
        clearTimeout(timeout);
        resolve();
      };
      child.stdout.on('data', checkReady);
      child.once('error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });
      child.once('exit', (code, signal) => {
        if (stdout.includes('API proxy target:')) return;
        clearTimeout(timeout);
        reject(
          new Error(
            `frontend server exited before ready: code=${code} signal=${signal}; stderr=${stderr}`,
          ),
        );
      });
    });
  } catch (error) {
    if (child.exitCode === null && child.signalCode === null) child.kill('SIGTERM');
    await rm(staticRoot, { recursive: true, force: true });
    throw error;
  }

  return { child, staticRoot, stdout: () => stdout };
}

async function stopFrontend(frontend) {
  if (frontend.child.exitCode === null && frontend.child.signalCode === null) {
    const exited = once(frontend.child, 'exit');
    frontend.child.kill('SIGTERM');
    await exited;
  }
  await rm(frontend.staticRoot, { recursive: true, force: true });
}

async function listen(server) {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert.ok(address && typeof address === 'object');
  return `http://127.0.0.1:${address.port}`;
}

async function close(server) {
  await new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

test('FamilyFoodOS proxy environment boundary', async (t) => {
  await t.test('FAMILY_FOOD_API_PROXY_TARGET is honored', async () => {
    const backend = createServer((request, response) => {
      response.writeHead(200, { 'content-type': 'application/json' });
      response.end(JSON.stringify({ path: request.url, source: 'family-food-test' }));
    });
    const backendOrigin = await listen(backend);
    const frontend = await startFrontend({
      FAMILY_FOOD_API_PROXY_TARGET: backendOrigin,
      COSMETIC_WORKSHOP_API_PROXY_TARGET: 'http://127.0.0.1:65534',
    });
    try {
      assert.match(frontend.stdout(), new RegExp(`API proxy target: ${backendOrigin}`));
      const response = await fetch(`${frontendOrigin}/api/identity-check`);
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), {
        path: '/api/identity-check',
        source: 'family-food-test',
      });
    } finally {
      await stopFrontend(frontend);
      await close(backend);
    }
  });

  await t.test('old proxy variable alone is ignored', async () => {
    const frontend = await startFrontend({
      COSMETIC_WORKSHOP_API_PROXY_TARGET: 'http://127.0.0.1:65534',
    });
    try {
      assert.match(
        frontend.stdout(),
        new RegExp(`API proxy target: ${defaultProxyTarget}`),
      );
    } finally {
      await stopFrontend(frontend);
    }
  });

  await t.test('default proxy target is unchanged when the new variable is absent', async () => {
    const frontend = await startFrontend();
    try {
      assert.match(
        frontend.stdout(),
        new RegExp(`API proxy target: ${defaultProxyTarget}`),
      );
    } finally {
      await stopFrontend(frontend);
    }
  });
});
