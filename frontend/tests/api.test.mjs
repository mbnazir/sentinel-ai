import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test, { beforeEach } from 'node:test';
import ts from 'typescript';

const source = readFileSync(new URL('../src/api.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { api } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);

beforeEach(() => {
  const values = new Map([['sentinel_access_token', 'synthetic-token']]);
  globalThis.sessionStorage = {
    getItem: key => values.get(key) ?? null,
    removeItem: key => values.delete(key),
  };
  globalThis.window = new EventTarget();
});

test('expired token clears the session and requests a new login', async () => {
  let loginRequested = false;
  window.addEventListener('sentinel:unauthorized', () => { loginRequested = true; });
  globalThis.fetch = async () => new Response('{}', { status: 401 });
  await assert.rejects(api.caseDetail('synthetic-case'), /session expired/);
  assert.equal(sessionStorage.getItem('sentinel_access_token'), null);
  assert.equal(loginRequested, true);
});

test('proxy failure produces a retryable message without clearing the token', async () => {
  globalThis.fetch = async () => new Response('Bad Gateway', { status: 502 });
  await assert.rejects(api.caseDetail('synthetic-case'), /API unavailable.*502/);
  assert.equal(sessionStorage.getItem('sentinel_access_token'), 'synthetic-token');
});

test('network failures produce an actionable message', async () => {
  globalThis.fetch = async () => { throw new TypeError('Failed to fetch'); };
  await assert.rejects(api.caseDetail('synthetic-case'), /Cannot reach the API/);
});

test('case updates send authorization and retain their request body', async () => {
  globalThis.fetch = async (path, init) => {
    assert.equal(path, '/api/v1/investigations/synthetic-case');
    assert.equal(init.method, 'PATCH');
    assert.equal(init.headers.get('Authorization'), 'Bearer synthetic-token');
    assert.equal(init.headers.get('Content-Type'), 'application/json');
    assert.deepEqual(JSON.parse(init.body), { status: 'in_review' });
    return Response.json({ status: 'in_review' });
  };
  assert.deepEqual(await api.updateCase('synthetic-case', { status: 'in_review' }), {
    status: 'in_review',
  });
});
