"use client";
import {useEffect,useLayoutEffect,useReducer,useRef,useState} from 'react';
import type {Solution} from '@/lib/types';
import {initialClassroom,classroomTransition,remainingNarration,teachingSteps,rowNeedsScroll} from '@/lib/question-teaching';
import {Teacher} from './teacher';
import {api} from '@/lib/api';
import {ThemedExampleVisual} from './themed-example-visual';
import {tamilStep,displayEquation,answerLines,wantsVisual} from '@/lib/teaching-language';
import {realWorldExample, type ExampleLanguage} from '@/lib/real-world-example';
import {RealWorldVisual} from './real-world-visual';
import {MathText} from './math';
import {GeometryDiagram} from './geometry-diagram';
import {Button} from './ui/button';
import {Play,Pause,RotateCcw,SkipBack,SkipForward,Square} from 'lucide-react';
import {MiaWhiteboard} from './mia-whiteboard';

export function QuestionTeaching({question,solution,onComplete,feedback,reviewId,initialLanguage='en',autoStart=false}: {reviewId?:string;initialLanguage?:ExampleLanguage;autoStart?:boolean;question:string;solution:Solution;onComplete?:()=>void;feedback?:{text:string;language:ExampleLanguage;mode:string}}) {
  const [lessonSession,lessonDispatch]=useReducer(classroomTransition,{...initialClassroom,phase:autoStart?'RESUMING':'READY'});
  const [exampleSession,exampleDispatch]=useReducer(classroomTransition,initialClassroom);
  const boardRef=useRef<HTMLDivElement>(null);
  const [speaking,setSpeaking]=useState(false);
  const [command,setCommand]=useState<{id:number;action:'stop'|'replay'}>();
  const [answerLanguage,setAnswerLanguage]=useState<ExampleLanguage>('en');
  const [localAnswer,setLocalAnswer]=useState<{id:number;text:string;mode?:string}>();
  const [boardAnswer,setBoardAnswer]=useState<{id:number;text:string;kind:'chat'|'example'|'feedback';visual?:string}>();
  const [answerProgress,setAnswerProgress]=useState(0);
  const [showExample,setShowExample]=useState(false);
  const [language,setLanguage]=useState<ExampleLanguage>(initialLanguage);
  const [context,setContext]=useState('');
  const [generating,setGenerating]=useState(false);
  const [generated,setGenerated]=useState<{message:string;mode:string;context:string}|null>(null);
  const generation=useRef<AbortController|null>(null);
  useEffect(()=>{setLanguage(initialLanguage);},[initialLanguage]);
  useEffect(()=>()=>generation.current?.abort(),[]);
  const session=showExample?exampleSession:lessonSession;
  const dispatch=showExample?exampleDispatch:lessonDispatch;
  const [notice,setNotice]=useState('');
  const serial=useRef(0), cursor=useRef<HTMLSpanElement>(null);
  const [screen,setScreen]=useState({x:.2,y:.42});
  const [reduced,setReduced]=useState(false);
  const active=session.phase==='TEACHING'||session.phase==='RESUMING';
  const example=realWorldExample(question,solution,language);
  const steps=showExample&&example?example.steps:teachingSteps(solution.steps).map(step=>language==='ta'?{...step,explanation:tamilStep(step.explanation)}:step);
  const current=steps[session.step];
  const answerPool=(session.phase==='ANSWERING'||session.phase==='WAITING_FOR_STUDENT')&&boardAnswer?answerLines(boardAnswer.text):[];
  const boardItems=answerPool.length?answerPool.map(line=>({equation:line,latex:null,plain:true})):steps;
  const boardStep=answerPool.length?Math.min(answerPool.length-1,Math.floor(answerProgress*answerPool.length)):session.step;

  useLayoutEffect(()=>{const board=boardRef.current,row=board?.querySelector<HTMLElement>('[aria-current="step"]');if(!board||!row)return;if(showExample){board.scrollTo({top:0,behavior:reduced?'instant':'smooth'});return;}const r=row.getBoundingClientRect(),b=board.getBoundingClientRect();if(!rowNeedsScroll(r.top,r.bottom,b.top,b.bottom))return;board.scrollTo({top:board.scrollTop+r.top-b.top-36,behavior:reduced?'instant':'smooth'});},[boardStep,showExample,reduced]);

  useEffect(()=>{const query=matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setReduced(query.matches);update();query.addEventListener('change',update);return()=>query.removeEventListener('change',update);},[]);
  useLayoutEffect(()=>{
    const update=()=>{const marker=cursor.current,stage=marker?.closest('.classroom-stage');if(!marker||!stage)return;const point=marker.getBoundingClientRect(),bounds=stage.getBoundingClientRect();if(bounds.width&&bounds.height)setScreen({x:(point.left+point.width/2-bounds.left)/bounds.width,y:(point.top+point.height/2-bounds.top)/bounds.height});};
    update();const board=boardRef.current;board?.addEventListener('scroll',update,{passive:true});const observer=new ResizeObserver(update);if(cursor.current?.parentElement)observer.observe(cursor.current.parentElement);window.addEventListener('resize',update);return()=>{observer.disconnect();board?.removeEventListener('scroll',update);window.removeEventListener('resize',update);};
  },[session.progress,session.step,showExample,reduced]);
  if(!solution.verified||!current)return <p role="status">Mia needs a verified result before teaching. Review the solver’s clarification above.</p>;
  const transcript=remainingNarration(current.explanation,session.segmentStart);
  function stopSpeech(){setCommand({id:++serial.current,action:'stop'});}
  function interrupt(){stopSpeech();dispatch({type:'interrupt'});}
  function resume(){setCommand(undefined);setNotice('');if(session.progress>=1){if(session.step+1<steps.length){dispatch({type:'move',step:session.step+1});dispatch({type:'resume'});}else dispatch({type:'replay'});}else dispatch({type:'resume'});}

  function answer(text:string,locale:ExampleLanguage=language,mode?:string,kind:'example'|'feedback'='example'){setAnswerLanguage(locale);stopSpeech();dispatch({type:'answering'});setLocalAnswer({id:++serial.current,text,mode});setBoardAnswer({id:++serial.current,text,kind});setAnswerProgress(0);}
  const status=({READY:'All working is shown. Press Play for Mia to explain each step.',TEACHING:'Teaching',RESUMING:'Resuming',INTERRUPTED:'Listening — your place is saved',ANSWERING:'Answering your question',WAITING_FOR_STUDENT:'Does that make sense? Resume when you’re ready.',COMPLETE:'Lesson complete. The answer is shown above.'})[session.phase];
  const controls=<>
    <div className="classroom-controls">
      <div className="classroom-transport" role="group" aria-label="Lesson playback">
      <Button title={active?'Pause lesson':'Play or resume lesson'} disabled={session.phase==='ANSWERING'} onClick={active?interrupt:resume}>{active?<Pause size={17}/>:<Play size={17}/>}{active?'Pause':session.phase==='READY'||session.phase==='COMPLETE'?'Play':'Resume'}</Button>
      <Button variant="outline" title="Stop narration and keep your place" onClick={()=>{interrupt();setNotice('Stopped. Your board and place are saved.');}}><Square size={16}/>Stop</Button>
      <Button variant="outline" title="Replay this step" onClick={()=>{setNotice('');setCommand({id:++serial.current,action:'replay'});dispatch({type:'replay'});}}><RotateCcw size={16}/>Replay</Button>
      <Button variant="outline" disabled={session.step===0} onClick={()=>{setNotice('');stopSpeech();dispatch({type:'move',step:session.step-1});}}><SkipBack size={16}/>Previous</Button>
      <Button variant="outline" disabled={session.step===steps.length-1} onClick={()=>{setNotice('');stopSpeech();dispatch({type:'move',step:session.step+1});}}><SkipForward size={16}/>Next</Button>
      </div>

      <div className="classroom-learning-actions">
      {feedback&&<Button variant="outline" onClick={()=>answer(feedback.text,feedback.language,feedback.mode,'feedback')}>Hear feedback</Button>}
      <Button variant="outline" disabled={generating} onClick={async()=>{interrupt();setNotice('');if(example&&!context.trim()){setGenerated(null);setCommand(undefined);setShowExample(true);exampleDispatch({type:'move',step:0});exampleDispatch({type:'resume'});return;}setShowExample(false);setGenerating(true);const abort=new AbortController();generation.current=abort;try{const response=await api<{message:string;mode:string;context:string}>('/tutor/real-world',{method:'POST',signal:abort.signal,body:JSON.stringify({equation:question,variable:solution.variable,review_id:reviewId,language:language==='ta'?'Tamil':'English',context:context.trim()||'everyday life'})});if(!abort.signal.aborted){setGenerated(response);answer(response.message,language,response.mode);}}catch(error){if(abort.signal.aborted)return;if(example){setGenerated(null);setCommand(undefined);setShowExample(true);exampleDispatch({type:'move',step:0});exampleDispatch({type:'resume'});setNotice(language==='ta'?'புதிய உதாரணம் உருவாக்க முடியவில்லை — சரிபார்க்கப்பட்ட உதாரணம் காட்டப்படுகிறது.':'A fresh example could not be created — showing the checked built-in example instead. Your verified maths is preserved.');}else{const result=solution.solution??solution.solutions.join(', ');const fallback=language==='ta'?`அன்றாட வாழ்க்கையுடன் இணைத்துப் பார்ப்போம். ${tamilStep(current.explanation)} சரிபார்க்கப்பட்ட விடை: ${result}. சமமான குழுக்களாகப் பிரிப்பதை நினைத்துப் பாருங்கள். இந்தப் படி ஏன் சரி என்று உங்கள் வார்த்தையில் சொல்ல முடியுமா?`:`Let's connect this to everyday life. ${current.explanation} The verified result is ${result}. Think of sharing equal groups — can you say in your own words why this step works?`;setGenerated(null);answer(fallback,language,language==='ta'?'மியா':'Mia');setNotice(language==='ta'?'புதிய உதாரணம் உருவாக்க முடியவில்லை — சரிபார்க்கப்பட்ட விளக்கம் காட்டப்படுகிறது.':'A fresh example could not be created — showing a checked explanation instead.');}}finally{if(generation.current===abort)setGenerating(false);}}}>{generating?'Creating example…':'Real-world example'}</Button>
      <label className="example-context">Your example setting<input aria-label="Real-world setting" maxLength={80} value={context} placeholder="Chocolate, pizza, coffee, cake…" onChange={e=>setContext(e.target.value)}/></label>
      {showExample&&<Button variant="outline" onClick={()=>{stopSpeech();exampleDispatch({type:'interrupt'});setShowExample(false);setNotice('Your original lesson is restored. Press Resume to continue.');}}>Back to lesson</Button>}
      <label className="example-language">Teaching language<select aria-label="Teaching language" value={language} onChange={e=>{interrupt();generation.current?.abort();setGenerating(false);setGenerated(null);setLanguage(e.target.value as ExampleLanguage);setLocalAnswer(undefined);lessonDispatch({type:'move',step:lessonSession.step});exampleDispatch({type:'move',step:exampleSession.step});}}><option value="en">English</option><option value="ta">தமிழ்</option></select></label>
      </div>
      <details><summary>Reading options</summary><div className="actions">
        <Button variant="outline" onClick={()=>{stopSpeech();dispatch({type:'read'});}}>Read step without audio</Button>
      </div></details>
    </div>
    <p role="status" className="classroom-session-status">{status}</p>{notice&&<p role="status" className="info-box">{notice}</p>}
  </>;
  const board=<div ref={boardRef} className="classroom-whiteboard" aria-label="Lesson whiteboard" tabIndex={0}>
    <span className="eyebrow">{answerPool.length?`Mia's answer · Line ${boardStep+1} / ${boardItems.length}`:`${solution.topic} · Step ${session.step+1} / ${steps.length}`}</span>
    {generated&&!showExample&&<section className="generated-example"><ThemedExampleVisual context={generated.context} question={question} solution={solution} language={language}/></section>}
    {showExample&&example&&<RealWorldVisual key={`${question}-${language}`} example={example} step={session.step} onInteract={interrupt} boardOnly/>}
    {answerPool.length>0&&boardAnswer?.kind==='chat'&&boardAnswer.visual&&!showExample&&<section className="answer-visual"><ThemedExampleVisual context={boardAnswer.visual} question={question} solution={solution} language={language}/></section>}
    <MiaWhiteboard items={boardItems} step={boardStep} playing={active||session.phase==='ANSWERING'} diagram={showExample?undefined:(solution.diagram||undefined)} handwritten />
    <span ref={cursor} className="classroom-writing-cursor mia-3d-anchor" aria-hidden="true" style={{position:'absolute',left:'60%',top:'40%'}}>{active?'←':' '}</span>
    <ol className="classroom-working" aria-label="Step-by-step solution" hidden>
      {boardItems.map((step,index)=>showExample&&index!==boardStep?null:<li key={index} aria-current={index===boardStep?'step':undefined} className={index===boardStep?'current-working-step':''}>
        <div className="working-step-heading"><span>{`Step ${index+1}`}</span></div>
        <div className="working-equation" aria-label={step.equation}>
          <MathText value={step.latex||step.equation} latex={!!step.latex}/>
          {index===boardStep&&<span className="classroom-writing-cursor" aria-hidden="true">{active?'←':' '}</span>}

        </div>
      </li>)}
    </ol>
    {showExample&&example&&session.phase==='COMPLETE'&&<span className="eyebrow">Example complete · answer verified</span>}
    {solution.diagram&&!showExample&&<span className="tiny">Diagram shown on Mia board above.</span>}
    {!showExample&&session.phase==='COMPLETE'&&<p className="classroom-result">{solution.kind==='none'?'No real solutions':solution.kind==='infinite'?'Infinitely many solutions':`Verified result: ${solution.solution??solution.solutions.join(', ')}`}</p>}
    {solution.kind==='parametric'&&<p className="tiny">The answer depends on the unspecified term value.</p>}
  </div>;
  return <section className="classroom-card" aria-label="Interactive maths classroom">
    <header className="classroom-lesson-header"><div><span className="eyebrow">LEARNING STUDIO</span><h2>{solution.topic || 'Your maths lesson'}</h2><p>Let’s explore {question} step by step</p></div><div className="classroom-progress"><span>Step {session.step+1} of {steps.length}</span><progress aria-label="Lesson progress" value={session.step+session.progress} max={steps.length}/><strong>{Math.round((session.step+session.progress)/steps.length*100)}%</strong></div></header>
    <Teacher narrationLanguage={session.phase==='ANSWERING'?answerLanguage:language} lessonLabel={showExample?'Local checked example':undefined} classroomBoard={board} classroomControls={controls} equation={question} variable={solution.variable||undefined} transcript={transcript} contextTranscript={showExample&&example?`${example.title}. ${example.context} ${current.explanation}`:current.explanation} stepNumber={session.step+1}
      writingBoard={{text:answerPool.length?answerPool[boardStep]:displayEquation(current.equation),progress:answerPool.length?answerProgress:session.progress,screen,active:!reduced&&(active||session.phase==='ANSWERING')&&speaking,paused:!active&&session.phase!=='ANSWERING'}}
      teachingGesture={(active||session.phase==='ANSWERING')&&speaking?'point':undefined} autoNarrate={active} playbackCommand={command} localAnswer={localAnswer}
      onInterrupt={()=>dispatch({type:'interrupt'})} onAnswerState={state=>dispatch({type:state==='answering'?'answering':'waiting'})}
      onSpeaking={value=>{setSpeaking(value);if(value)dispatch({type:'started'});}}
      onNarrationProgress={value=>{setAnswerProgress(value);dispatch({type:'progress',value});}}
      onTourStop={()=>{if(active)dispatch({type:'interrupt'});}}
      onNext={()=>{stopSpeech();if(session.step+1<steps.length){dispatch({type:'move',step:session.step+1});dispatch({type:'resume'});}}}
      onNarrationEnd={()=>dispatch({type:'ended',count:steps.length})} onAnswerText={(text,student)=>{setBoardAnswer(prev=>({id:++serial.current,text,kind:student===undefined?prev?.kind??'chat':'chat',visual:student===undefined?prev?.visual:(wantsVisual(student)?student:undefined)}));setAnswerProgress(0);}}/>
    {!showExample&&session.phase==='COMPLETE'&&onComplete&&<Button variant="outline" onClick={onComplete}>Mark lesson complete</Button>}
    <p className="classroom-limitations">Mia board shows the verified maths and writes her answers line by line. Narration uses on-device browser speech. Voice input works where your browser supports it; typing always works.</p>
  </section>;
}
