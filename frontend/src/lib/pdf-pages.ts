/** Render bounded PDFs to page images. No PDF scripts, links or attachments are executed. */
export async function* pdfPageImages(
  bytes: Uint8Array, signal: AbortSignal,
  options: {canvas?: () => HTMLCanvasElement; workerSrc?: string; pages?: number[]} = {},
) {
  if (signal.aborted) throw new Error('Recognition cancelled.');
  if (bytes.length > 5 * 1024 * 1024) throw new Error('Choose a PDF no larger than 5 MB.');
  if (new TextDecoder().decode(bytes.subarray(0, 5)) !== '%PDF-') throw new Error('The file is not a valid PDF.');
  const pdfjs = await import('pdfjs-dist/legacy/build/pdf.mjs');
  if (signal.aborted) throw new Error('Recognition cancelled.');
  pdfjs.GlobalWorkerOptions.workerSrc = options.workerSrc || '/ocr/pdf/pdf.worker.min.mjs';
  const loading = pdfjs.getDocument({data: bytes, stopAtErrors: true, maxImageSize: 16_777_216,
    canvasMaxAreaInBytes: 16_777_216, useWorkerFetch: false,
    wasmUrl: '/ocr/pdf/wasm/', standardFontDataUrl: '/ocr/pdf/standard_fonts/',
  });
  let rendering: {cancel: () => void} | undefined;
  const cancel = () => {rendering?.cancel(); void loading.destroy().catch(() => {});};
  signal.addEventListener('abort', cancel, {once: true});
  try {
    if (signal.aborted) {cancel(); throw new Error('Recognition cancelled.');}
    const pdf = await loading.promise;
    if (pdf.numPages < 1 || pdf.numPages > 5) throw new Error('Choose a PDF with 1–5 pages.');
    for (let index = 1; index <= pdf.numPages; index++) {
      if (options.pages && !options.pages.includes(index)) continue;
      if (signal.aborted) throw new Error('Recognition cancelled.');
      const page = await pdf.getPage(index);
      const original = page.getViewport({scale: 1});
      if (!Number.isFinite(original.width * original.height) || original.width <= 0 || original.height <= 0) throw new Error('Invalid PDF page dimensions.');
      const scale = Math.min(2, 2400 / Math.max(original.width, original.height), Math.sqrt(4_000_000 / (original.width * original.height)));
      const viewport = page.getViewport({scale});
      const canvas = options.canvas?.() || document.createElement('canvas');
      try {
        canvas.width = Math.max(1, Math.floor(viewport.width)); canvas.height = Math.max(1, Math.floor(viewport.height));
        const task = page.render({canvas, viewport, background: 'rgb(255,255,255)'});
        rendering = task; await task.promise; rendering = undefined;
        if (signal.aborted) throw new Error('Recognition cancelled.');
        yield {image: canvas.toDataURL('image/png'), page: index, pages: pdf.numPages};
      } finally {canvas.width = 0; canvas.height = 0; page.cleanup();}
    }
  } finally {signal.removeEventListener('abort', cancel); await loading.destroy().catch(() => {});}
}
