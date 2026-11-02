import test from 'node:test';
import assert from 'node:assert/strict';
import { answerLines, wantsVisual } from '../src/lib/teaching-language.ts';

test('answers split into short written lines', () => {
  assert.deepEqual(answerLines('First we subtract 3. Then we divide by 2. So x is 4.'),
    ['First we subtract 3.', 'Then we divide by 2.', 'So x is 4.']);
  assert.deepEqual(answerLines('Does that make sense? Tell me!'), ['Does that make sense?', 'Tell me!']);
});

test('markdown and code never reach the board', () => {
  assert.deepEqual(answerLines('**Bold** and `code` go. # Title here.'), ['Bold and code go.', 'Title here.']);
  assert.deepEqual(answerLines('```2*x=8```\nNext line.'), ['Next line.']);
  assert.deepEqual(answerLines('[see this](http://x) now.'), ['see this now.']);
});

test('diagram and picture requests trigger a visual', () => {
  assert.equal(wantsVisual('Show me a diagram for this'), true);
  assert.equal(wantsVisual('Can you draw it with pizza?'), true);
  assert.equal(wantsVisual('Explain with a real world example'), true);
  assert.equal(wantsVisual('படம் போட்டு காட்டு'), true);
  assert.equal(wantsVisual('Explain it with pizza'), true);
  assert.equal(wantsVisual('Use chocolate'), true);
  assert.equal(wantsVisual('pizza'), true);
  assert.equal(wantsVisual('பீட்சாவில் சொல்லு'), true);
  assert.equal(wantsVisual('What is x?'), false);
  assert.equal(wantsVisual('Why do we subtract?'), false);
});

test('empty and Tamil answers behave', () => {
  assert.deepEqual(answerLines('   '), []);
  assert.deepEqual(answerLines('புரிகிறதா? சொல்லுங்கள்.'), ['புரிகிறதா?', 'சொல்லுங்கள்.']);
  assert.deepEqual(answerLines('No ending punctuation'), ['No ending punctuation']);
});
