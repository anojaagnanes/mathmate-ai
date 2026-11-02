import test from 'node:test';
import assert from 'node:assert/strict';
import { tamilStep } from '../src/lib/teaching-language.ts';

test('Mia Tamil covers orchestrator control phrases', () => {
  assert.match(tamilStep("Let's slow down."), /மெதுவாக/);
  assert.match(tamilStep('Here is another way to see it.'), /வேறு/);
  assert.match(tamilStep('Read the expression.'), /கோவை/);
});

test('Mia whiteboard contract is maths-only', async () => {
  const src = await import('node:fs').then(fs => fs.readFileSync(new URL('../src/components/mia-whiteboard.tsx', import.meta.url), 'utf8'));
  assert.doesNotMatch(src, /transcript|explanation|chat|reply/i);
  assert.match(src, /equation/);
  assert.match(src, /GeometryDiagram|diagram/);
});

test('Real-world visuals support board-only maths mode', async () => {
  const { readFileSync } = await import('node:fs');
  const visual = readFileSync(new URL('../src/components/real-world-visual.tsx', import.meta.url), 'utf8');
  assert.match(visual, /boardOnly/);
  const teaching = readFileSync(new URL('../src/components/question-teaching.tsx', import.meta.url), 'utf8');
  assert.match(teaching, /boardOnly/);
  assert.doesNotMatch(teaching, /example\.check/);
});

test('Crop editor is direct on-picture drag without sliders', async () => {
  const { readFileSync } = await import('node:fs');
  const editor = readFileSync(new URL('../src/components/handwriting-image-editor.tsx', import.meta.url), 'utf8');
  assert.match(editor, /data-crop-mode/);
  assert.doesNotMatch(editor, /Crop width/);
  assert.doesNotMatch(editor, /blue ink/);
  const upload = readFileSync(new URL('../src/components/handwriting.tsx', import.meta.url), 'utf8');
  assert.match(upload, /Crop & read page image/);
});

test('Mia panel wires language, voice, and follow-ups', async () => {
  const { readFileSync } = await import('node:fs');
  const panel = readFileSync(new URL('../src/components/mia-panel.tsx', import.meta.url), 'utf8');
  assert.match(panel, /useMiaSession/);
  assert.match(panel, /useMiaVoice/);
  assert.match(panel, /MiaControls/);
  const controls = readFileSync(new URL('../src/components/mia-controls.tsx', import.meta.url), 'utf8');
  assert.match(controls, /தமிழ்/);
  assert.match(controls, /Another method/);
  assert.match(controls, /Slow/);
});
