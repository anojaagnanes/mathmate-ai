'use client';
import { useEffect, useRef, useState } from 'react';
import {Paperclip, FileText, Crop, X, LoaderCircle, ArrowRight} from 'lucide-react';
import { recognizeLocally } from '@/lib/local-ocr';
import { api } from '@/lib/api';
import {composeQuestion, formatPages, reviewAfterEdit, withDeadline, type ExtractedPage} from '@/lib/question-workflow';
import type { Feedback, Solution } from '@/lib/types';
import { Button } from './ui/button';
import { HandwritingImageEditor } from './handwriting-image-editor';
import { ConstructionGuide, type ConstructionGuide as Guide } from './construction-guide';
import { Teacher } from './teacher';
import { MiaWhiteboard } from './mia-whiteboard';

type Reply = {
  route: 'solver' | 'interpretation' | 'image' | 'document' | 'working' | 'construction';
  feedback?: Feedback | null;
  document: {text: string; mode: string; pages: number; message: string; page_text?: ExtractedPage[]; unread_pages?: number[]} | null;
  status: 'solved' | 'unsupported' | 'review_required' | 'manual_required';
  proposed_math: string | null; assumptions: string[];
  suggested_variable?: string | null;
  suggested_input?: string | null;
  question_type?: string | null;
  message: string; question: string; solution: Solution | null;
  upload: {steps: string[]; mode: string} | null;
  guides?: Guide[];
};


export function QuestionInput({value, variable, onChange, onVariable, onSolution, onExploreTopics}: {
  onExploreTopics: () => void;
  value: string; variable: string; onChange: (text: string) => void;
  onVariable: (value: string) => void; onSolution: (solution: Solution) => void;
}) {
  const [editingImage, setEditingImage] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [reply, setReply] = useState<Reply | null>(null);
  const [reviewReply, setReviewReply] = useState<Reply | null>(null);
  const reviewField = useRef<HTMLTextAreaElement>(null);
  const resultPanel = useRef<HTMLDivElement>(null);
  const [sourceLines, setSourceLines] = useState<string[]>([]);
  const [sourcePages, setSourcePages] = useState<ExtractedPage[]>([]);
  const [intent, setIntent] = useState<'solve' | 'check_work'>('solve');
  const network = useRef<AbortController | null>(null);
  const [beforeReview, setBeforeReview] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [ocrStatus, setOcrStatus] = useState('');
  const ocr = useRef<AbortController | null>(null);
  const request = useRef(0);
  const picker = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!file || file.type === 'application/pdf') {setPreview(''); return;}
    const url = URL.createObjectURL(file); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => () => {request.current += 1; ocr.current?.abort(); network.current?.abort();}, []);
  function focusReview() {reviewField.current?.focus(); reviewField.current?.scrollIntoView({block: 'center', behavior: 'auto'});}
  useEffect(() => {if (reviewReply) focusReview();}, [reviewReply]);
  useEffect(() => {if (reply?.solution) {resultPanel.current?.focus(); resultPanel.current?.scrollIntoView({block: 'center', behavior: 'auto'});}}, [reply]);
  function reset(keepReview = false) {network.current?.abort(); ocr.current?.abort(); setOcrStatus(''); request.current += 1; setBusy(false); setError(''); setReply(null); setConfirmed(false); if (!keepReview) {setReviewReply(null);setSourceLines([]);setSourcePages([]);}}
  function changeFile(next: File | null) {
    if (next && !['image/jpeg','image/png','image/webp','application/pdf'].includes(next.type)) {setError('Choose a JPEG, PNG, WebP or PDF file.'); if(picker.current) picker.current.value=''; return;}
    if (next && next.size > 5 * 1024 * 1024) {setError('Choose a file no larger than 5 MB.'); if(picker.current) picker.current.value=''; return;}
    reset(!next && !!reviewReply); setEditingImage(false); onChange(value); setFile(null);
    if (picker.current) picker.current.value = '';
    setFile(next);
  }
  async function submit(text = value, image = file, target = variable, fromReview = false) {
    reset(fromReview); onChange(text);
    if (!text.trim() && !image) {setError('Enter a question or attach an image.'); return;}
    if (text.length > 4000) {setError('Keep the question within 4,000 characters. Select the part you want solved.'); return;}
    const id = ++request.current; setBusy(true);
    if (image) setOcrStatus('Reading attachment with the configured recognizer. Local vision can take up to three minutes on a CPU…');
    const body = new FormData(); body.append('question', text); body.append('variable', target); body.append('intent', intent);
    if (image) body.append('file', image);
    try {
      const controller = new AbortController(); network.current = controller;
      const result = await withDeadline(signal => api<Reply>('/math/question', {method: 'POST', body, signal}), controller.signal, image?.type.startsWith('image/') ? 210000 : 45000);
      if (!result || typeof result.message !== 'string' || !['solved','unsupported','review_required','manual_required'].includes(result.status) || (result.status === 'solved' && !result.solution && !result.guides?.length)) throw new Error('The server returned an incomplete result. Retry; your question and attachment are preserved.');
      if (id !== request.current) return;
      if (image && result.route === 'image' && result.status === 'manual_required') {
        const controller = new AbortController(); ocr.current = controller;
        try {
          const draft = await recognizeLocally(image, controller.signal, message => {if (id === request.current) setOcrStatus(message);});
          if (id !== request.current) return;
          if (draft.text) {
            result.status = 'review_required';
            result.upload = {steps: draft.text.split('\n'), mode: 'quick-read draft'};
            result.message = 'Quick-read draft — check every character. Printed English works best; handwriting, fractions and diagrams may be incorrect. For Tamil handwriting, typing the question gives the best result. This is not a verified answer.';
            if (draft.confidence < 75) result.message += ' Low reading confidence: compare the draft carefully with your image, or enter the question manually.';
          } else result.message += ' The quick reader also found no readable text. Try a clearer crop or type the question manually.';
        } catch (e) {
          if (id !== request.current) return;
          result.message += ' Quick reading could not finish: ' + (e as Error).message + ' Type the question manually below.';
        } finally {if (id === request.current) setOcrStatus('');}
      }
      if (image && result.route === 'document' && result.document && (result.document.mode === 'manual' || result.document.unread_pages?.length)) {
        const controller = new AbortController(); ocr.current = controller;
        try {
          const {recognizePdfLocally} = await import('@/lib/local-pdf-ocr');
          const draft = await recognizePdfLocally(image, controller.signal, message => {if (id === request.current) setOcrStatus(message);}, {
            embedded: result.document.page_text,
            recognize: async (data, signal, progress) => {
              progress('Reading page with the configured image recognizer…');
              const encoded=data.split(',')[1]; const bytes=Uint8Array.from(atob(encoded), char=>char.charCodeAt(0));
              const pageFile=new File([bytes], 'pdf-page.png', {type:'image/png'});
              const pageBody=new FormData(); pageBody.append('file', pageFile);
              try {
                const pageDraft=await withDeadline(inner=>api<{steps:string[];message:string}>('/handwriting/upload',{method:'POST',body:pageBody,signal:inner}),signal,185000);
                if(pageDraft.steps?.length) return {text:pageDraft.steps.join('\n'),confidence:null};
              } catch(e) {if(signal.aborted) throw e;}
              return recognizeLocally(pageFile,signal,progress);
            },
          });
          if (id !== request.current) return;
          result.document.text = draft.text;
          result.document.mode = 'page_ocr';
          result.document.page_text = draft.pages; result.document.unread_pages = draft.unread;
          result.status = draft.text ? 'review_required' : 'manual_required';
          result.message = draft.text ? 'PDF text and page-recognition draft. Review every symbol and page before submitting; recognition is not mathematical verification.' : 'No readable text was recognized. Type the question manually or upload a clearer page.';
          if (draft.unread.length) result.message += ` No text recognized on page(s) ${draft.unread.join(', ')}.`;
          if (draft.warnings.length) result.message += ' ' + draft.warnings.join(' ');
          if (draft.text && draft.confidence !== null && draft.confidence < 75) result.message += ' Low reading confidence: compare carefully with the original PDF.';
        } catch (e) {
          if (id !== request.current) return;
          result.message = 'PDF reading could not finish: ' + (e as Error).message + ' You can type the question manually below.';
        } finally {if (id === request.current) setOcrStatus('');}
      }
      if (id !== request.current) return;
      if (result.document?.page_text?.length) {
        setSourcePages(result.document.page_text);
        if (result.document.page_text.some(page => page.text.trim())) result.document.text = formatPages(result.document.page_text);
      }
      setReply(result);
      if (!result.solution && (result.route === 'image' || result.route === 'document' || result.proposed_math)) {
        onVariable(result.suggested_variable || '');
        setBeforeReview(text); setReviewReply(result);
        if (result.proposed_math) {
          // OCR choices belong to the transcription review, not this new model.
          // Restoring an old OCR line here would restart interpretation on Solve.
          setSourceLines([]); setSourcePages([]);
          onChange(result.proposed_math);
        }
        else {
          const extracted = result.document?.text || (result.upload?.steps || []).join('\n');
          onChange(composeQuestion(text, extracted));
          if (!extracted) setError('No usable text was recognized. Type the question above or try another attachment.');
        }
      }
      if (result.route === 'image' || result.route === 'document') {
        const extracted = result.document?.text || (result.upload?.steps || []).join('\n');
        setSourceLines(extracted.split(/\r?\n/).map(line => line.trim()).filter(line => !!line && !/^\[(Page \d+|No readable text.*)\]$/.test(line)));
      }
      if (result.solution) {setReviewReply(null); setFile(null); if (picker.current) picker.current.value = ''; onSolution(result.solution);}
      else if (fromReview) focusReview();
    } catch (e) {if (id === request.current) setError((e as Error).message);}
    finally {if (id === request.current) {setBusy(false); setOcrStatus('');}}
  }
  function editQuestion(text: string) {
    reset(!!reviewReply);
    if (reviewReply) setReviewReply(reviewAfterEdit(reviewReply, text));
    onChange(text);
  }
  function rejectDraft() {
    const original = beforeReview;
    reset(); setFile(null); setEditingImage(false);
    if (picker.current) picker.current.value = '';
    onChange(original); focusReview();
  }
  return <div className="question-composer unified-composer">
    <form className="composer-surface" aria-label="Maths question composer" aria-busy={busy} onSubmit={e => {
      e.preventDefault();
      if (busy || editingImage) return;
      if (reviewReply) {
        if (!confirmed) {setError('Review the question and confirm it before solving.'); return;}
        void submit(value, null, variable, true);
      } else void submit();
    }}>
      <label htmlFor="math-question" className="composer-label">Your maths question</label>
      <textarea ref={reviewField} id="math-question" rows={4} maxLength={4000} value={value} disabled={busy}
        placeholder="Type a maths question, or attach an image or PDF…"
        aria-describedby="composer-hint" onChange={e => editQuestion(e.target.value)}/>
      {file && <div className="composer-attachment">
        {preview ? <img src={preview} alt="Attached question thumbnail"/> : <FileText size={22} aria-hidden="true"/>}
        <span className="composer-filename" title={file.name}>{file.name}</span>
        {file.type.startsWith('image/') && <button className="composer-icon" type="button" title="Crop / clean handwriting" aria-label="Crop / clean handwriting" disabled={busy} aria-expanded={editingImage} onClick={() => setEditingImage(v => !v)}><Crop size={17}/></button>}
        <button className="composer-icon" type="button" title="Remove attachment" aria-label="Remove attachment" onClick={() => changeFile(null)}><X size={17}/></button>
      </div>}
      {busy && <div className="composer-status" role="status"><LoaderCircle className="composer-spinner" size={15}/><span>{ocrStatus ? 'Reading attachment… Local vision may take up to 3 minutes.' : 'Solving your question…'}</span><button type="button" onClick={() => reset(!!reviewReply)}>Cancel</button></div>}
      {error && <p className="composer-error" role="alert">{error}</p>}
      {reply?.route==='construction'&&reply.guides&&<ConstructionGuide guides={reply.guides}/>}
      {reply && !reply.solution && !reviewReply && reply.route!=='construction' && <div role="status"><p className="composer-error">{reply.message}</p>{reply.question_type && <p className="tiny">Detected: {reply.question_type}</p>}{reply.suggested_input && <button type="button" className="text-button" onClick={()=>editQuestion(reply.suggested_input!)}>Use suggested equation: {reply.suggested_input}</button>}</div>}
      {reviewReply && <div className="composer-review">
        {reply && !reply.solution && reply !== reviewReply && <p role="status" className="composer-error">{reply.message}</p>}
        <div className="composer-review-heading"><span>{reviewReply.proposed_math ? 'Check the interpreted model above' : 'Check the recognized text above'}</span><button type="button" disabled={busy} onClick={rejectDraft}>Reject {reviewReply.proposed_math ? 'model' : 'extraction'}</button></div>
        {reviewReply.proposed_math && <p className="tiny">Model to solve: <strong>{reviewReply.proposed_math}</strong>{reviewReply.suggested_variable ? ` · Solve for ${reviewReply.suggested_variable}` : ''}</p>}
        {reviewReply.question_type && <p className="tiny">Detected: {reviewReply.question_type}</p>}
        {reviewReply.suggested_input && !reviewReply.proposed_math && <button type="button" className="text-button" onClick={()=>editQuestion(reviewReply.suggested_input!)}>Use suggested equation: {reviewReply.suggested_input}</button>}
        {reviewReply.route === 'interpretation' && <p className="tiny">{reviewReply.message}</p>}
        {!reviewReply.proposed_math && sourceLines.length > 0 && <label className="composer-line-select">Choose what to solve (your original text is kept in details)
          <select aria-label="Use one extracted line" value="" disabled={busy} onChange={e => {if(e.target.value !== '') {const choice=e.target.value; editQuestion(choice === 'extracted' ? (sourcePages.length ? formatPages(sourcePages) : sourceLines.join('\n')) : choice === 'typed' ? beforeReview : choice.startsWith('page:') ? sourcePages[Number(choice.slice(5))].text : sourceLines[Number(choice)]); focusReview();}}}>
            <option value="">Keep the current text…</option>
            <option value="extracted">Use recognized text only</option>
            {beforeReview.trim() && <option value="typed">Use my original typed text only</option>}
            {sourcePages.length > 1 && sourcePages.map((page,index)=><option key={`page-${page.page}`} value={`page:${index}`} disabled={!page.text.trim()}>Page {page.page}{!page.text.trim() ? " (unread — enter manually)" : " only"}</option>)}
            {sourceLines.length > 1 && sourceLines.map((line, index) => <option key={index} value={index}>Line {index + 1}: {line}</option>)}
          </select>
        </label>}
        <details className="composer-details"><summary>{reviewReply.proposed_math ? 'Original question & assumptions' : 'Original text & recognition details'}</summary>
          {beforeReview && <><strong>Your text before recognition</strong><p className="composer-original">{beforeReview}</p></>}
          <p>{reviewReply.message}</p>
          {sourceLines.length > 0 && <p className="composer-original">{sourceLines.join('\n')}</p>}
          {reviewReply.assumptions.length > 0 && <ul>{reviewReply.assumptions.map(item => <li key={item}>{item}</li>)}</ul>}
        </details>
        <label className="composer-confirm"><input type="checkbox" disabled={busy} checked={confirmed} onChange={e => setConfirmed(e.target.checked)}/>{reviewReply.proposed_math ? 'I checked this model and its assumptions.' : 'I checked the text above. Solve this question.'}</label>
      </div>}
      {(value.includes('\n') || intent === 'check_work') && <label className="composer-line-select" style={{padding:'0 16px 12px'}}>Submission type
        <select aria-label="Submission type" disabled={busy} value={intent} onChange={e=>{reset(!!reviewReply);setIntent(e.target.value as 'solve'|'check_work');}}><option value="solve">Solve question / simultaneous equations</option><option value="check_work">Check my working (original equation first)</option></select>
      </label>}
      <div className="composer-toolbar">
        <input hidden ref={picker} type="file" aria-label="Choose maths image or PDF" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={e => {const next=e.target.files?.[0]; if(next) changeFile(next);}}/>
        <button type="button" className="composer-icon" aria-label={file ? 'Replace attachment' : 'Attach image or PDF'} title="JPEG, PNG, WebP or PDF · up to 5 MB" disabled={busy || editingImage} onClick={() => picker.current?.click()}><Paperclip size={20}/></button>
        <span id="composer-hint" className="composer-hint">{reviewReply ? 'Review, confirm, then Solve' : 'Image or PDF · up to 5 MB'}</span>
        <Button type="submit" className="composer-solve" disabled={busy || editingImage || (!value.trim() && !file) || (!!reviewReply && !confirmed)}>{busy ? <LoaderCircle size={16} className="composer-spinner"/> : <ArrowRight size={16}/>}Solve</Button>
      </div>
    </form>
    <div className="composer-links"><button type="button" className="text-button" onClick={onExploreTopics}>Explore Topics →</button>
      <details className="composer-options"><summary>Equation options</summary><label>Solve for<select value={variable} disabled={busy} onChange={e => {reset(!!reviewReply); onVariable(e.target.value);}}><option value="">Auto-detect</option>{['x','y','z','n','a','b','c','t','u','v','theta','alpha','beta'].map(v => <option key={v}>{v}</option>)}</select></label><p className="tiny">Images: 16–4096 pixels. PDFs: 1–5 pages. Confirm recognized text before solving.</p></details>
    </div>
    {editingImage && file && <HandwritingImageEditor file={file} onCancel={() => setEditingImage(false)} onApply={prepared => changeFile(prepared)}/>}
    {reviewReply && (reviewReply.route==='image'||reviewReply.route==='document') && <div className="review-classroom">
      <Teacher transcript={reviewReply.message} equation={sourceLines[0]||''} autoNarrate narrationLanguage="en"/>
      {sourceLines.length>0&&<MiaWhiteboard items={sourceLines.map(line=>({equation:line}))} step={sourceLines.length-1} playing={false} handwritten/>}
    </div>}
    {reply?.solution && <div ref={resultPanel} tabIndex={-1} className="success-box question-answer" role="status">
      {reply.feedback && <div className={reply.feedback.valid ? 'success-box' : 'info-box'}><strong>{reply.feedback.valid ? 'Correct transformations' : `Incorrect step ${reply.feedback.first_incorrect_step}`}</strong><p className="tiny">{reply.feedback.message}</p><p className="tiny">The answer below solves the original equation; it does not endorse an incorrect submitted step.</p></div>}
      <p className="tiny" style={{whiteSpace:'pre-wrap'}}>Question: {reply.question}</p>
      <h3>{reply.solution.verified ? 'Mathematical result' : 'Clarification needed'}</h3>
      <p>{reply.solution.solution !== null ? `${['unique', 'parametric'].includes(reply.solution.kind) && reply.solution.variable ? reply.solution.variable + ' = ' : ''}${reply.solution.solution}` : reply.solution.kind === 'none' ? 'No real solutions.' : reply.solution.kind === 'infinite' ? 'Infinitely many solutions.' : 'See the result details below.'}</p>
      <span className="tiny">{reply.solution.verified ? 'The submitted maths was checked. See the steps below.' : 'The solver needs more information; see details below.'}</span>
    </div>}
  </div>;
}
