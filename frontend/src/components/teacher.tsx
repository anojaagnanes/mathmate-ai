'use client';
import dynamic from 'next/dynamic';
import { useEffect, useRef, useState } from 'react';
import { Pause, Play, Square, Volume2, VolumeX, Send } from 'lucide-react';
import { LipSyncClock, type SyncMode } from '@/lib/lip-sync';
import type { VoiceProvider } from '@/lib/voice-provider';
import { api, post } from '@/lib/api';
import { encouragement, type TeacherState } from '@/lib/teacher-state';
import { Button } from './ui/button';
const Avatar = dynamic(() => import('./teacher-avatar'), {ssr: false, loading: () => <div className="teacher-3d avatar-fallback">Opening Mia’s studio…</div>});
export function Teacher({equation, transcript, reaction, onSpeaking, onNext, voiceProvider, stepNumber, variable}: {
  variable?: string; stepNumber?: number; voiceProvider?: VoiceProvider; equation: string; transcript: string; reaction?: 'correct' | 'incorrect'; onSpeaking?: (speaking: boolean) => void; onNext?: () => void;
}) {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voice, setVoice] = useState('');
  const [muted, setMuted] = useState(false);
  const lipSync = useRef(new LipSyncClock());
  const [syncMode, setSyncMode] = useState<SyncMode>('idle');
  const lessonAudio = useRef(false);
  const [state, setState] = useState<TeacherState>('idle');
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState('Hi, I’m Mia. Take your time — every small step counts.');
  const [mode, setMode] = useState('Local tutor · development mode');
  const [error, setError] = useState('');
  const [available, setAvailable] = useState(false);
  const [caption, setCaption] = useState('');
  const [spokenWord, setSpokenWord] = useState<{start:number;end:number}|null>(null);
  const [understood, setUnderstood] = useState(false);
  const speechId = useRef(0);
  const mounted = useRef(true);
  const speakingCallback = useRef(onSpeaking);
  speakingCallback.current = onSpeaking;
  const remoteAudio = useRef<HTMLAudioElement | null>(null);
  const audioUrl = useRef<string | null>(null);
  const audioRequest = useRef<AbortController | null>(null);
  function releaseAudio() {audioRequest.current?.abort(); remoteAudio.current?.pause(); remoteAudio.current = null; if (audioUrl.current) URL.revokeObjectURL(audioUrl.current); audioUrl.current = null;}
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);
  function stop() {
    speechId.current++; lipSync.current.stop(); releaseAudio();
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    utterance.current = null; setSpokenWord(null); setSyncMode('idle'); setState('idle'); speakingCallback.current?.(false);
  }
  useEffect(() => {
    mounted.current = true;
    api<{configured: boolean}>('/tutor/status').then(s => {if (mounted.current) setMode(s.configured ? 'Meta provider configured' : 'Local tutor · development mode');}).catch(() => {});
    if (!('speechSynthesis' in window)) return () => {mounted.current = false; speechId.current++; lipSync.current.stop(); releaseAudio(); speakingCallback.current?.(false);};
    setAvailable(true);
    const update = () => setVoices(window.speechSynthesis.getVoices());
    update(); window.speechSynthesis.addEventListener('voiceschanged', update);
    api<{muted: boolean; voice: string}>('/settings').then(s => {if (mounted.current) {setMuted(s.muted); setVoice(s.voice);}}).catch(() => {});
    return () => {mounted.current = false; speechId.current++; lipSync.current.stop(); releaseAudio(); window.speechSynthesis.cancel(); speakingCallback.current?.(false); window.speechSynthesis.removeEventListener('voiceschanged', update);};
  }, []);
  useEffect(() => {stop(); setCaption(transcript); setUnderstood(false);}, [transcript]); // Each new board step cancels stale narration.
  useEffect(() => {if (reaction) {stop(); setState(reaction); setReply(encouragement[reaction]);}}, [reaction]);
  // Microsoft documents Zira as female; this is a verified provider mapping, not a gender guess.
  // https://learn.microsoft.com/en-us/uwp/api/windows.media.speechsynthesis.voiceinformation.gender
  const recommended = voices.find(v => v.lang === 'en-US' && /^Microsoft Zira(?: Desktop)? - English \(United States\)$/.test(v.name));
  const selected = voices.find(v => v.voiceURI === voice && /^en\b/i.test(v.lang)) || recommended;
  async function speak(text = transcript, slow = false, lesson = true) {
    stop(); setError(''); lessonAudio.current = lesson;
    if ((!available && !voiceProvider) || muted) return;
    if (voiceProvider) {
      const id = speechId.current; const controller = new AbortController(); audioRequest.current = controller; setState('thinking'); setCaption(text);
      try {
        const result = await voiceProvider.synthesize(text, slow ? .78 : .88, controller.signal);
        if (id !== speechId.current || !mounted.current) return;
        const track = result instanceof Blob ? {audio:result,cues:[],language:'en-US'} : result;
        const url = URL.createObjectURL(track.audio); audioUrl.current = url; const audio = new Audio(url); remoteAudio.current = audio;
        lipSync.current.startAudio(audio, track.cues, text, track.language); setSyncMode(lipSync.current.mode);
        audio.onwaiting = () => {if (id === speechId.current) lipSync.current.pause();};
        audio.onplaying = () => {if (id === speechId.current) {lipSync.current.resume(); setState('explaining'); speakingCallback.current?.(lesson);}};
        audio.onended = () => {if (id === speechId.current) {setState('encouraging'); setUnderstood(lesson); lipSync.current.stop(); setSyncMode('idle'); speakingCallback.current?.(false); releaseAudio();}};
        audio.onerror = () => {if (id === speechId.current) {stop(); setError('The configured voice could not play.');}};
        await audio.play();
      } catch(e) {if (id === speechId.current && mounted.current) {stop(); setError((e as Error).message);}}
      return;
    }
    if (!selected) {setError('Choose and preview an English voice first. Your browser does not report voice gender.'); return;}
    const id = speechId.current;
    const speech = new SpeechSynthesisUtterance(text);
    utterance.current = speech;
    speech.voice = selected; speech.lang = selected.lang; speech.rate = slow ? .78 : .88; speech.pitch = 1;
    setCaption(text); setUnderstood(false);
    speech.onstart = () => {if (id === speechId.current) {lipSync.current.startBrowser(text, speech.rate); setSyncMode(lipSync.current.mode); setState('explaining'); speakingCallback.current?.(lesson);}};
    speech.onboundary = event => {if (id === speechId.current && event.name === 'word') {lipSync.current.boundary(text,event.charIndex); setSpokenWord({start:event.charIndex,end:event.charIndex+(text.slice(event.charIndex).match(/^\S+/)?.[0].length||0)}); setSyncMode(lipSync.current.mode);}};
    speech.onpause = () => {if (id === speechId.current) lipSync.current.pause();};
    speech.onresume = () => {if (id === speechId.current) lipSync.current.resume();};
    speech.onend = () => {if (id === speechId.current) {setState('encouraging'); setUnderstood(lesson); lipSync.current.stop(); setSyncMode('idle'); speakingCallback.current?.(false); utterance.current = null;}};
    speech.onerror = e => {if (id === speechId.current) {lipSync.current.stop(); setSyncMode('idle'); setState('idle'); speakingCallback.current?.(false); if (e.error !== 'canceled' && e.error !== 'interrupted') setError('This voice could not play. Preview another installed voice.');}};
    window.speechSynthesis.speak(speech);
  }
  function simpler() {setReply(encouragement.confused); void speak(`${encouragement.confused} For this step: ${transcript}`, true); setState('confused');}
  return <aside className="teacher-panel">
    <div className="row between"><div><span className="eyebrow">YOUR PERSONAL TEACHER</span><h2>Mia <span className="pill">Here for you</span></h2></div><button className="icon-button" aria-label={muted ? 'Unmute' : 'Mute'} onClick={() => {stop(); setMuted(!muted);}}>{muted ? <VolumeX size={19}/> : <Volume2 size={19}/>}</button></div>
    <Avatar state={state} speech={lipSync.current} syncMode={syncMode} stepNumber={stepNumber}/>
    <p className="tiny">Interactive 3D human · browser narration</p>
    <div className="transcript" aria-live="polite"><span className="eyebrow">{state === 'explaining' ? 'MIA IS EXPLAINING' : 'LESSON TRANSCRIPT'}</span><p>{state==='explaining' && spokenWord ? <>{caption.slice(0,spokenWord.start)}<mark>{caption.slice(spokenWord.start,spokenWord.end)}</mark>{caption.slice(spokenWord.end)}</> : caption || transcript}</p></div>
    <div className="voice-controls"><Button variant="outline" disabled={(!available && !voiceProvider) || muted} onClick={() => speak(`Let’s look at this step together. ${transcript} Take a moment. Does that make sense?`)}><Play size={14}/> Explain / replay</Button><button className="icon-button" aria-label="Pause or resume narration" disabled={(!available && !voiceProvider) || !['explaining', 'paused'].includes(state)} onClick={() => {if (state === 'paused') {lipSync.current.resume(); if (remoteAudio.current) void remoteAudio.current.play().catch(() => setError('Could not resume audio.')); else window.speechSynthesis.resume(); setState('explaining'); speakingCallback.current?.(lessonAudio.current);} else {lipSync.current.pause(); if (remoteAudio.current) remoteAudio.current.pause(); else window.speechSynthesis.pause(); setState('paused'); speakingCallback.current?.(false);}}}><Pause size={15}/></button><button className="icon-button" aria-label="Stop narration" disabled={!available && !voiceProvider} onClick={stop}><Square size={14}/></button></div>
    <label className="tiny">Narration voice<select value={selected?.voiceURI || ''} onChange={e => {stop(); setVoice(e.target.value);}}><option value="">Choose a voice to preview</option>{voices.filter(v => /^en\b/i.test(v.lang)).map(v => <option value={v.voiceURI} key={v.voiceURI}>{v.name} ({v.lang})</option>)}</select></label>
    <div className="actions"><Button variant="outline" disabled={!selected || muted} onClick={() => speak('Hi, I’m Mia. It’s completely okay to take your time. We’ll work through the maths together.', false, false)}>Preview voice</Button><Button variant="outline" disabled={!selected} onClick={async () => {try {await api('/settings', {method:'PUT', body:JSON.stringify({voice: selected?.voiceURI || '', muted})}); setError('Voice preference saved.');} catch(e) {setError((e as Error).message);}}}>Save voice</Button></div>
    <p className="tiny">{selected === recommended && recommended ? 'Microsoft Zira is selected: Microsoft identifies this voice as female. ' : ''}Preview to check the sound. Voice quality depends on your device; choose the voice you find most comfortable.</p>
    {(!available || !voices.some(v => /^en\b/i.test(v.lang))) && <p className="info-box">No English browser voice is available. Captions work without audio. Install an English voice in your system’s speech settings, or configure a voice provider with your developer.</p>}
    {understood && <p className="info-box">Does that make sense? We can pause here as long as you need.</p>}
    <div className="actions"><Button variant="outline" onClick={simpler}>Explain more slowly</Button>{onNext && <Button onClick={() => {stop(); onNext();}}>I understand · next step</Button>}</div>
    <hr/><div className="chat-reply" aria-live="polite"><span className="eyebrow">{mode}</span><p>{reply}</p><button className="text-button" disabled={(!available && !voiceProvider) || muted} onClick={() => speak(reply, false, false)}>Read Mia’s response</button></div>
    <form onSubmit={async e => {e.preventDefault(); stop(); setState('thinking'); setError(''); try {const result = await post<{message: string; mode: string}>('/tutor/chat', {equation, message, variable}); if (mounted.current) {setReply(result.message); setMode(result.mode); setMessage(''); setState('encouraging');}} catch(e) {if (mounted.current) {setError((e as Error).message); setState('idle');}}}}><label className="sr-only" htmlFor="chat">Ask your tutor</label><div className="chat-input"><input id="chat" placeholder="I’m confused about this step…" value={message} onChange={e => setMessage(e.target.value)} onFocus={() => {if (!['explaining','thinking'].includes(state)) setState('listening');}} onBlur={() => {if (state === 'listening') setState('idle');}} maxLength={2000} required/><button className="icon-button" aria-label="Send message" disabled={state === 'thinking'}><Send size={17}/></button></div></form>
    {error && <p role="status" className="info-box">{error}</p>}
  </aside>;
}
