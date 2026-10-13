const { test } = require('node:test');
const assert = require('node:assert/strict');
const { evaluate } = require('./app.js');
const base = { task_id:'T-1', target_identifier:'KEY-1', primary_metric:10, secondary_metric:2,
               status_descriptor:'NOMINAL', is_critical_flag:false };
test('nominal threshold evaluation', () => {
  const out = evaluate(base);
  assert.equal(out.overall_urgency, 'ROUTINE');
  assert.equal(out.total_alerts, 0);
  assert.equal(out.cryptographic_audit, false);
});
test('threshold and critical escalation match Python worker rules', () => {
  let out = evaluate({...base,primary_metric:30,secondary_metric:13,status_descriptor:'DISCORDANT'});
  assert.equal(out.total_alerts, 3);
  assert.equal(out.overall_urgency, 'ELEVATED_RISK');
  out = evaluate({...base,is_critical_flag:true});
  assert.equal(out.overall_urgency, 'CRITICAL_STAT_PANIC');
});
test('nonfinite and personal identifiers are rejected', () => {
  assert.throws(() => evaluate({...base,primary_metric:Infinity}), /finite/);
  assert.throws(() => evaluate({...base,task_id:'MRN-123456'}), /personal identifier/);
  assert.throws(() => evaluate({...base,secondary_metric:NaN}), /finite/);
});
