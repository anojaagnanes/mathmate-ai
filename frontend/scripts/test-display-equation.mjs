import test from 'node:test';
import assert from 'node:assert/strict';
import { displayEquation } from '../src/lib/teaching-language.ts';

test('solver star notation becomes plain maths', () => {
  assert.equal(displayEquation('2*x + 3 = 11'), '2x + 3 = 11');
  assert.equal(displayEquation('2*x = 8'), '2x = 8');
  assert.equal(displayEquation('(2*x)/(2) = (8)/(2)'), '(2x)/(2) = (8)/(2)');
  assert.equal(displayEquation('x = 4'), 'x = 4');
});

test('powers become superscripts', () => {
  assert.equal(displayEquation('x**2 - 5*x + 6 = 0'), 'x² - 5x + 6 = 0');
  assert.equal(displayEquation('D = (-5)^2 - 4*(1)*(6) = 1'), 'D = (-5)² - 4(1)(6) = 1');
  assert.equal(displayEquation('(x - 3)*(x - 2) = 0'), '(x - 3)(x - 2) = 0');
});

test('roots and digit multiplication stay readable', () => {
  assert.equal(displayEquation('x = (-(-5) ± sqrt(1)) / (2*(1))'), 'x = (-(-5) ± √(1)) / (2(1))');
  assert.equal(displayEquation('2*3 = 6'), '2×3 = 6');
  assert.equal(displayEquation('1/2 + 1/4'), '1/2 + 1/4');
  assert.equal(displayEquation('11 = 11'), '11 = 11');
});
