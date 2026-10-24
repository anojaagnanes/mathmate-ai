export const visemes = ['sil','PP','FF','TH','DD','kk','CH','SS','nn','RR','aa','E','I','O','U'] as const;
export type Viseme = typeof visemes[number];
export type VisemeCue = {start: number; end: number; viseme: Viseme};
export type SpeechTrack = {audio: Blob; cues: VisemeCue[]; language: string};
export type SyncMode = 'idle' | 'provider' | 'word' | 'estimated';

export function validateCues(value: unknown): VisemeCue[] {
  if (!Array.isArray(value) || value.length > 20000) throw new Error('Invalid viseme cue list.');
  let end = 0;
  return value.map(c => {
    if (!c || !Number.isFinite(c.start) || !Number.isFinite(c.end) || c.start < end || c.end <= c.start || c.end > 600 || !visemes.includes(c.viseme)) throw new Error('Viseme cues must be ordered, non-overlapping intervals in seconds.');
    end = c.end;
    return {start:c.start, end:c.end, viseme:c.viseme};
  });
}

// English spelling approximation, NOT a pronunciation dictionary or forced alignment.
// Kept separate from provider cues so another language never receives English guesses.
export function estimateEnglish(text: string, rate = .88): VisemeCue[] {
  const digits=['zero','one','two','three','four','five','six','seven','eight','nine'];
  text=text.replace(/\d/g,d=>` ${digits[Number(d)]} `);
  const sounds: Record<string, Viseme> = {p:'PP',b:'PP',m:'PP',f:'FF',v:'FF',t:'DD',d:'DD',k:'kk',g:'kk',c:'kk',s:'SS',z:'SS',n:'nn',l:'nn',r:'RR',a:'aa',e:'E',i:'I',o:'O',u:'U',w:'U',y:'I',h:'aa'};
  const units = text.toLowerCase().match(/th|sh|ch|[a-z]|[^a-z]+/g) || [];
  let time = 0;
  return units.map(unit => {
    const viseme: Viseme = unit === 'th' ? 'TH' : ['sh','ch'].includes(unit) ? 'CH' : sounds[unit] || 'sil';
    const duration = (viseme === 'sil' ? /[,.!?;:]/.test(unit) ? .2 : .045 : .065) / Math.max(.5,rate);
    const cue = {start: time, end: time+duration, viseme}; time += duration; return cue;
  });
}

export function sampleCues(cues: VisemeCue[], time: number): Partial<Record<Viseme,number>> {
  let lo = 0, hi = cues.length-1;
  while (lo <= hi) {const mid = (lo+hi) >>> 1; const c = cues[mid];
    if (time < c.start) hi=mid-1; else if(time >= c.end) lo=mid+1;
    else {if(c.viseme === 'sil') return {}; const ramp=Math.min(.035,(c.end-c.start)/3); return {[c.viseme]:Math.min(1,(time-c.start)/ramp,(c.end-time)/ramp)};}
  }
  return {};
}

/** Mutable playback clock read by R3F; no React updates on every animation frame. */
export class LipSyncClock {
  mode: SyncMode = 'idle';
  private cues: VisemeCue[] = [];
  private origin = 0;
  private pauseAt: number | null = null;
  private audio: HTMLAudioElement | null = null;
  private running = false;
  private rate = .88;
  private wordPosition=0;
  private textLength=0;
  startBrowser(text: string, rate: number, now = performance.now()) {this.stop();this.rate=rate;this.textLength=text.length;this.cues=estimateEnglish(text,rate);this.origin=now;this.mode='estimated';this.running=true;}
  boundary(text: string, charIndex: number, now = performance.now()) {
    if(!this.running || this.audio) return;
    const word=text.slice(charIndex).match(/^\S+/)?.[0] || '';
    this.wordPosition=Math.max(this.wordPosition,charIndex);this.cues=estimateEnglish(word,this.rate);this.origin=now;this.mode='word';
  }
  startAudio(audio: HTMLAudioElement, cues: VisemeCue[], text: string, language: string) {
    this.stop();this.audio=audio;this.cues=validateCues(cues);this.mode=cues.length?'provider':'estimated';
    if(!cues.length && /^en\b/i.test(language))this.cues=estimateEnglish(text);
    this.running=true;
  }
  pause(now=performance.now()) {if(this.pauseAt===null)this.pauseAt=now;}
  resume(now=performance.now()) {if(this.pauseAt!==null){this.origin+=now-this.pauseAt;this.pauseAt=null;}}
  stop(){this.running=false;this.audio=null;this.cues=[];this.pauseAt=null;this.wordPosition=0;this.textLength=0;this.mode='idle';}
  progress(now=performance.now()) {
    if(!this.running)return 0;
    if(this.mode==='word')return Math.min(1,this.wordPosition/Math.max(1,this.textLength));
    const duration=this.audio && Number.isFinite(this.audio.duration)?this.audio.duration:this.cues.at(-1)?.end || 1;
    const time=this.audio?this.audio.currentTime:((this.pauseAt??now)-this.origin)/1000;
    return Math.max(0,Math.min(1,time/Math.max(.01,duration)));
  }
  sample(now=performance.now()) {
    if(!this.running || this.pauseAt!==null || (this.audio && (this.audio.paused || this.audio.ended || this.audio.readyState<3)))return {};
    return sampleCues(this.cues,this.audio?this.audio.currentTime:(now-this.origin)/1000);
  }
}
