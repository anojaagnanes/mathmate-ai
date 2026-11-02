'use client';
import dynamic from 'next/dynamic';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import { Pause, Play, Square, Volume2, VolumeX, Send } from 'lucide-react';
import { LipSyncClock, type SyncMode } from '@/lib/lip-sync';
import type {WritingBoardState} from './writing-board-scene';
import type { VoiceProvider } from '@/lib/voice-provider';
import { api, post } from '@/lib/api';
import {matchesLanguage,selectNarrationVoice,speechText} from '@/lib/teaching-language';
import { encouragement, type TeacherState } from '@/lib/teacher-state';
import { Button } from './ui/button';
const Avatar = dynamic(() => import('./teacher-avatar'), {ssr: false, loading: () => <div className="teacher-3d avatar-fallback">Opening Mia’s studio…</div>});

export function Teacher({narrationLanguage='en',lessonLabel, equation, transcript, reaction, onSpeaking, onNext, voiceProvider, stepNumber, variable, autoNarrate = false, onNarrationEnd, onTourStop, playbackCommand, onNarrationProgress, teachingGesture, writingBoard, classroomBoard, classroomControls, onInterrupt, onAnswerState, localAnswer, contextTranscript, onAnswerText}: {
  narrationLanguage?:'en'|'ta'; lessonLabel?:string;
  contextTranscript?:string;
  classroomBoard?: ReactNode; classroomControls?: ReactNode;
  onInterrupt?:()=>void; onAnswerState?:(state:'answering'|'waiting')=>void; onAnswerText?:(text:string,student?:string)=>void;
  localAnswer?:{id:number;text:string;mode?:string};
  writingBoard?: WritingBoardState;
  onNarrationProgress?: (progress: number) => void; teachingGesture?: "point";
  playbackCommand?: {id: number; action: "pause" | "resume" | "replay" | "stop"};
  autoNarrate?: boolean; onNarrationEnd?: () => void; onTourStop?: () => void;
  variable?: string; stepNumber?: number; voiceProvider?: VoiceProvider; equation: string; transcript: string; reaction?: 'correct' | 'incorrect'; onSpeaking?: (speaking: boolean) => void; onNext?: () => void;
}) {
  const [explanationTab,setExplanationTab]=useState<'explanation'|'transcript'>('explanation');
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voice, setVoice] = useState('');
  const [muted, setMuted] = useState(false);
  const lipSync = useRef(new LipSyncClock());
  const [syncMode, setSyncMode] = useState<SyncMode>('idle');
  const lessonAudio = useRef(false);
  const [state, setState] = useState<TeacherState>('idle');
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState(classroomBoard ? '' : 'Hi, I’m Mia. Take your time — every small step counts.');
  const [mode, setMode] = useState('Mia');
  const [error, setError] = useState('');
  const [available, setAvailable] = useState(false);
  const [caption, setCaption] = useState('');
  const [spokenWord, setSpokenWord] = useState<{start:number;end:number}|null>(null);
  const [understood, setUnderstood] = useState(false);
  const speechId = useRef(0);
  const manualHandoff = useRef(false);
  const mounted = useRef(true);
  const progressCallback = useRef(onNarrationProgress); progressCallback.current = onNarrationProgress;
  const narrationEnd = useRef(onNarrationEnd); narrationEnd.current = onNarrationEnd;
  const answerState=useRef(onAnswerState);answerState.current=onAnswerState;
  const tourStop = useRef(onTourStop); tourStop.current = onTourStop;
  const speakingCallback = useRef(onSpeaking);
  speakingCallback.current = onSpeaking;
  const remoteAudio = useRef<HTMLAudioElement | null>(null);
  const audioUrl = useRef<string | null>(null);
  const audioRequest = useRef<AbortController | null>(null);
  function releaseAudio() {audioRequest.current?.abort(); audioRequest.current=null; remoteAudio.current?.pause(); remoteAudio.current = null; if (audioUrl.current) URL.revokeObjectURL(audioUrl.current); audioUrl.current = null;}
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);
  function stop() {
    speechId.current++; lipSync.current.stop(); releaseAudio();
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    utterance.current = null; setSpokenWord(null); setSyncMode('idle'); setState('idle'); speakingCallback.current?.(false);
  }
  useEffect(() => {
    mounted.current = true;
    api<{configured: boolean}>('/tutor/status').then(s => {if (mounted.current) setMode('Mia');}).catch(() => {});
    if (!('speechSynthesis' in window)) return () => {mounted.current = false; speechId.current++; lipSync.current.stop(); releaseAudio(); speakingCallback.current?.(false);};
    setAvailable(true);
    const update = () => setVoices(window.speechSynthesis.getVoices());
    update(); window.speechSynthesis.addEventListener('voiceschanged', update);
    api<{muted: boolean; voice: string}>('/settings').then(s => {if (mounted.current) {setMuted(s.muted); setVoice(s.voice);}}).catch(() => {});
    return () => {mounted.current = false; speechId.current++; lipSync.current.stop(); releaseAudio(); window.speechSynthesis.cancel(); speakingCallback.current?.(false); window.speechSynthesis.removeEventListener('voiceschanged', update);};
  }, []);
  useEffect(() => {stop(); setCaption(transcript); setUnderstood(false); if(classroomBoard)setReply('');}, [transcript, equation, stepNumber, narrationLanguage]); // Each new board step cancels stale narration.
  useEffect(() => {if (reaction) {stop(); setState(reaction); setReply(encouragement[reaction]);}}, [reaction]);
  // Default voice cascade: an explicitly saved voice wins, else Clara (Mia's default),
  // else Zira (Microsoft documents Zira as female; verified provider mapping, not a gender guess).
  // https://learn.microsoft.com/en-us/uwp/api/windows.media.speechsynthesis.voiceinformation.gender
  const recommended = voices.find(v => /^en/i.test(v.lang) && /clara/i.test(v.name))
    || voices.find(v => v.lang === 'en-US' && /^Microsoft Zira(?: Desktop)? - English \(United States\)$/.test(v.name));
  const selected = selectNarrationVoice(voices,voice || recommended?.voiceURI || '',narrationLanguage);
  async function speak(text = transcript, slow = false, lesson = true, tour = false) {
    manualHandoff.current = !tour;
    if (!tour) tourStop.current?.();
    stop(); setError(''); lessonAudio.current = lesson; progressCallback.current?.(0);
    if ((!available && !voiceProvider) || muted) {tourStop.current?.();if(!lesson)answerState.current?.('waiting');return;}
    if(narrationLanguage==='ta'&&!/[\u0B80-\u0BFF]/.test(text)){setError('A Tamil explanation is not available for this response. English audio will not play while Tamil is selected.');tourStop.current?.();answerState.current?.('waiting');return;}
    const spoken = speechText(text); if (voiceProvider) {
      const id = speechId.current; const controller = new AbortController(); audioRequest.current = controller; setState('thinking'); setCaption(text);
      try {
        const result = await voiceProvider.synthesize(spoken, slow ? .78 : .88, controller.signal);
        if (id !== speechId.current || !mounted.current) return;
        const track = result instanceof Blob ? {audio:result,cues:[],language:'en-US'} : result;
        if(!matchesLanguage(track.language,narrationLanguage))throw new Error('The voice provider returned a different language.');
        const url = URL.createObjectURL(track.audio); audioUrl.current = url; const audio = new Audio(url); remoteAudio.current = audio;
        lipSync.current.startAudio(audio, track.cues, spoken, track.language); setSyncMode(lipSync.current.mode);
        audio.ontimeupdate = () => {if (id === speechId.current && Number.isFinite(audio.duration) && audio.duration > 0) progressCallback.current?.(audio.currentTime / audio.duration);};
        audio.onwaiting = () => {if (id === speechId.current) lipSync.current.pause();};
        audio.onplaying = () => {if (id === speechId.current) {lipSync.current.resume(); setState('explaining'); speakingCallback.current?.(true);}};
        audio.onended = () => {if (id === speechId.current) {progressCallback.current?.(1); setState('encouraging'); setUnderstood(lesson); lipSync.current.stop(); setSyncMode('idle'); speakingCallback.current?.(false); releaseAudio(); if (tour) narrationEnd.current?.(); else if(!lesson) answerState.current?.('waiting');}};
        audio.onerror = () => {if (id === speechId.current) {stop(); tourStop.current?.(); setError('The configured voice could not play.');}};
        await audio.play();
      } catch(e) {if (id === speechId.current && mounted.current) {stop(); tourStop.current?.(); setError((e as Error).message);}}
      return;
    }
    if (!selected) {tourStop.current?.();if(!lesson)answerState.current?.('waiting'); setError(narrationLanguage==='ta'?'No Tamil voice is installed. Read the Tamil explanation or choose English.':'Choose and preview an English voice first. Your browser does not report voice gender.'); return;}
    const id = speechId.current;
    const speech = new SpeechSynthesisUtterance(spoken);
    utterance.current = speech;
    speech.voice = selected; speech.lang = selected.lang; speech.rate = slow ? .78 : .88; speech.pitch = 1;
    setCaption(text); setUnderstood(false);
    speech.onstart = () => {if (id === speechId.current) {lipSync.current.startBrowser(spoken, speech.rate); setSyncMode(lipSync.current.mode); setState('explaining'); speakingCallback.current?.(true);}};
    speech.onboundary = event => {if (id === speechId.current && event.name === 'word') {progressCallback.current?.(event.charIndex / Math.max(1, spoken.length)); lipSync.current.boundary(spoken,event.charIndex); setSpokenWord({start:event.charIndex,end:event.charIndex+(spoken.slice(event.charIndex).match(/^\S+/)?.[0].length||0)}); setSyncMode(lipSync.current.mode);}};
    speech.onpause = () => {if (id === speechId.current) lipSync.current.pause();};
    speech.onresume = () => {if (id === speechId.current) lipSync.current.resume();};
    speech.onend = () => {if (id === speechId.current) {progressCallback.current?.(1); setState('encouraging'); setUnderstood(lesson); lipSync.current.stop(); setSyncMode('idle'); speakingCallback.current?.(false); utterance.current = null; if (tour) narrationEnd.current?.(); else if(!lesson) answerState.current?.('waiting');}};
    speech.onerror = e => {if (id === speechId.current) {tourStop.current?.();if(!lesson)answerState.current?.('waiting'); lipSync.current.stop(); setSyncMode('idle'); setState('idle'); speakingCallback.current?.(false); if (e.error !== 'canceled' && e.error !== 'interrupted') setError('This voice could not play. Preview another installed voice.');}};
    // Cancellation does not reset the browser-wide paused flag.
    window.speechSynthesis.resume();
    window.speechSynthesis.speak(speech);
  }
  useEffect(() => {
    if(autoNarrate&&!voiceProvider&&(!available||voices.length===0))return;
    if (autoNarrate) void speak(transcript, false, true, true);
    else {
      // Clicking replay during a tour starts a new manual utterance. Do not
      // cancel that utterance when the parent switches the tour flag off.
      if (!manualHandoff.current && (utterance.current || remoteAudio.current || audioRequest.current)) stop();
      manualHandoff.current = false;
    }
    // Start only on a requested tour or a new board step, never on voice-list updates.
  }, [autoNarrate, transcript, equation, stepNumber, narrationLanguage, available, voices.length]);
  useEffect(() => {
    if (!playbackCommand) return;
    if (playbackCommand.action === 'stop') {manualHandoff.current=false; stop(); return;}
    if (playbackCommand.action === 'replay') {void speak(transcript, false, true, true); return;}
    if (playbackCommand.action === 'pause') {
      lipSync.current.pause();
      if (remoteAudio.current) remoteAudio.current.pause();
      else if ('speechSynthesis' in window) window.speechSynthesis.pause();
      setState('paused'); speakingCallback.current?.(false);
    } else {
      lipSync.current.resume();
      if (remoteAudio.current) void remoteAudio.current.play().catch(() => {stop(); tourStop.current?.(); setError('Could not resume audio.');});
      else if ('speechSynthesis' in window) window.speechSynthesis.resume();
      setState('explaining'); speakingCallback.current?.(lessonAudio.current);
    }
  }, [playbackCommand]);
  useEffect(() => {
    if(state!=='explaining'||!lessonAudio.current)return;
    let frame=0,last=0;
    const tick=(now:number)=>{if(now-last>=80){progressCallback.current?.(lipSync.current.progress());last=now;}frame=requestAnimationFrame(tick);};
    frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);
  },[state]);
  useEffect(()=>{if(localAnswer){setReply(localAnswer.text);setMode('Mia');void speak(localAnswer.text,false,false);}},[localAnswer]);
  function simpler() {const slow=narrationLanguage==='ta'?'பரவாயில்லை. ஒரே ஒரு படியை மட்டும் மெதுவாகப் பார்ப்போம். இரு பக்கங்களிலும் ஒரே செயலைச் செய்து சமநிலையைக் காப்போம்.':encouragement.confused;setReply(slow); answerState.current?.('answering'); const full=narrationLanguage==='ta'?`${slow} இந்தப் படி: ${contextTranscript||transcript}`:`${slow} For this step: ${transcript}`;onAnswerText?.(full);void speak(full, true);setState('confused');}
  return <aside className={classroomBoard ? "classroom-teacher" : "teacher-panel"}>
    <div className="row between teacher-heading"><div><span className="eyebrow">{classroomBoard ? "YOUR CLASSROOM" : "YOUR PERSONAL TEACHER"}</span><h2>Mia <span className="pill">Here for you</span></h2></div><button className="icon-button" aria-label={muted ? 'Unmute' : 'Mute'} onClick={() => {tourStop.current?.(); stop(); setMuted(!muted);}}>{muted ? <VolumeX size={19}/> : <Volume2 size={19}/>}</button></div>
    <div className={classroomBoard ? 'classroom-stage' : undefined}>
      {classroomBoard}
      <Avatar writingBoard={writingBoard} teachingGesture={teachingGesture} state={state} speech={lipSync.current} syncMode={syncMode} stepNumber={stepNumber}/>
    </div>
    <div className={classroomBoard ? 'classroom-toolbar' : undefined}>{classroomControls}</div>
    <div className={classroomBoard ? 'classroom-conversation' : undefined}>
    {classroomBoard && <div className="classroom-tabs" aria-label="Explanation view"><button type="button" aria-pressed={explanationTab==='explanation'} onClick={()=>setExplanationTab('explanation')}>Mia’s explanation</button><button type="button" aria-pressed={explanationTab==='transcript'} onClick={()=>setExplanationTab('transcript')}>Lesson transcript</button><button type="button" aria-label={muted?'Unmute':'Mute'} onClick={()=>{tourStop.current?.();stop();setMuted(!muted);}}>{muted?<VolumeX size={16}/>:<Volume2 size={16}/>}</button></div>}
    {classroomBoard && explanationTab==='explanation' && !reply && <div className="chat-reply"><p>{contextTranscript || transcript}</p><span className="tiny">{lessonLabel||'Verified lesson explanation'}</span></div>}
    <div hidden={!!classroomBoard && explanationTab!=='explanation'}>
    {reply && <div className="chat-reply" aria-live="polite"><span className="eyebrow">{mode}</span><p>{reply}</p><button className="text-button" disabled={(!available && !voiceProvider) || muted} onClick={() => {answerState.current?.('answering'); onAnswerText?.(reply); speak(reply, false, false);}}>Read Mia’s response</button></div>}
    </div>
    <form className="classroom-ask" onSubmit={async e => {e.preventDefault(); onInterrupt?.(); tourStop.current?.(); stop(); answerState.current?.('answering'); setState('thinking'); setError(''); const chatId=speechId.current; try {const result = await post<{message: string; mode: string}>('/tutor/chat', {equation, message: `Respond in ${narrationLanguage==='ta'?'Tamil':'English'}. Current step ${stepNumber || 1}: ${contextTranscript || transcript}\nStudent question: ${message}`.slice(0,2000), variable}); if (mounted.current && chatId===speechId.current) {setReply(result.message); setMode(result.mode); onAnswerText?.(result.message,message); setMessage(''); setState('encouraging'); void speak(result.message,false,false);}} catch(e) {if (mounted.current && chatId===speechId.current) {setError((e as Error).message); setState('idle'); answerState.current?.('waiting');}}}}><label htmlFor="chat">{narrationLanguage==='ta'?'மியாவிடம் கேளுங்கள்':'Ask Mia a question'}</label><div className="chat-input"><input id="chat" placeholder={narrationLanguage==='ta'?'இந்தப் படி புரியவில்லை…':'I’m confused about this step…'} value={message} onChange={e => setMessage(e.target.value)} onFocus={() => {if(classroomBoard){onInterrupt?.();stop();} if(state!=='thinking')setState('listening');}} onBlur={() => {if (state === 'listening') setState('idle');}} maxLength={2000} required/><Button type="submit" disabled={state === 'thinking' || !message.trim()}>{state === 'thinking' ? (narrationLanguage==='ta'?'யோசிக்கிறேன்…':'Thinking…') : (narrationLanguage==='ta'?'கேளுங்கள்':'Ask Mia')}<Send size={16}/></Button></div></form>
    <div className="transcript" hidden={!!classroomBoard && explanationTab!=='transcript'} aria-live="polite"><span className="eyebrow">{state === 'explaining' ? 'MIA IS EXPLAINING' : 'LESSON TRANSCRIPT'}</span><p>{state==='explaining' && spokenWord ? <>{caption.slice(0,spokenWord.start)}<mark>{caption.slice(spokenWord.start,spokenWord.end)}</mark>{caption.slice(spokenWord.end)}</> : caption || transcript}</p></div>
    {!writingBoard && <div className="voice-controls"><Button variant="outline" disabled={(!available && !voiceProvider) || muted} onClick={() => speak(`Let’s look at this step together. ${transcript} Take a moment. Does that make sense?`)}><Play size={14}/> Explain / replay</Button><button className="icon-button" aria-label="Pause or resume narration" disabled={(!available && !voiceProvider) || !['explaining', 'paused'].includes(state)} onClick={() => {if (state === 'paused') {lipSync.current.resume(); if (remoteAudio.current) void remoteAudio.current.play().catch(() => setError('Could not resume audio.')); else window.speechSynthesis.resume(); setState('explaining'); speakingCallback.current?.(lessonAudio.current);} else {lipSync.current.pause(); if (remoteAudio.current) remoteAudio.current.pause(); else window.speechSynthesis.pause(); setState('paused'); speakingCallback.current?.(false);}}}><Pause size={15}/></button><button className="icon-button" aria-label="Stop narration" disabled={!available && !voiceProvider} onClick={() => {tourStop.current?.(); stop();}}><Square size={14}/></button></div>}
    <details className="teacher-voice-settings"><summary>Voice settings</summary><label className="tiny">Narration voice<select value={selected?.voiceURI || ''} onChange={e => {tourStop.current?.(); stop(); setVoice(e.target.value);}}><option value="">Choose a voice to preview</option>{voices.filter(v => matchesLanguage(v.lang,narrationLanguage)).map(v => <option value={v.voiceURI} key={v.voiceURI}>{v.name} ({v.lang})</option>)}</select></label>
    <div className="actions"><Button variant="outline" disabled={!selected || muted} onClick={() => speak(narrationLanguage==='ta'?'வணக்கம், நான் மியா. அவசரம் வேண்டாம். கணிதத்தை ஒன்றாகப் படிப்படியாகக் கற்போம்.':'Hi, I’m Mia. It’s completely okay to take your time. We’ll work through the maths together.', false, false)}>Preview voice</Button><Button variant="outline" disabled={!selected} onClick={async () => {try {await api('/settings', {method:'PUT', body:JSON.stringify({voice: selected?.voiceURI || '', muted})}); setError('Voice preference saved.');} catch(e) {setError((e as Error).message);}}}>Save voice</Button></div>
    <p className="tiny">{selected === recommended && recommended ? recommended.name + " is Mia's default voice. " : ''}Preview to check the sound. Voice quality depends on your device; choose the voice you find most comfortable.</p></details>
    {(!available || !voices.some(v => matchesLanguage(v.lang,narrationLanguage))) && <p className="info-box">{narrationLanguage==='ta'?'இந்த உலாவியில் தமிழ் குரல் கிடைக்கவில்லை. தமிழ் உரையைப் படிக்கலாம். Tamil audio requires an installed Tamil voice exposed by your browser; English will not be substituted.':'No English browser voice is available. Captions work without audio. Install an English voice in your system’s speech settings.'}</p>}
    {understood && <p className="info-box">Does that make sense? We can pause here as long as you need.</p>}
    <div className="actions"><Button variant="outline" onClick={simpler}>{narrationLanguage==='ta'?'மெதுவாக விளக்குங்கள்':'Explain more slowly'}</Button>{onNext && <Button onClick={() => {tourStop.current?.(); stop(); onNext();}}>I understand · next step</Button>}</div>

    {error && <p role="status" className="info-box">{error}</p>}
    </div>
  </aside>;
}
