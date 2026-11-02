import { useCallback, useEffect, useRef, useState } from 'react';
import { matchesLanguage, selectNarrationVoice, speechText } from './teaching-language';
import type { MiaLanguage } from './mia-session';

export function useMiaVoice(language: MiaLanguage, voiceRate = 0.88) {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceURI, setVoiceURI] = useState('');
  const [muted, setMuted] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState('');
  const [listening, setListening] = useState(false);
  const [heard, setHeard] = useState('');
  const recog = useRef<{ stop?: () => void } | null>(null);

  useEffect(() => {
    if (!('speechSynthesis' in window)) return;
    const update = () => setVoices(window.speechSynthesis.getVoices());
    update();
    window.speechSynthesis.addEventListener('voiceschanged', update);
    return () => {window.speechSynthesis.removeEventListener('voiceschanged', update); if ('speechSynthesis' in window) window.speechSynthesis.cancel(); try {recog.current?.stop?.();} catch {}};
  }, []);

  const selected = selectNarrationVoice(voices, voiceURI, language);

  const stop = useCallback(() => {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  const speak = useCallback((text: string, slow = false) => {
    setError('');
    if (muted || !('speechSynthesis' in window)) return;
    if (language === 'ta' && !/[\u0b80-\u0bff]/.test(text)) {
      setError('Tamil audio needs Tamil script. Showing captions instead.');
      return;
    }
    if (!selected) {
      setError(language === 'ta' ? 'No Tamil voice installed.' : 'No English voice available.');
      return;
    }
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(speechText(text));
    u.voice = selected;
    u.lang = selected.lang;
    u.rate = slow ? 0.65 : voiceRate;
    u.onstart = () => setSpeaking(true);
    u.onend = () => setSpeaking(false);
    u.onerror = e => {
      setSpeaking(false);
      if (e.error !== 'canceled' && e.error !== 'interrupted') setError('Voice could not play.');
    };
    window.speechSynthesis.resume();
    window.speechSynthesis.speak(u);
  }, [muted, language, selected, voiceRate]);

  const listen = useCallback(() => {
    setError('');
    setHeard('');
    const SR = (window as unknown as { SpeechRecognition?: new () => unknown; webkitSpeechRecognition?: new () => unknown }).SpeechRecognition
      || (window as unknown as { webkitSpeechRecognition?: new () => unknown }).webkitSpeechRecognition;
    if (!SR) {
      setError('Voice input is not supported here. Type your question.');
      return;
    }
    try {
      const r = new SR() as unknown as {
        lang: string; interimResults: boolean; maxAlternatives: number;
        onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
        onerror: ((e: { error: string }) => void) | null;
        onend: (() => void) | null;
        start: () => void; stop: () => void;
      };
      recog.current = r;
      r.lang = language === 'ta' ? 'ta-IN' : 'en-US';
      r.interimResults = false;
      r.maxAlternatives = 1;
      setListening(true);
      r.onresult = e => {
        const t = e.results?.[0]?.[0]?.transcript || '';
        setHeard(t);
        setListening(false);
      };
      r.onerror = e => {
        setListening(false);
        if (e.error !== 'aborted') setError('Could not hear you. Type instead.');
      };
      r.onend = () => setListening(false);
      r.start();
    } catch {
      setListening(false);
      setError('Voice input failed. Type instead.');
    }
  }, [language]);

  const stopListening = useCallback(() => {
    try { recog.current?.stop?.(); } catch { /* noop */ }
    setListening(false);
  }, []);

  return { voices: voices.filter(v => matchesLanguage(v.lang, language)), voiceURI, setVoiceURI, muted, setMuted, speaking, speak, stop, error, listening, listen, stopListening, heard };
}
