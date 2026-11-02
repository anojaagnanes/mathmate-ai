export type ExtractedPage = {page: number; text: string};

/** An edited question must never keep approval language for an older model. */
export function reviewAfterEdit<T extends {proposed_math: string | null; assumptions: string[]; suggested_variable?: string | null; message: string}>(review: T, text: string): T {
  if (!review.proposed_math || text === review.proposed_math) return review;
  return {...review, proposed_math: null, assumptions: [], suggested_variable: null,
    message: 'You edited the interpreted model. Confirm the edited text, then Solve will check it again. Ambiguous notation may require a new interpretation review.'};
}

export function composeQuestion(typed: string, extracted: string): string {
  return [typed, extracted].filter(part => part.trim()).join('\n');
}

export function formatPages(pages: ExtractedPage[]): string {
  if (pages.length === 1) return pages[0].text;
  return pages.map(page => `[Page ${page.page}]\n${page.text || '[No readable text — review this page manually]'}`).join('\n\n');
}

/** Bounds even a stalled fetch/refresh chain, and propagates cancellation to fetch. */
export async function withDeadline<T>(work: (signal: AbortSignal) => Promise<T>, parent: AbortSignal, ms: number): Promise<T> {
  const controller = new AbortController();
  let rejectAbort: (error: Error) => void = () => {};
  const interrupted = new Promise<never>((_, reject) => {rejectAbort = reject;});
  const cancel = () => {controller.abort(); rejectAbort(new Error('Request cancelled. Your question is preserved.'));};
  parent.addEventListener('abort', cancel, {once: true});
  const timer = setTimeout(() => {
    controller.abort(); rejectAbort(new Error('Request timed out. Your question is preserved. Try a smaller crop or retry.'));
  }, ms);
  try {
    if (parent.aborted) {cancel(); return await interrupted;}
    return await Promise.race([work(controller.signal), interrupted]);
  } finally {clearTimeout(timer); parent.removeEventListener('abort', cancel);}
}
