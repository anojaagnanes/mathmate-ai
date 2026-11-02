import { useCallback, useEffect, useRef, useState } from 'react';
import { api, post } from './api';
import type { Solution } from './types';

export type MiaLanguage = 'en' | 'ta';
export type MiaIntent = string;
export type WhiteboardItem = { equation: string; latex?: string | null; diagram?: Solution['diagram'] };
export type MiaTurn = {
  reply: string; language: string; mode: string; intent: MiaIntent; plan: string[];
  verified_math: Solution | null; whiteboard: WhiteboardItem[]; followups: string[];
  practice: { equation: string; hint?: string } | null; real_world: string | null;
  voice_rate: number; provider_mode: string;
};

export function useMiaSession(initialQuestion = '', initialLanguage: MiaLanguage = 'en') {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [language, setLanguage] = useState<MiaLanguage>(initialLanguage);
  const [turn, setTurn] = useState<MiaTurn | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<{ role: string; message: string }[]>([]);
  const creating = useRef(false);

  const ensureSession = useCallback(async (question = initialQuestion, lang = language) => {
    if (sessionId) return sessionId;
    if (creating.current) return null;
    creating.current = true;
    try {
      const s = await post<{ id: string; language: string }>('/tutor/session', { language: lang, mode: 'classroom', question });
      setSessionId(s.id);
      return s.id;
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      creating.current = false;
    }
  }, [sessionId, initialQuestion, language]);

  useEffect(() => { void ensureSession(); }, [ensureSession]);

  const ask = useCallback(async (message: string, opts: { equation?: string; slow?: boolean; method?: 'default' | 'alternative' | 'visual'; step_index?: number } = {}) => {
    const id = sessionId || (await ensureSession(opts.equation || initialQuestion));
    if (!id) return null;
    setBusy(true);
    setError('');
    try {
      const result = await post<MiaTurn>('/tutor/turn', {
        session_id: id, message, equation: opts.equation || '', language,
        slow: !!opts.slow, method: opts.method, step_index: opts.step_index,
      });
      setTurn(result);
      setHistory(h => [...h.slice(-19), { role: 'user', message }, { role: 'mia', message: result.reply }]);
      return result;
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      setBusy(false);
    }
  }, [sessionId, ensureSession, initialQuestion, language]);

  const switchLanguage = useCallback(async (lang: MiaLanguage) => {
    setLanguage(lang);
    if (sessionId) {
      try {
        await api('/tutor/session/' + sessionId + '/history');
      } catch { /* history is best-effort; language is local-first */ }
    }
  }, [sessionId]);

  return { sessionId, language, switchLanguage, turn, busy, error, history, ask, ensureSession };
}
