import test from 'node:test';
import assert from 'node:assert/strict';
import { speechText } from '../src/lib/teaching-language.ts';

test('emoji and decoration become silence', () => {
  assert.equal(speechText('Well done! 🎉 ✅'), 'Well done!');
  assert.equal(speechText('✦ Step 2 ✦'), 'Step 2');
});

test('fractions speak as over', () => {
  assert.equal(speechText('Add 3/2 and 1/4.'), 'Add 3 over 2 and 1 over 4.');
});

test('equations speak naturally', () => {
  assert.equal(speechText('Solve 2x + 6 = 14.'), 'Solve 2x plus 6 equals 14.');
  assert.equal(speechText('x = -5'), 'x equals minus 5');
  assert.equal(speechText('3*2 and 50%'), '3 times 2 and 50 percent');
});

test('quotes and markdown vanish, words survive', () => {
  assert.equal(speechText('Say "hi" *loud*.'), 'Say hi loud .');
  assert.equal(speechText("don't worry"), "don't worry");
});

test('Tamil script survives with spoken fractions', () => {
  assert.equal(speechText('பாருங்கள் 3/2'), 'பாருங்கள் 3 over 2');
});
