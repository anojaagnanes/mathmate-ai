import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createWorker, PSM} from 'tesseract.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
test('local English+Tamil model extracts a printed equation without a remote OCR service', {timeout: 90000}, async () => {
  const worker = await createWorker('eng+tam', 1, {
    langPath: path.join(root, 'public/ocr/lang'), cacheMethod: 'none',
  });
  try {
    await worker.setParameters({tessedit_pageseg_mode: PSM.AUTO, preserve_interword_spaces: '1'});
    const {data} = await worker.recognize(path.join(root, '../backend/tests/fixtures/printed-equation.png'), {}, {text: true});
    assert.equal(data.text.replace(/\s/g, ''), '2x+3=11');
  } finally {await worker.terminate();}
});
test('local Tamil model reads printed Tamil words offline', {timeout: 90000}, async () => {
  const worker = await createWorker('eng+tam', 1, {
    langPath: path.join(root, 'public/ocr/lang'), cacheMethod: 'none',
  });
  try {
    await worker.setParameters({tessedit_pageseg_mode: PSM.AUTO, preserve_interword_spaces: '1'});
    const {data} = await worker.recognize(path.join(root, '../backend/tests/fixtures/printed-tamil.png'), {}, {text: true});
    // Single Latin letters may wobble in case; Tamil wording must be exact. Drafts are always student-reviewed.
    assert.equal(data.text.replace(/\s/g, '').toLowerCase(), 'x-னமதிப்பு');
  } finally {await worker.terminate();}
});
