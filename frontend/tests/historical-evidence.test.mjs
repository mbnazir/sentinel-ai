import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import test from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';

const source = readFileSync(new URL('../src/HistoricalDecisionEvidence.tsx', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.ReactJSX,
  },
}).outputText;
const exports = {};
new Function('require', 'exports', compiled)(createRequire(import.meta.url), exports);
const render = finding => renderToStaticMarkup(
  React.createElement(exports.HistoricalDecisionEvidence, { finding }),
);
const finding = {
  rule_id: 'QF-001', source_session_id: 'synthetic-session', evidence_json: {
    metadata: {
      earlier: { status_id: 2, supervisor_status_id: 4, ingestion_run_id: 'earlier-run', snapshot_id: 'old-snapshot', content_hash: 'old-hash' },
      later: { status_id: 2, supervisor_status_id: 5, ingestion_run_id: 'later-run', snapshot_id: 'new-snapshot', content_hash: 'new-hash' },
      editor_identity: 'UNVERIFIED', payroll_finalization: 'UNVERIFIED', financial_impact: 'UNVERIFIED',
    },
    comparison_context: {
      eligibility_mode: 'OBSERVED_RECORDS_ONLY', override_actor: 'reviewer',
      override_reason: 'Review observed sessions only',
      reconciliation_limitations: ['Baseline is incomplete'],
      reconciliation_statuses: { 'earlier-run': 'INCOMPLETE/INCOMPLETE', 'later-run': 'COMPLETE/RECONCILED' },
    },
  },
};

test('renders manager decisions, source references and baseline limitations', () => {
  const html = render(finding);
  for (const value of ['Accepted by Manager (4)', 'Rejected by Manager (5)',
    'old-snapshot', 'new-snapshot', 'old-hash', 'new-hash', 'OBSERVED_RECORDS_ONLY',
    'Baseline is incomplete', 'UNVERIFIED', 'reviewer', 'Session status (separate field)']) {
    assert.ok(html.includes(value), value);
  }
});

test('does not infer manager decisions from session status', () => {
  const value = structuredClone(finding);
  value.evidence_json.metadata.earlier = { status_id: 4 };
  value.evidence_json.metadata.later = { status_id: 5 };
  const html = render(value);
  assert.ok(!html.includes('Accepted by Manager (4)'));
  assert.ok(!html.includes('Rejected by Manager (5)'));
  assert.ok(html.includes('Not recorded'));
});

test('handles missing metadata and leaves other rules alone', () => {
  assert.ok(render({ rule_id: 'QF-001' }).includes('Not recorded'));
  assert.equal(render({ rule_id: 'OTHER' }), '');
});

test('source strings are escaped as text', () => {
  const value = structuredClone(finding);
  value.evidence_json.comparison_context.override_reason = '<script>alert(1)</script>';
  const html = render(value);
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;'));
});
