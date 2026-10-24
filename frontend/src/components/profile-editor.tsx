'use client';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { User } from '@/lib/types';
import { Button } from './ui/button';

export function ProfileEditor({user, onUpdate}: {user: User; onUpdate: (user: User) => void}) {
  const [name, setName] = useState(user.name);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  return <section className="card settings-card"><span className="eyebrow">YOUR PROFILE</span><h2>What should we call you?</h2><form onSubmit={async event => {
    event.preventDefault(); setBusy(true); setStatus('');
    try {onUpdate(await api<User>('/me', {method: 'PUT', body: JSON.stringify({name: name.trim()})})); setStatus('Your name has been updated.');}
    catch (error) {setStatus((error as Error).message);}
    finally {setBusy(false);}
  }}><label>Display name<input value={name} onChange={event => setName(event.target.value)} maxLength={80} autoComplete="name" required/></label><label>Email address<input value={user.email} type="email" readOnly/></label><p className="tiny">Email changes and password recovery are not available in this MVP.</p><Button disabled={busy || !name.trim()}>{busy ? 'Saving…' : 'Save profile'}</Button><p role="status">{status}</p></form></section>;
}
