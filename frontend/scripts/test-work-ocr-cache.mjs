import test from 'node:test';
import assert from 'node:assert/strict';
import {WorkOcrCache} from '../src/lib/work-ocr-cache.ts';
test('exact crop cache preserves review status and never reuses a different image',async()=>{
 const cache=new WorkOcrCache();const a=await cache.key(new Blob(['one crop']));const b=await cache.key(new Blob(['changed crop']));
 assert.notEqual(a,b);cache.set(a,'3n+4=40');assert.equal(cache.get(b),undefined);assert.equal(cache.get(a).confirmed,false);
 cache.set(a,'3n + 4 = 40',true);assert.equal(cache.get(a).confirmed,true);
 assert.equal(new WorkOcrCache().get(a),undefined);
});
test('empty OCR is not cached and entries are bounded',()=>{
 const cache=new WorkOcrCache();cache.set('empty',' ');assert.equal(cache.get('empty'),undefined);
 for(let i=0;i<6;i++)cache.set(String(i),'x=4');assert.equal(cache.get('0'),undefined);assert.equal(cache.get('5').text,'x=4');
});
