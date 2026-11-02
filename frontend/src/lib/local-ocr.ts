import type { Worker } from 'tesseract.js';

let running = false;

/** Best-effort English+Tamil OCR, not mathematical validation or diagram recognition. */
export async function recognizeLocally(file: File | string, signal: AbortSignal, progress: (message: string) => void) {
  if (signal.aborted) throw new Error('Recognition cancelled.');
  if (running) throw new Error('Local recognition is busy. Please try again shortly.');
  running = true;
  let worker: Worker | undefined;
  let pending: Promise<Worker> | undefined;
  let ended = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let cancel: () => void = () => {};
  const interrupted = new Promise<never>((_, reject) => {
    cancel = () => reject(new Error('Recognition cancelled.'));
    signal.addEventListener('abort', cancel, {once: true});
    timer = setTimeout(() => reject(new Error('Local recognition timed out. Try a smaller, clearer image or enter the text manually.')), 60000);
  });
  try {
    return await Promise.race([interrupted, (async () => {
      const {createWorker, PSM} = await import('tesseract.js');
      if (ended || signal.aborted) throw new Error('Recognition cancelled.');
      progress('Loading quick reader…');
      pending = createWorker('eng+tam', 1, {
        workerPath: '/ocr/worker.min.js', corePath: '/ocr/core', langPath: '/ocr/lang',
        workerBlobURL: false,
        logger: message => {if (!ended && !signal.aborted) progress(`${message.status} · ${Math.round(message.progress * 100)}%`);},
      });
      worker = await pending;
      if (ended || signal.aborted) throw new Error('Recognition cancelled.');
      await worker.setParameters({tessedit_pageseg_mode: PSM.AUTO, preserve_interword_spaces: '1'});
      const {data} = await worker.recognize(file, {}, {text: true});
      const text = data.text.trim();
      if (text.length > 4000) throw new Error('Too much text was recognized. Crop the image to one question and try again.');
      return {text, confidence: data.confidence};
    })()]);
  } finally {
    ended = true;
    clearTimeout(timer); signal.removeEventListener('abort', cancel);
    if (worker) await worker.terminate().catch(() => {});
    else if (pending) void pending.then(late => late.terminate()).catch(() => {});
    running = false;
  }
}
