'use client';
import { useEffect, useState } from 'react';
import { Pencil, Volume2 } from 'lucide-react';
import { api } from '@/lib/api';
import type { User } from '@/lib/types';
import { Button } from './ui/button';
export function Settings({user}: {user: User}) {const [muted, setMuted] = useState(false); const [voice, setVoice] = useState(''); const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]); const [status, setStatus] = useState(''); const [ready, setReady] = useState(false); useEffect(() => {api<{muted: boolean; voice: string}>('/settings').then(r => {setMuted(r.muted); setVoice(r.voice); setReady(true);}).catch(e => setStatus(e.message)); if (!('speechSynthesis' in window)) return; const load = () => setVoices(window.speechSynthesis.getVoices()); load(); window.speechSynthesis.addEventListener('voiceschanged', load); return () => window.speechSynthesis.removeEventListener('voiceschanged', load);}, []);
  function scrollToProfile() {const el = document.getElementById('profile-editor'); if (!el) return; el.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start'}); el.classList.add('flash'); setTimeout(() => {el.querySelector('input')?.focus({preventScroll: true}); setTimeout(() => el.classList.remove('flash'), 1600);}, 450);}
  return <div className="stack">
    <section className="card settings-profile-card"><div className="profile-identity"><span className="user-avatar large">{user.name.slice(0, 1)}</span><div><h2>{user.name}</h2><p>{user.email}</p><p className="tiny">Math Explorer · Student</p></div></div><Button type="button" variant="outline" onClick={scrollToProfile}><Pencil size={15}/> Edit</Button></section>
    <section className="card"><h2>Preferences</h2>
      <form onSubmit={async e => {e.preventDefault(); setStatus('Saving…'); try {await api('/settings', {method: 'PUT', body: JSON.stringify({muted, voice})}); setStatus('Preferences saved. They will apply when you reopen a lesson.');} catch(e) {setStatus((e as Error).message);}}}>
        <div className="pref-row"><div className="pref-text"><strong><Volume2 size={15}/> Narration</strong><span>Hear questions and instructions read aloud</span></div><label className="switch"><input type="checkbox" checked={!muted} onChange={e => setMuted(!e.target.checked)} aria-label="Narration"/><span aria-hidden="true"/></label></div>
        <div className="pref-row"><div className="pref-text"><strong>Voice</strong><span>Choose the narration voice</span></div><select value={voice} onChange={e => setVoice(e.target.value)} aria-label="Preferred voice"><option value="">Browser default</option>{voices.map(v => <option value={v.voiceURI} key={v.voiceURI}>{v.name}</option>)}</select></div>
        <div className="row end"><Button disabled={!ready}>Save preferences</Button></div>
        <p role="status">{status}</p>
      </form>
    </section>
  </div>;
}
