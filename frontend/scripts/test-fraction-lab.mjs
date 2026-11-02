import test from 'node:test';
import assert from 'node:assert/strict';
import { vulgarToAscii, parseAddends, gcd, lcm, labModel, vulgar } from '../src/lib/fractions.ts';

test('unicode vulgar fractions become ascii', () => {
  assert.equal(vulgarToAscii('½ + ⅓ = ⅖'), '1/2 + 1/3 = 2/5');
});

test('addends parse from student attempts', () => {
  assert.deepEqual(parseAddends('1/2 + 1/3 = 2/5'), [[1, 2], [1, 3]]);
  assert.deepEqual(parseAddends('½ + ⅓ = ⅖'), [[1, 2], [1, 3]]);
  assert.deepEqual(parseAddends('1/2 + 1/4 = '), [[1, 2], [1, 4]]);
  assert.equal(parseAddends('2x + 3 = 11'), null);
  assert.equal(parseAddends('just one 1/2 here'), null);
});

test('lab model discovers the common denominator', () => {
  assert.deepEqual(labModel([1, 2], [1, 3]), {lcm: 6, needA: 3, needB: 2, sumN: 5, sumD: 6});
  assert.deepEqual(labModel([1, 2], [1, 4]), {lcm: 4, needA: 2, needB: 1, sumN: 3, sumD: 4});
  assert.deepEqual(labModel([1, 4], [1, 4]), {lcm: 4, needA: 1, needB: 1, sumN: 1, sumD: 2});
});

test('helpers stay exact', () => {
  assert.equal(gcd(10, 15), 5);
  assert.equal(lcm(4, 6), 12);
  assert.equal(vulgar(1, 2), '½');
  assert.equal(vulgar(5, 6), '⅚');
  assert.equal(vulgar(5, 12), '5/12');
});
