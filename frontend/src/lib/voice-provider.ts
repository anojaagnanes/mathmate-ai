import {validateCues, type SpeechTrack} from './lip-sync';
/** Optional server-backed narration. No service is configured or paid API enabled. */
export interface VoiceProvider {
  label: string;
  synthesize(text: string, rate: number, signal: AbortSignal): Promise<Blob | SpeechTrack>;
}

/** Supply your own authenticated same-origin server route. Keep vendor keys server-side. */
export class ServerVoiceProvider implements VoiceProvider {
  constructor(public label: string, private endpoint: string, private voiceId: string) {
    if (!endpoint.startsWith('/') || endpoint.startsWith('//')) throw new Error('Voice endpoint must be same-origin.');
  }
  async synthesize(text: string, rate: number, signal: AbortSignal) {
    const response = await fetch(this.endpoint, {method: 'POST', credentials: 'include', signal,
      headers: {'Content-Type': 'application/json', 'X-MathMate-Client': 'web'},
      body: JSON.stringify({text, rate, voice: this.voiceId})});
    if (!response.ok) throw new Error('Voice provider is unavailable. Please use captions or a browser voice.');
    if (response.headers.get('content-type')?.includes('application/json')) {
      const payload = await response.json();
      if (typeof payload.audioBase64 !== 'string' || payload.audioBase64.length > 28 * 1024 * 1024 || !['audio/wav','audio/mpeg','audio/ogg','audio/mp4'].includes(payload.mimeType) || typeof payload.language !== 'string') throw new Error('Invalid timed speech response.');
      const cues = validateCues(payload.cues);
      const audio = new Blob([Uint8Array.from(atob(payload.audioBase64), c => c.charCodeAt(0))], {type:payload.mimeType});
      return {audio, cues, language:payload.language};
    }
    const audio = await response.blob();
    if (!audio.type.startsWith('audio/') || audio.size > 20 * 1024 * 1024) throw new Error('Voice provider returned invalid audio.');
    return audio;
  }
}
