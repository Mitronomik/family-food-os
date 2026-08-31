import assert from 'node:assert/strict';
import { access, readFile } from 'node:fs/promises';
import test from 'node:test';

const frontendRoot = new URL('../', import.meta.url);

async function read(relativePath) {
  return readFile(new URL(relativePath, frontendRoot), 'utf8');
}

test('current frontend metadata and shell use FamilyFoodOS identity', async () => {
  const [packageJson, packageLock, html, shell, restoreRuntime, restorePresentation] =
    await Promise.all([
      read('package.json'),
      read('package-lock.json'),
      read('index.html'),
      read('src/main.ts'),
      read('src/restore-control-runtime.ts'),
      read('src/restore-control-presentation.ts'),
    ]);
  const packageMetadata = JSON.parse(packageJson);
  const lockMetadata = JSON.parse(packageLock);

  assert.equal(packageMetadata.name, 'family-food-os-frontend');
  assert.equal(lockMetadata.name, 'family-food-os-frontend');
  assert.equal(lockMetadata.packages[''].name, packageMetadata.name);
  assert.match(html, /<title>FamilyFoodOS<\/title>/);
  assert.doesNotMatch(html, /mch-logo/i);

  assert.match(shell, /class="brand" aria-label="FamilyFoodOS"/);
  assert.match(shell, /class="brand-fallback">FF<\/span>/);
  assert.match(shell, /class="brand-name">FamilyFoodOS<\/p>/);
  assert.doesNotMatch(shell, /mch-logo|class="brand-fallback">МК<\/span>/i);

  for (const currentIdentitySurface of [html, shell, restoreRuntime, restorePresentation]) {
    assert.doesNotMatch(
      currentIdentitySurface,
      /cosmetic-workshop|cosmetic_workshop|CosmeticWorkshopOS|Мастерск(?:ая|ую|ой) косметолога/i,
    );
  }

  await assert.rejects(
    access(new URL('public/brand/mch-logo.png', frontendRoot)),
    (error) => error?.code === 'ENOENT',
  );
});

test('inherited business-domain routes remain present', async () => {
  const routes = await read('src/app-navigation-routes.ts');
  for (const route of [
    '/recipes',
    '/clients',
    '/client-recipes',
    '/orders',
    '/inventory',
    '/production',
    '/packaging-items',
    '/settings',
  ]) {
    assert.match(routes, new RegExp(`'${route.replaceAll('/', '\\/')}'`));
  }
});
