import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createCanvas} from '@napi-rs/canvas';
import {createWorker, PSM} from 'tesseract.js';
import {fileURLToPath} from 'node:url';
import {pdfPageImages} from '../src/lib/pdf-pages.ts';

const fixture = name => readFile(new URL(`../../backend/tests/fixtures/${name}`, import.meta.url));
const options = {canvas: () => createCanvas(1, 1), workerSrc: new URL('../node_modules/pdfjs-dist/legacy/build/pdf.worker.min.mjs', import.meta.url).href};
const signal = () => new AbortController().signal;
test('scanned PDF renders locally and its printed equation is recognized', {timeout: 60000}, async () => {
  const worker = await createWorker('eng', 1, {langPath: fileURLToPath(new URL('../public/ocr/lang', import.meta.url)), cacheMethod:'none'});
  try {
    await worker.setParameters({tessedit_pageseg_mode: PSM.AUTO});
    let count = 0;
    for await (const page of pdfPageImages(new Uint8Array(await fixture('scanned-equation.pdf')), signal(), options)) {
      assert.equal(page.pages, 1);
      const {data} = await worker.recognize(page.image);
      assert.equal(data.text.replace(/\s/g,''), '2x+3=11'); count++;
    }
    assert.equal(count, 1);
  } finally {await worker.terminate();}
});
test('PDF renderer rejects invalid, oversized and excessive-page documents', async () => {
  for (const [bytes, message] of [
    [new TextEncoder().encode('not a pdf'), /valid PDF/],
    [new Uint8Array(5*1024*1024+1), /5 MB/],
    [new Uint8Array(await fixture('scanned-six-pages.pdf')), /1–5 pages/],
  ]) {
    await assert.rejects(async () => {for await (const page of pdfPageImages(bytes, signal(), options)) void page;}, message);
  }
});
test('PDF renderer honors cancellation before loading and between pages', async () => {
  const controller = new AbortController(); controller.abort();
  await assert.rejects(async () => {for await (const page of pdfPageImages(new Uint8Array(await fixture('scanned-equation.pdf')), controller.signal, options)) void page;}, /cancelled/);
  const mid = new AbortController();
  const pages = pdfPageImages(new Uint8Array(await fixture('scanned-equation.pdf')), mid.signal, options);
  assert.equal((await pages.next()).done, false);
  mid.abort();
  await pages.return(); // Releases the document and canvas even when the consumer stops.
});

test('embedded pages can be skipped without rendering them again', async () => {
  let rendered=0;
  for await (const page of pdfPageImages(new Uint8Array(await fixture('scanned-equation.pdf')), signal(), {...options,pages:[]})) rendered++;
  assert.equal(rendered,0);
  for await (const page of pdfPageImages(new Uint8Array(await fixture('scanned-equation.pdf')), signal(), {...options,pages:[1]})) {
    assert.equal(page.page,1); rendered++;
  }
  assert.equal(rendered,1);
});
