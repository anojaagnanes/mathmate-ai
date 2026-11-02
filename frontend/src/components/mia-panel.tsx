'use client';
import { useEffect } from 'react';
import { useMiaSession } from '@/lib/mia-session';
import { useMiaVoice } from '@/lib/mia-voice';
import { MiaControls } from './mia-controls';
import { MiaWhiteboard } from './mia-whiteboard';
import { Button } from './ui/button';

export function MiaPanel({ question, compact = false, hidePractice = false }: { question?: string; compact?: boolean; hidePractice?: boolean }) {
  const { language, switchLanguage, turn, busy, error, ask } = useMiaSession(question || '', 'en');
  const voice = useMiaVoice((turn?.language as 'en' | 'ta') || language, turn?.voice_rate || 0.88);
  const followups = hidePractice ? (turn?.followups || []).filter(f => !/practic|பயிற்சி|easier|harder/i.test(f)) : (turn?.followups || []);

  useEffect(() => {
    if (turn?.reply && !voice.muted) voice.speak(turn.reply, (turn?.voice_rate || 0.88) < 0.8);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turn?.reply]);

  useEffect(() => {
    if (voice.heard) void ask(voice.heard, { equation: question });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [voice.heard]);

  return (
    <section className="mia-panel" aria-label="Mia tutor">
      <div className="row between">
        <span className="eyebrow">MIA · YOUR TUTOR</span>
        <div className="row">
          <Button variant="outline" disabled={voice.listening} onClick={voice.listening ? voice.stopListening : voice.listen}>
            {voice.listening ? 'Stop' : 'Speak'}
          </Button>
          <Button variant="outline" onClick={() => voice.setMuted(!voice.muted)}>{voice.muted ? 'Unmute' : 'Mute'}</Button>
        </div>
      </div>
      {turn && (
        <>
          <p className="mia-reply">{turn.reply}</p>
          <div className="mia-plan" aria-label="Mia plan">{turn.plan.map((p, i) => <span key={i}>{p}</span>)}</div>
          {turn.whiteboard.length > 0 && !compact && (
            <MiaWhiteboard items={turn.whiteboard} step={0} playing={voice.speaking} diagram={turn.verified_math?.diagram || undefined} />
          )}
          {turn.practice && !hidePractice && <p className="tiny">Practice: {turn.practice.equation}</p>}
        </>
      )}
      <MiaControls
        language={language}
        busy={busy}
        followups={followups}
        onLanguage={switchLanguage}
        onAsk={(msg, opts) => void ask(msg, { equation: question, ...opts })}
      />
      {(error || voice.error) && <p role="status" className="info-box">{error || voice.error}</p>}
    </section>
  );
}
