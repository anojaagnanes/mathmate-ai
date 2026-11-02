'use client';
import {useEffect,useRef,useState} from 'react';
import dynamic from 'next/dynamic';
import {LipSyncClock} from '@/lib/lip-sync';


import {WorkOcrCache} from '@/lib/work-ocr-cache';
import {withDeadline} from '@/lib/question-workflow';

const WorkAvatar=dynamic(()=>import('./teacher-avatar'),{ssr:false,loading:()=> <p>Loading Mia…</p>});
function WaitingMia({text,busy}:{text:string;busy:boolean}){const speech=useRef(new LipSyncClock());return <section className="classroom-card" aria-label="Mia is here to help"><header className="classroom-lesson-header"><h2>Mia is here with you</h2><p>{busy?'Reading your work. Your answer will be checked after you review the text.':'Review your text, then submit it so we can check each step together.'}</p></header><div className="classroom-stage"><div className="classroom-whiteboard"><span className="eyebrow">{text?'YOUR WORK — NOT YET VERIFIED':'READY FOR YOUR WORK'}</span><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',fontFamily:'inherit'}}>{text||'Upload your work or type your equation and steps. Mia will explain the verified correction here.'}</pre></div><WorkAvatar state="idle" speech={speech.current} syncMode="idle" writingBoard={{text:"",progress:0,screen:{x:.65,y:.4},active:false,paused:true}}/></div></section>;}
import {Upload,ShieldCheck,BookOpen,CheckCircle2,AlertCircle,ArrowRight,Crop,FileText,Trash2} from 'lucide-react';
import {useQueryClient} from '@tanstack/react-query';
import {recognizeLocally} from '@/lib/local-ocr';
import {recognizePdfLocally} from '@/lib/local-pdf-ocr';
import {api,post} from '@/lib/api';
import type {Solution} from '@/lib/types';
import {Button} from './ui/button';
import {HandwritingImageEditor} from './handwriting-image-editor';
import {QuestionTeaching} from './question-teaching';
import {MathText} from './math';
import {FractionLab} from './fraction-lab';

type Review={id?:string;status:string;message:string;normalization_required:boolean;first_incorrect_step:number|null;verified_correction:string|null;corrected:Solution|null;practice:{equation:string;variable:string|null;hint:string;kind?:string}|null;lines:{number:number;original:string;normalized:string;status:string;reason:string}[]};
type Guidance={mode:string;guidance:{misconception:string;explanation:string;strategy:string;encouragement:string}};
const labels:Record<string,string>={starting_equation:'Starting equation',equivalent:'Equivalent step',correct:'Correct',incorrect:'First error',dependent:'Depends on earlier error',uncertain:'Review notation',unverified:'Not verified'};
export function Handwriting(){
  const client=useQueryClient(),mounted=useRef(true),controller=useRef<AbortController|null>(null);
  const ocrCache=useRef(new WorkOcrCache()),imageKey=useRef('');
  const [metaVision,setMetaVision]=useState(false);
  const [style,setStyle]=useState('simple'),[showLab,setShowLab]=useState(false);
  const [memory,setMemory]=useState<{patterns:{category:string;count:number}[];revision:string|null}|null>(null);

  useEffect(()=>{api<{configured:boolean}>('/tutor/status').then(s=>{if(mounted.current)setMetaVision(s.configured);}).catch(()=>{});},[]);
  const [prepared,setPrepared]=useState<File|null>(null);
  const [file,setFile]=useState<File|null>(null),[cropOpen,setCropOpen]=useState(false),[preview,setPreview]=useState('');
  const [pageImage,setPageImage]=useState<{page:number;file:File}|null>(null);
  const [steps,setSteps]=useState(''),[raw,setRaw]=useState(''),[confirmed,setConfirmed]=useState(false),[busy,setBusy]=useState(false),[status,setStatus]=useState(''),[error,setError]=useState('');
  const [result,setResult]=useState<Review|null>(null),[guidance,setGuidance]=useState<Guidance|null>(null),[language,setLanguage]=useState('English'),[teachingBusy,setTeachingBusy]=useState(false);
  useEffect(()=>{api<typeof memory>('/work/memory').then(setMemory).catch(()=>{});},[result?.id]);
  const [pages,setPages]=useState<{page:number;text:string}[]>([]),[page,setPage]=useState(1),[answer,setAnswer]=useState(''),[practice,setPractice]=useState<{correct:boolean;message:string;supportive_visual?:boolean;support_message?:string}|null>(null),[hint,setHint]=useState(false);
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;controller.current?.abort();};},[]);
  useEffect(()=>()=>{if(preview)URL.revokeObjectURL(preview);},[preview]);
  function edit(value:string){setSteps(value);setConfirmed(false);setResult(null);setGuidance(null);setPractice(null);setAnswer('');setHint(false);if(pages.length)setPages(old=>old.map(p=>p.page===page?{...p,text:value}:p));}
  function draft(value:string,message:string){setSteps(value);setRaw(value);setConfirmed(false);setResult(null);setGuidance(null);setPractice(null);const hint=value.trim()&&!value.includes('=')?' This looks like a question rather than worked steps — you can also paste it into Learning Studio to solve it there.':'';setStatus(message+hint);}
  function cancel(){controller.current?.abort();setStatus('Reading cancelled. You can type your steps manually.');}
  function removeUpload(){controller.current?.abort();controller.current=null;ocrCache.current.remove(imageKey.current);imageKey.current='';setFile(null);setPrepared(null);setPageImage(null);setCropOpen(false);setPreview('');setConfirmed(false);setResult(null);setGuidance(null);setPractice(null);setAnswer('');setHint(false);setPages([]);setError('');setBusy(false);draft('','Upload removed. Upload again or type your steps below.');}
  async function readImage(image:File,localOnly=!metaVision){
    const abort=new AbortController();controller.current=abort;setBusy(true);setError('');setCropOpen(false);setPrepared(image);setPreview(URL.createObjectURL(image));setStatus(localOnly?'Reading quickly…':'Reading your work. You can cancel at any time.');
    try{
      const key=await ocrCache.current.key(image);imageKey.current=key;
      if(abort.signal.aborted||!mounted.current)return;
      const saved=localOnly?ocrCache.current.get(key):undefined;
      if(saved){draft(saved.text,`Saved ${saved.confirmed?'student-reviewed transcription':'quick-read draft'} for this exact crop — no new recognition call. Review before submitting.`);return;}
      let text='',message='';
      if(localOnly){
        try{
          const local=await withDeadline(signal=>recognizeLocally(image,signal,m=>{if(mounted.current)setStatus(m);}),abort.signal,8000);
          text=local.text;message='Quick-read draft — review every line. Handwriting and symbols may be incorrect.';
        }catch(e){if(abort.signal.aborted)throw e;}
      }
      if(!text.trim()){
        if(abort.signal.aborted||!mounted.current)return;
        setStatus(localOnly?'Quick read could not read this crop. Trying careful recognition automatically. This can take up to 3 minutes; you can cancel.':'Reading the crop with handwriting recognition…');
        const form=new FormData();form.append('file',image);
        const upload=await withDeadline(signal=>api<{steps:string[];message:string}>('/handwriting/upload',{method:'POST',body:form,signal}),abort.signal,195000);
        text=upload.steps.join('\n');message=upload.message;
      }
      if(!abort.signal.aborted&&mounted.current){
        if(text.trim()){ocrCache.current.set(key,text);draft(text,message);}
        else{setStatus('');setError((message?message+' ':'')+'No transcription is ready. Try a wider crop with cleanup off, or type the visible steps below.');}
      }
    }catch(e){if(mounted.current)setError(abort.signal.aborted?'Recognition cancelled; manual entry remains available.':(e as Error).message);}finally{if(mounted.current){setBusy(false);controller.current=null;}}
  }
  async function readDocument(document:File){const abort=new AbortController();controller.current=abort;setBusy(true);setError('');setStatus('Extracting document text…');try{
    const form=new FormData();form.append('file',document);const data=await api<{text:string;message:string;page_text?:{page:number;text:string}[]}>('/work/document',{method:'POST',body:form,signal:abort.signal});
    if(abort.signal.aborted||!mounted.current)return;
    let extracted=data.page_text||[];let message=data.message;
    if(document.type==='application/pdf'&&extracted.some(p=>!p.text.trim())){const ocr=await recognizePdfLocally(document,abort.signal,m=>{if(mounted.current)setStatus(m);},{embedded:extracted,recognize:metaVision?async(image,signal,progress)=>{progress('Reading this scanned page…');const blob=await (await fetch(image)).blob();const form=new FormData();form.append('file',new File([blob],'document-page.png',{type:'image/png'}));const response=await withDeadline(child=>api<{steps:string[];message:string}>('/handwriting/upload',{method:'POST',body:form,signal:child}),signal,70000);if(!response.steps.length)throw new Error(response.message);return {text:response.steps.join('\n'),confidence:null};}:undefined});extracted=ocr.pages;message=(extracted.some(p=>p.text.trim())?'Document text is ready. Check the recognized lines before submitting.':'No readable text was found. Enter the steps manually.')+' '+ocr.warnings.join(' ');}
    if(abort.signal.aborted||!mounted.current)return;
    setPages(extracted);setPage(extracted[0]?.page||1);draft(extracted[0]?.text??data.text,message+' Select one problem and its working for review.');
  }catch(e){if(mounted.current)setError(abort.signal.aborted?'Document reading cancelled.':(e as Error).message);}finally{if(mounted.current){setBusy(false);controller.current=null;}}}
  async function readPageImage(image:File,pageNo:number){
    const abort=new AbortController();controller.current=abort;setBusy(true);setError('');setStatus('Reading cropped page…');
    try{
      let text='',message='Quick-read draft — review every line.';
      try{const local=await withDeadline(signal=>recognizeLocally(image,signal,()=>{}),abort.signal,8000);text=local.text;}catch(e){if(abort.signal.aborted)throw e;}
      if(!text.trim()){
        const form=new FormData();form.append('file',image);
        const upload=await withDeadline(signal=>api<{steps:string[];message:string}>('/handwriting/upload',{method:'POST',body:form,signal}),abort.signal,195000);
        text=upload.steps.join('\n');message=upload.message;
      }
      if(!abort.signal.aborted&&mounted.current){
        if(text.trim()){setPages(old=>old.map(p=>p.page===pageNo?{...p,text}:p));if(page===pageNo)draft(text,message);else setStatus(`Page ${pageNo} text is ready. Switch to page ${pageNo} to review.`);}
        else setError('No text found on this crop. Try a wider selection.');
      }
    }catch(e){if(mounted.current)setError(abort.signal.aborted?'Cancelled.':(e as Error).message);}finally{if(mounted.current){setBusy(false);controller.current=null;}}
  }
  async function cropPdfPage(pageNo:number){
    if(!file||busy)return;setBusy(true);setError('');setStatus('Rendering page image…');
    try{
      const bytes=new Uint8Array(await file.arrayBuffer());
      const abort=new AbortController();controller.current=abort;
      const {pdfPageImages}=await import('@/lib/pdf-pages');
      for await(const shot of pdfPageImages(bytes,abort.signal,{pages:[pageNo]})){
        const blob=await (await fetch(shot.image)).blob();
        if(!abort.signal.aborted&&mounted.current){setPageImage({page:pageNo,file:new File([blob],`page-${pageNo}.png`,{type:'image/png'})});setStatus('Crop the maths on this page, then use the crop.');}
      }
    }catch(e){if(mounted.current)setError((e as Error).message);}finally{if(mounted.current){setBusy(false);controller.current=null;}}
  }
  function choose(next:File){if(busy)return;setError('');if(next.size>5*1024*1024){setError('Choose a file no larger than 5 MB.');return;}const image=['image/png','image/jpeg','image/webp'].includes(next.type),document=['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(next.type);if(!image&&!document){setError('Use PNG, JPEG, WebP, PDF or DOCX.');return;}imageKey.current='';setFile(next);setPrepared(null);setPageImage(null);setResult(null);setGuidance(null);setPractice(null);setConfirmed(false);setPages([]);setPreview('');draft('','Review the crop or document before checking your work.');if(image){setPreview(URL.createObjectURL(next));setCropOpen(true);}else{setCropOpen(false);void readDocument(next);}}
  async function submit(){if(!confirmed||!steps.trim()||cropOpen||pageImage||busy)return;ocrCache.current.set(imageKey.current,steps,true);setBusy(true);setStatus('Checking your steps…');setError('');setHint(false);setGuidance(null);setPractice(null);try{const review=await post<Review>('/work/review',{steps:steps.split('\n').map(x=>x.trim()).filter(Boolean)});if(mounted.current){setResult(review);setStatus('');setConfirmed(false);await client.invalidateQueries({queryKey:['progress']});}}catch(e){if(mounted.current)setError((e as Error).message);}finally{if(mounted.current)setBusy(false);}}
  const stage=result?.practice&&practice?4:result?.corrected?3:steps?2:1;
  return <section className="check-work-page">
    <header className="work-intro"><div><span className="eyebrow">UNDERSTAND YOUR MISTAKES. LEARN WITH MIA.</span><h2>Every step tells a story.</h2><p>Review your handwriting, find the first mistake, and build understanding with a verified correction.</p></div><div className="work-intro-note"><BookOpen size={30}/><strong>Every mistake has<br/>something to teach.</strong></div></header>
    <ol className="work-stages" aria-label="Review progress">{['Upload work','Review steps','Explanation','Practice'].map((s,i)=><li key={s} aria-current={stage===i+1?'step':undefined}><span>{i+1}</span>{s}</li>)}</ol>
    <div className="check-work-layout"><section className="card work-upload-card"><h3><FileText size={20}/>Your work</h3>
      <label className="work-dropzone" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();const f=e.dataTransfer.files[0];if(f)choose(f);}}><Upload size={24}/><strong>{file?file.name:'Upload or drop your work'}</strong><span>Image, PDF or DOCX · up to 5 MB</span><input aria-label="Upload handwritten work or document" type="file" accept="image/png,image/jpeg,image/webp,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" disabled={busy} onChange={e=>{const f=e.target.files?.[0];e.target.value='';if(f)choose(f);}}/></label>
      {pageImage?<HandwritingImageEditor key={'page-'+pageImage.page} file={pageImage.file} onCancel={()=>setPageImage(null)} onApply={image=>{const n=pageImage.page;setPageImage(null);void readPageImage(image,n);}}/>:cropOpen&&file?<HandwritingImageEditor key={file.name+file.lastModified} file={file} onCancel={()=>setCropOpen(false)} onApply={image=>void readImage(image)}/>:preview&&<><img className="review-original-image" src={preview} alt="Submitted work: compare with the extracted lines"/><Button variant="outline" disabled={busy} onClick={()=>setCropOpen(true)}><Crop size={16}/>Adjust crop</Button><Button variant="outline" disabled={busy} onClick={removeUpload}><Trash2 size={16}/>Remove</Button>{file&&<div className="actions"><Button type="button" variant="outline" disabled={busy} onClick={()=>void readImage(prepared||file,false)}>{metaVision?'Read carefully':'Use handwriting recognition'}</Button><Button type="button" variant="outline" disabled={busy} onClick={()=>void readImage(prepared||file,true)}>Quick read</Button></div>}</>}
      {file&&!preview&&!cropOpen&&!pageImage&&<div className="actions"><Button type="button" variant="outline" disabled={busy} onClick={removeUpload}><Trash2 size={16}/>Remove upload</Button></div>}{busy&&<p role="status" className="work-processing">{status||'Checking your steps…'}{controller.current&&<button type="button" onClick={cancel}>Cancel</button>}</p>}
      {status&&!busy&&<p className="tiny" role="status">{status}</p>}
      {pages.length>0&&!(pages.find(p=>p.page===page)?.text||'').trim()&&file?.type==='application/pdf'&&<div className="actions"><Button type="button" variant="outline" disabled={busy} onClick={()=>void cropPdfPage(page)}><Crop size={16}/>Crop & read page image</Button></div>}
      {pages.length>1&&<label>Document page<select value={page} disabled={busy} onChange={e=>{const n=+e.target.value;setPage(n);draft(pages.find(p=>p.page===n)?.text||'','Choose one problem on this page. Remove unrelated questions from the editable text before checking.');}}>{pages.map(p=><option key={p.page} value={p.page}>Page {p.page}{p.text?'':' — unread'}</option>)}</select></label>}
      <label>Teaching language<select aria-label="Review teaching language" value={language} onChange={e=>setLanguage(e.target.value)}><option>English</option><option>Tamil</option></select></label><form onSubmit={e=>{e.preventDefault();void submit();}}><label>Editable mathematical steps<textarea rows={7} value={steps} maxLength={6000} placeholder={'2x + 6 = 14\n2x = 14 + 6\nx = 10'} disabled={busy||cropOpen||!!pageImage} onChange={e=>edit(e.target.value)} required/></label><p className="tiny">One equality per line. Include the original problem first; select only one problem. You can also type without uploading.</p>
      {raw&&<details><summary>Original extracted text</summary><pre className="raw-work">{raw}</pre></details>}
      <label className="check-label"><input type="checkbox" checked={confirmed} disabled={busy||cropOpen||!!pageImage} onChange={e=>setConfirmed(e.target.checked)}/>I checked these lines against my work.</label><Button disabled={busy||cropOpen||!!pageImage||!confirmed||!steps.trim()}><ShieldCheck size={17}/>{busy?'Processing…':'Submit for review'}<ArrowRight size={16}/></Button></form>
      {error&&<p className="error-box" role="alert">{error}</p>}
    </section>
    <div className="work-teaching-column">{memory?.revision&&<section className="card"><h3>Mistake Memory · a short revision</h3><p>Your saved work includes {memory.patterns.find(p=>p.category==='fraction_addition')?.count} fraction-addition review(s) with an error. Revisit equal-sized parts.</p><button className="text-button" onClick={()=>{edit('1/2 + 1/4 = ');setShowLab(true);}}>Try ½ + ¼ again</button><p className="tiny">Based on your saved maths work, not emotion detection.</p></section>}{(showLab||result?.corrected?.topic==='Fractions')&&<FractionLab key={result?.lines?.[0]?.normalized||steps} expression={result?.lines?.[0]?.normalized||steps}/>}{!result?.corrected&&<WaitingMia text={steps} busy={busy}/ >}{result?<>
      <section className="card work-feedback"><h3>{result.first_incorrect_step?<AlertCircle size={20}/>:<ShieldCheck size={20}/>}Mathematical review</h3><p role="status">{result.message}</p>
      <div className="work-feedback-lines">{result.lines.map(line=><article className={`work-line work-line-${line.status}`} key={line.number}><span>Step {line.number}</span><div><strong>{line.original}</strong>{line.normalized!==line.original&&<p>Proposed notation: {line.normalized}</p>}<p>{line.reason}</p></div><span className="work-line-status">{labels[line.status]||line.status}</span></article>)}</div>
      {result.normalization_required&&<Button onClick={()=>{setRaw(steps);edit(result.lines.map(l=>l.normalized).join('\n'));}}>Use proposed notation, then review</Button>}
      {result.verified_correction&&<div className="work-correction"><strong>Verified correction</strong><MathText value={result.verified_correction}/></div>}</section>
      {result.corrected&&<><section className="card work-guidance"><div className="row between"><h3>Explain My Way</h3><select aria-label="Guidance language" value={language} onChange={e=>setLanguage(e.target.value)}><option>English</option><option>Tamil</option></select><select aria-label="Explanation style" value={style} onChange={e=>setStyle(e.target.value)}><option value="simple">Simple steps</option><option value="chocolate">Chocolate example</option><option value="shopping">Shopping example</option><option value="visual">Visual explanation</option></select></div><Button disabled={teachingBusy} variant="outline" onClick={async()=>{setTeachingBusy(true);setError('');try{setGuidance(await post<Guidance>(`/work/${result.id}/teach`,{language,style}));}catch(e){setError((e as Error).message);}finally{setTeachingBusy(false);}}}>{teachingBusy?'Preparing guidance…':'Explain this feedback'}</Button>{guidance&&<div><span className="tiny">{guidance.mode}</span><p>{guidance.guidance.explanation}</p><p><strong>Possible learning difficulty: </strong>{guidance.guidance.misconception}</p><p>{guidance.guidance.strategy}</p><p>{guidance.guidance.encouragement}</p></div>}</section>
      <QuestionTeaching autoStart initialLanguage={language==='Tamil'?'ta':'en'} reviewId={result.id} key={result.id} question={result.lines[0].normalized} solution={result.corrected} feedback={guidance?{text:guidance.guidance.explanation,language:language==='Tamil'?'ta':'en',mode:guidance.mode}:undefined}/>
      {result.practice&&<section className="card work-practice"><h3><CheckCircle2 size={20}/>Try a similar question</h3><p>Check whether you can apply the same idea independently.</p>{result.practice.kind==='comparison'?<p>{result.practice.equation}</p>:<MathText value={result.practice.equation}/>}<form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{const response=await post<{correct:boolean;message:string;next_question?:Review['practice'];practice_complete?:boolean;supportive_visual?:boolean;support_message?:string}>(`/work/${result.id}/practice`,{answer});setPractice(response);if(response.supportive_visual)setShowLab(true);if(response.practice_complete)setResult(previous=>previous?{...previous,practice:null}:previous);if(response.next_question){setResult(previous=>previous?{...previous,practice:response.next_question!}:previous);setAnswer('');setHint(false);}}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}><label>Your answer<input value={answer} onChange={e=>{setAnswer(e.target.value);setPractice(null);}} required maxLength={100} placeholder={result.practice.variable?`${result.practice.variable} = …`:result.practice.kind==='comparison'?'<, = or >':'Your fraction answer'}/></label><Button disabled={busy}>Check answer</Button></form><button className="text-button" onClick={()=>setHint(!hint)}>Give me a hint</button>{hint&&<p>{result.practice.hint}</p>}{practice&&<p role="status" className={practice.correct?'success-box':'info-box'}>{practice.message}{practice.support_message&&<><br/>{practice.support_message}<br/><small>Based on your last three answers. Explore the Fraction Lab above.</small></>}</p>}</section>}</>}
    </>:null}</div></div>
  </section>;
}
