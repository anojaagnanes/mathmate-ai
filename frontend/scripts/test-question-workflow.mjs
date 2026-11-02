import test from 'node:test';
import assert from 'node:assert/strict';
import {composeQuestion, formatPages, reviewAfterEdit, withDeadline} from '../src/lib/question-workflow.ts';

test('restoring OCR notation invalidates the previous interpreted model', () => {
  const model={proposed_math:'3n + 4=t',suggested_variable:'n',assumptions:['t is the nth term'],message:'Review model',question:'3n + 4 = Tn'};
  assert.equal(reviewAfterEdit(model,'3n + 4=t'),model);
  const edited=reviewAfterEdit(model,'3n + 4 = Tn');
  assert.equal(edited.proposed_math,null);
  assert.deepEqual(edited.assumptions,[]);
  assert.equal(edited.suggested_variable,null);
  assert.equal(edited.question,model.question);
  assert.match(edited.message,/edited/);
  assert.equal(reviewAfterEdit(model,'3n + 4 = 40').proposed_math,null);
});

test('combined input preserves typed text, notation and line breaks', () => {
  assert.equal(composeQuestion('Please check\nmy work', '3n + 4 = 40\nn = 12'), 'Please check\nmy work\n3n + 4 = 40\nn = 12');
  assert.equal(composeQuestion('', 'x² = 4'), 'x² = 4');
});
test('PDF boundaries and unread pages remain explicit', () => {
  assert.equal(formatPages([{page:1,text:'x=4'}]), 'x=4');
  const result = formatPages([{page:1,text:'x=4'}, {page:2,text:''}, {page:3,text:'y=5'}]);
  assert.match(result, /\[Page 2\]\n\[No readable text/);
  assert.ok(result.indexOf('x=4') < result.indexOf('y=5'));
});
test('stalled requests time out and abort their fetch', async () => {
  let signal;
  await assert.rejects(withDeadline(s => {signal=s; return new Promise(()=>{});}, new AbortController().signal, 10), /timed out/);
  assert.equal(signal.aborted,true);
});
test('cancellation ends even an unresponsive operation', async () => {
  const controller=new AbortController();
  const result=withDeadline(()=>new Promise(()=>{}),controller.signal,1000);
  controller.abort();
  await assert.rejects(result,/cancelled/);
});
test('server errors remain actionable and retry can succeed', async () => {
  await assert.rejects(withDeadline(async()=>{throw new Error('HTTP 500');},new AbortController().signal,1000),/HTTP 500/);
  assert.deepEqual(await withDeadline(async()=>({answer:4}),new AbortController().signal,1000),{answer:4});
});
