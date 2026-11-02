import test from 'node:test';
import assert from 'node:assert/strict';
import {teachingTransition as transition,initialTeaching,equalGroupsExample,writingLayout,classroomTransition as session,initialClassroom,remainingNarration,teachingSteps,recordBoardProgress,rowNeedsScroll} from '../src/lib/question-teaching.ts';

test('classroom interruption preserves board through answering and resumes from its segment',()=>{
  let state=session(initialClassroom,{type:'resume'});
  assert.equal(state.phase,'RESUMING');state=session(state,{type:'started'});
  state=session(state,{type:'progress',value:.4});state=session(state,{type:'interrupt'});
  assert.equal(state.phase,'INTERRUPTED');
  assert.deepEqual(session(state,{type:'ended',count:5}),state);
  assert.deepEqual(session(state,{type:'progress',value:.9}),state);
  state=session(state,{type:'answering'});state=session(state,{type:'waiting'});
  assert.equal(state.progress,.4);assert.equal(state.step,0);
  state=session(state,{type:'resume'});assert.equal(state.segmentStart,.4);
  state=session(state,{type:'started'});state=session(state,{type:'progress',value:.5});
  assert.equal(state.progress,.7);
  const text='Subtract six from both sides to preserve equality.';
  assert.notEqual(remainingNarration(text,.4),text);
});
test('narration completion automatically advances every step and then finishes',()=>{
  let state=session(initialClassroom,{type:'resume'});
  for(let step=0;step<5;step++) {assert.equal(state.step,step);state=session(state,{type:'started'});state=session(state,{type:'ended',count:5});}
  assert.equal(state.phase,'COMPLETE');assert.equal(state.progress,1);
});

test('pause freezes progress; resume is monotonic; stop ignores late speech events',()=>{
  let state=transition(initialTeaching,{type:'play'});
  state=transition(state,{type:'progress',progress:.4});
  state=transition(state,{type:'pause'});
  assert.equal(transition(state,{type:'progress',progress:.9}).progress,.4);
  state=transition(state,{type:'resume'});
  assert.equal(transition(state,{type:'progress',progress:.1}).progress,.4);
  state=transition(state,{type:'stop'});
  assert.equal(transition(state,{type:'progress',progress:1}).progress,.4);
});
test('step change and replay reset the board; silent read explicitly reveals it',()=>{
  const old={step:2,progress:1,playing:true,paused:true};
  assert.deepEqual(transition(old,{type:'move',step:1}),{...initialTeaching,step:1});
  assert.deepEqual(transition(old,{type:'replay'}),{step:2,progress:0,playing:true,paused:false});
  assert.equal(transition(initialTeaching,{type:'reveal'}).progress,1);
});
test('analogy uses the current verified equation, not a canned notebook lesson',()=>{
  const solution={verified:true,kind:'unique',variable:'x',solution:'4'};
  assert.deepEqual(equalGroupsExample('2x + 6 = 14',solution)?.answer,4);
  const other=equalGroupsExample('3n + 4 = 40',{...solution,variable:'n',solution:'12'});
  assert.equal(other?.quantity,3); assert.equal(other?.answer,12); assert.match(other.narration,/40/);
  for(const [question,result] of [['3n+4=Tn',{...solution,kind:'parametric'}],['2x+6=14',{...solution,verified:false}],['2x+6=14',{...solution,solution:'5'}],['x^2=4',solution]]) assert.equal(equalGroupsExample(question,result),null);
});
test('hand cursor and text share bounded layout including Unicode and wrapped lines',()=>{
  for(const text of ['2x + 6 = 14','3n + 4 = t','√(9) = 3','x'.repeat(200)]) {
    assert.deepEqual(writingLayout(text,0).lines,[]);
    const final=writingLayout(text,1);assert.equal(final.lines.join(''),text);
    for(const progress of [0,.1,.5,.99,1]) {const p=writingLayout(text,progress);assert.ok(p.x>=0&&p.x<=1&&p.y>=0&&p.y<=1);}
  }
});

test('teaching begins with the submitted question, then every solving step',()=>{
 const original={equation:'2*x + 6 = 14',explanation:'Start with the original equation.'};
 const transform={equation:'2*x = 8',explanation:'Subtract 6 from both sides.'};
 assert.deepEqual(teachingSteps([original,transform]),[original,transform]);
 assert.deepEqual(teachingSteps([transform]),[transform]);
 assert.deepEqual(teachingSteps([original]),[original]);
 assert.deepEqual(teachingSteps([{...original,explanation:'Subtract zero to verify equivalence.'},transform]).length,2);
});

test('board retains all written steps across replay, previous and interruptions',()=>{
 let history=recordBoardProgress({},0,.5);
 history=recordBoardProgress(history,1,.4);
 assert.deepEqual(history,{0:1,1:.4});
 assert.deepEqual(recordBoardProgress(history,0,0),history);
 assert.deepEqual(recordBoardProgress(history,1,0),history);
 history=recordBoardProgress(history,3,1);
 assert.deepEqual(history,{0:1,1:1,2:1,3:1});
 assert.equal(Object.keys(recordBoardProgress({},0,0)).length,1);
});

test('lesson ends at the answer, omitting successful substitution verification',()=>{
 const answer={equation:'x = 4',explanation:'Simplify to isolate x.'};
 const check={equation:'11 = 11',explanation:'Substitute x = 4 into the original equation. Both sides agree.'};
 const input=[answer,check];
 assert.deepEqual(teachingSteps(input),[answer]);
 assert.equal(input.length,2);
 const substitution={equation:'y = 2*4',explanation:'Substitute x = 4 to solve for y.'};
 assert.deepEqual(teachingSteps([answer,substitution]),[answer,substitution]);
});
test('board auto-scroll fires only when the current row leaves the viewport',()=>{
 assert.equal(rowNeedsScroll(120,150,100,400),false);
 assert.equal(rowNeedsScroll(100,400,100,400),false);
 assert.equal(rowNeedsScroll(50,90,100,400),true);
 assert.equal(rowNeedsScroll(350,450,100,400),true);
});
