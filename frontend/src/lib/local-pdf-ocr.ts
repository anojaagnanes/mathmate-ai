import { pdfPageImages } from './pdf-pages';
import { recognizeLocally } from './local-ocr';
import {formatPages, type ExtractedPage} from './question-workflow';

type Recognizer = (image: string, signal: AbortSignal, progress: (message: string) => void) => Promise<{text: string; confidence: number | null}>;

export async function recognizePdfLocally(file: File, signal: AbortSignal, progress: (message: string) => void,
  options: {embedded?: ExtractedPage[]; recognize?: Recognizer} = {}) {
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal.addEventListener('abort', cancel, {once: true});
  if (signal.aborted) cancel();
  let timedOut = false;
  const timer = setTimeout(() => {timedOut = true; controller.abort();}, 240000);
  const pages: ExtractedPage[] = (options.embedded || []).map(page => ({...page}));
  const warnings: string[] = [];
  let confidence: number | null = 100;
  try {
    progress('Reading scanned PDF pages…');
    const missing = options.embedded?.filter(page => !page.text.trim()).map(page => page.page);
    for await (const page of pdfPageImages(new Uint8Array(await file.arrayBuffer()), controller.signal, {pages: missing})) {
      if (!pages.length) for (let index=1; index<=page.pages; index++) pages.push({page:index,text:''});
      try {
        const draft = await (options.recognize || recognizeLocally)(page.image, controller.signal, message => progress(`Page ${page.page}/${page.pages} · ${message}`));
        confidence = confidence === null || draft.confidence === null ? null : Math.min(confidence, draft.confidence);
        const entry=pages.find(item => item.page===page.page)!;
        entry.text=draft.text;
        if (formatPages(pages).length > 4000) {entry.text=''; warnings.push(`Page ${page.page} exceeds the 4,000-character review limit. Upload it separately.`); break;}
      } catch(error) {
        if (controller.signal.aborted) throw error;
        warnings.push(`Page ${page.page}: ${(error as Error).message}`);
      }
    }
  } catch(error) {
    if (signal.aborted) throw new Error('Recognition cancelled.');
    if (timedOut) warnings.push('PDF recognition timed out. Unread pages are listed; upload them separately.');
    else if (pages.some(page => page.text)) warnings.push(`PDF processing stopped: ${(error as Error).message}`);
    else throw error;
  } finally {clearTimeout(timer); signal.removeEventListener('abort', cancel);}
  const unread=pages.filter(page => !page.text.trim()).map(page => page.page);
  return {text: pages.some(page => page.text.trim()) ? formatPages(pages) : '', pages, confidence, unread, warnings};
}
