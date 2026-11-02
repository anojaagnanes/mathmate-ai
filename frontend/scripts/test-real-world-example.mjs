import test from 'node:test';
import assert from 'node:assert/strict';
import {realWorldExample} from '../src/lib/real-world-example.ts';
import {classroomTransition,initialClassroom} from '../src/lib/question-teaching.ts';
const result=(solution,extra={})=>({verified:true,kind:'expression',solution,variable:null,steps:[],...extra});
test('shopping checks the current solution and produces equivalent steps',()=>{
 const s=result('4',{kind:'unique',variable:'x'}),e=realWorldExample('2x + 6 = 14',s);
 assert.deepEqual(e.values,[2,6,14,4]);assert.equal(e.steps.at(-1).equation,'x = 8 / 2 = 4');
 assert.equal(realWorldExample('2x + 6 = 14',{...s,solution:'5'}),null);
 assert.deepEqual(realWorldExample('3n+4=40',result('12',{kind:'unique',variable:'n'})).values,[3,4,40,12]);
});
test('fraction uses equal, bounded portions and agrees with the verified result',()=>{
 assert.deepEqual(realWorldExample('3/4',result('3/4')).values,[3,4]);
 assert.equal(realWorldExample('3/4',result('1/4')),null);
 assert.equal(realWorldExample('3/0',result('0')),null);
 assert.equal(realWorldExample('3/1000000',result('0.000003')),null);
});
test('discount distinguishes savings from final price',()=>{
 const e=realWorldExample('20/100*1500',result('300'));
 assert.deepEqual(e.values,[20,1500,300]);assert.match(e.steps[1].explanation,/1200.00/);
 assert.equal(realWorldExample('120/100*1500',result('1800')),null);
});
test('room dimensions and area must agree',()=>{
 assert.deepEqual(realWorldExample('rectangle_area(6,4)',result('24')).values,[6,4]);
 assert.equal(realWorldExample('rectangle_area(6,4)',result('10')),null);
});
test('journey graph only accepts the matching verified linear function',()=>{
 assert.deepEqual(realWorldExample('y=3*x',result('3*x',{kind:'parametric',variable:'y'})).values,[3]);
 assert.equal(realWorldExample('y=3*x',result('4*x',{kind:'parametric',variable:'y'})),null);
});
test('Tamil preserves mathematical content and local attribution',()=>{
 const e=realWorldExample('2x+6=14',result('4',{kind:'unique',variable:'x'}),'ta');
 assert.match(e.steps[0].explanation,/[\u0b80-\u0bff]/);assert.equal(e.steps[0].equation,'2x + 6 = 14');assert.equal(e.source,'local');
});
test('unsupported, missing and unverified results safely decline',()=>{
 assert.equal(realWorldExample('sin(x)',result('0')),null);
 assert.equal(realWorldExample('3/4',result('3/4',{verified:false})),null);
 assert.equal(realWorldExample('3/4',result('not a number')),null);
});
test('separate example playback does not change the saved lesson',()=>{
 const lesson={...initialClassroom,step:2,progress:.4,phase:'INTERRUPTED'};
 let example=classroomTransition(initialClassroom,{type:'resume'});
 example=classroomTransition(example,{type:'progress',value:.3});
 example=classroomTransition(example,{type:'interrupt'});
 example=classroomTransition(example,{type:'answering'});
 example=classroomTransition(example,{type:'waiting'});
 assert.equal(example.progress,.3);
 example=classroomTransition(example,{type:'resume'});assert.equal(example.segmentStart,.3);
 example=classroomTransition(example,{type:'replay'});assert.equal(example.progress,0);
 assert.equal(lesson.step,2);assert.equal(classroomTransition(lesson,{type:'resume'}).segmentStart,.4);
});
