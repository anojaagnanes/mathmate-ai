import {mkdir, cp, readdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'public/ocr');
await mkdir(path.join(output, 'core'), {recursive: true});
await mkdir(path.join(output, 'lang'), {recursive: true});
await cp(path.join(root, 'node_modules/tesseract.js/dist/worker.min.js'), path.join(output, 'worker.min.js'));
const core = path.join(root, 'node_modules/tesseract.js-core');
for (const name of await readdir(core)) {
  if (name.endsWith('.wasm') || name.endsWith('.wasm.js')) await cp(path.join(core, name), path.join(output, 'core', name));
}
await cp(path.join(root, 'node_modules/@tesseract.js-data/eng/4.0.0_best_int/eng.traineddata.gz'), path.join(output, 'lang/eng.traineddata.gz'));
await cp(path.join(root, 'node_modules/@tesseract.js-data/tam/4.0.0_best_int/tam.traineddata.gz'), path.join(output, 'lang/tam.traineddata.gz'));
await cp(path.join(root, 'node_modules/tesseract.js/LICENSE.md'), path.join(output, 'TESSERACT-JS-LICENSE'));
await cp(path.join(core, 'LICENSE'), path.join(output, 'TESSERACT-CORE-LICENSE'));
await cp(path.join(root, 'node_modules/@tesseract.js-data/eng/package.json'), path.join(output, 'ENGLISH-MODEL-PACKAGE.json'));
await cp(path.join(root, 'node_modules/@tesseract.js-data/tam/package.json'), path.join(output, 'TAMIL-MODEL-PACKAGE.json'));
console.log('Local English+Tamil OCR worker, core and language data prepared. No runtime CDN required.');

const pdf = path.join(root, 'node_modules/pdfjs-dist');
await mkdir(path.join(output, 'pdf'), {recursive: true});
await cp(path.join(pdf, 'legacy/build/pdf.worker.min.mjs'), path.join(output, 'pdf/pdf.worker.min.mjs'));
for (const directory of ['wasm', 'standard_fonts']) await cp(path.join(pdf, directory), path.join(output, 'pdf', directory), {recursive: true});
await cp(path.join(pdf, 'LICENSE'), path.join(output, 'pdf/LICENSE'));
console.log('Local PDF renderer assets prepared.');
