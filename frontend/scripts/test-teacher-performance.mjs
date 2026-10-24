import test from 'node:test';
import assert from 'node:assert/strict';
import {LipSyncClock,validateCues,sampleCues,estimateEnglish} from '../src/lib/lip-sync.ts';
import {gestureAt} from '../src/lib/teacher-performance.ts';

test('provider cues follow the audio clock, including gaps, pause, seek and end',()=>{
  const audio={currentTime:.15,paused:false,ended:false,readyState:4};
  const clock=new LipSyncClock();
  clock.startAudio(audio,[{start:.1,end:.3,viseme:'PP'},{start:.5,end:.8,viseme:'aa'}],'hello','en-US');
  assert.equal(clock.mode,'provider');assert.equal(clock.sample().PP,1);
  audio.currentTime=.4;assert.deepEqual(clock.sample(),{});
  audio.currentTime=.6;assert.equal(clock.sample().aa,1);
  audio.paused=true;assert.deepEqual(clock.sample(),{});
  audio.paused=false;audio.currentTime=.15;assert.equal(clock.sample().PP,1);
  audio.ended=true;assert.deepEqual(clock.sample(),{});
  clock.stop();assert.deepEqual(clock.sample(),{});assert.equal(clock.mode,'idle');
});
test('browser boundary resets estimation and pause does not advance its clock',()=>{
  const clock=new LipSyncClock();clock.startBrowser('make five',1,1000);
  assert.equal(clock.mode,'estimated');assert.ok(clock.sample(1030).PP>0);
  clock.boundary('make five',5,2000);assert.equal(clock.mode,'word');assert.ok(clock.sample(2030).FF>0);
  clock.pause(2030);assert.deepEqual(clock.sample(3000),{});clock.resume(4030);assert.ok(clock.sample(4030).FF>0);
  clock.stop();assert.deepEqual(clock.sample(4040),{});
});
test('invalid, overlapping, unsupported and unsorted cues fail explicitly',()=>{
  for(const cues of [[{start:0,end:1,viseme:'unknown'}],[{start:-1,end:1,viseme:'aa'}],[{start:0,end:1,viseme:'aa'},{start:.5,end:2,viseme:'PP'}],[{start:0,end:Infinity,viseme:'aa'}]])assert.throws(()=>validateCues(cues));
  assert.deepEqual(sampleCues([{start:0,end:1,viseme:'sil'}],.5),{});
});
test('English fallback includes distinct closures, vowels and maths digits',()=>{
  const cues=estimateEnglish('five, map 2.');assert.ok(cues.some(c=>c.viseme==='FF'));assert.ok(cues.some(c=>c.viseme==='PP'));assert.ok(cues.some(c=>c.viseme==='U'));assert.ok(cues.some(c=>c.viseme==='sil'));
});
test('Tamil provider cues work without applying English spelling guesses',()=>{
  const clock=new LipSyncClock();const audio={currentTime:.2,paused:false,ended:false,readyState:4};
  clock.startAudio(audio,[{start:0,end:1,viseme:'aa'}],'வணக்கம்','ta-IN');assert.equal(clock.sample().aa,1);
  clock.startAudio(audio,[],'வணக்கம்','ta-IN');assert.deepEqual(clock.sample(),{});
});
test('teaching gestures are finite, event-specific and allow quiet intervals',()=>{
  assert.equal(gestureAt('explaining',1,2),'count');assert.equal(gestureAt('explaining',5,2),'point');
  assert.equal(gestureAt('explaining',10,2),'open');assert.equal(gestureAt('explaining',30,2),'rest');
  assert.equal(gestureAt('correct',1),'celebrate');assert.equal(gestureAt('correct',4),'rest');
  assert.equal(gestureAt('incorrect',1),'reassure');assert.equal(gestureAt('paused',1),'rest');
  assert.equal(gestureAt('explaining',1,6),'open');
});
