'use client';
import { useState } from 'react';
import { Button } from './ui/button';
import type { MiaLanguage } from '@/lib/mia-session';

export function MiaControls({ language, busy, followups, onAsk, onLanguage }: {
  language: MiaLanguage; busy: boolean; followups: string[];
  onAsk: (message: string, opts?: { slow?: boolean; method?: 'default' | 'alternative' | 'visual' }) => void;
  onLanguage: (lang: MiaLanguage) => void;
}) {
  const [text, setText] = useState('');
  return (
    <div className="mia-controls">
      <div className="row">
        <label className="example-language">Language
          <select aria-label="Mia language" value={language} onChange={e => onLanguage(e.target.value as MiaLanguage)}>
            <option value="en">English</option>
            <option value="ta">தமிழ்</option>
          </select>
        </label>
        <Button variant="outline" disabled={busy} onClick={() => onAsk(language === 'ta' ? 'மெதுவாக விளக்குங்கள்' : 'Explain slowly', { slow: true })}>Slow</Button>
        <Button variant="outline" disabled={busy} onClick={() => onAsk(language === 'ta' ? 'மீண்டும் சொல்லுங்கள்' : 'Repeat this step')}>Repeat</Button>
        <Button variant="outline" disabled={busy} onClick={() => onAsk(language === 'ta' ? 'வேறு முறையில் விளக்குங்கள்' : 'Show another method', { method: 'alternative' })}>Another method</Button>
      </div>
      <form className="classroom-ask" onSubmit={e => { e.preventDefault(); if (text.trim()) { onAsk(text.trim()); setText(''); } }}>
        <div className="chat-input">
          <input aria-label="Ask Mia" placeholder={language === 'ta' ? 'மியாவிடம் கேளுங்கள்…' : 'Ask Mia…'} value={text} onChange={e => setText(e.target.value)} maxLength={2000} />
          <Button type="submit" disabled={busy || !text.trim()}>{busy ? 'Thinking…' : 'Ask'}</Button>
        </div>
      </form>
      {followups.length > 0 && (
        <div className="row wrap" aria-label="Suggested follow-ups">
          {followups.slice(0, 3).map((f, i) => (
            <Button key={i} variant="outline" disabled={busy} onClick={() => onAsk(f)}>{f}</Button>
          ))}
        </div>
      )}
    </div>
  );
}
