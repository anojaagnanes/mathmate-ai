'use client';
import { useEffect, useState } from 'react';
import { ArrowRight, Play, ShieldCheck } from 'lucide-react';
import { api, post } from '@/lib/api';
import { MathText } from '@/components/math';
import { Button } from '@/components/ui/button';

type Drill = {number: number; equation: string; hint: string; difficulty: number; kind: string; steps?: string[]};
type ExampleStep = {equation: string; explanation: string};
type Teaching = {equation: string; answer: string; hint: string};
type Verdict = {mastered: boolean; accuracy_before: number; accuracy_after: number; drills: number; replans: number; message: string; teaching: Teaching[]};
type Mission = {id: string; goal: string; briefing: string | null; topic: string; error: string | null; state: string; difficulty: number;
  drills_done: number; consecutive: number; exit_wins: number; max_drills: number;
  example: {equation: string; answer: string; steps: ExampleStep[]; verified: boolean} | null;
  current: Drill | null; trace: string[]; verdict: Verdict | null};
type Turn = {correct: boolean; message: string; cheer: string | null; consecutive: number; drills_done: number; difficulty: number; state: string; current: Drill | null; trace: string[]; verdict: Mission['verdict']};

export function Mission() {
  const [mission, setMission] = useState<Mission | null>(null);
  const [started, setStarted] = useState(false);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
  const [cheer, setCheer] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {let active = true;
    api<Mission>('/mission/current').then(m => {if (active) {setMission(m); setStarted(true);}}).catch(() => {if (active) setStarted(false);});
    return () => {active = false;};}, []);

  async function start() {setBusy(true); setError(''); setCheer(''); try {setMission(await post<Mission>('/mission/start')); setStarted(true);} catch (e) {setError((e as Error).message);} finally {setBusy(false);}}
  async function submit() {if (!mission || !answer.trim()) return; setBusy(true); setError(''); setFeedback('');
    try {const turn = await post<Turn>(`/mission/${mission.id}/answer`, {answer: answer.trim()});
      setMission({...mission, consecutive: turn.consecutive, drills_done: turn.drills_done, difficulty: turn.difficulty, state: turn.state, current: turn.current, trace: turn.trace, verdict: turn.verdict});
      setFeedback(turn.message); setAnswer(''); if (turn.cheer) setCheer(turn.cheer);
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}}

  if (!started || !mission) return <section className="card"><span className="eyebrow">✦ MIA AUTOPILOT · FULLY AUTONOMOUS</span>
    <h2>One button. Mia runs the mission.</h2>
    <p>She studies your mistake history, diagnoses your weakest point, teaches one worked example, drills you adaptively, and declares mastery with before-and-after proof. Every answer is graded by the verified maths engine — never by guesswork.</p>
    {error && <p role="alert" className="error-box">{error}</p>}
    <Button onClick={start} disabled={busy}>{busy ? 'Planning your mission…' : 'Start my mission'} <Play size={16}/></Button></section>;

  if (mission.state === 'complete' && mission.verdict) {const v = mission.verdict;
    return <div className="stack"><div className={v.mastered ? 'success-box' : 'info-box'}><h3>{v.mastered ? '✓ Mastery achieved.' : 'Mission complete — not yet mastered.'}</h3><p>{v.message}</p>{cheer && <p>Mia: {cheer}</p>}</div>
    <section className="card"><span className="eyebrow">BEFORE → AFTER</span><h2>Your proof of progress.</h2>
      <div className="stats"><article><strong>{Math.round(v.accuracy_before * 100)}% → {Math.round(v.accuracy_after * 100)}%</strong><span>accuracy</span></article>
      <article><strong>{v.drills}</strong><span>drills completed</span></article><article><strong>{v.replans}</strong><span>agent re-plans</span></article></div>
      <div className="row" style={{marginTop: 20}}><Button onClick={() => {setMission(null); setStarted(false); setFeedback(''); setCheer('');}}>Start next mission <ArrowRight size={16}/></Button></div></section>
    {v.teaching.length > 0 && <section className="card"><span className="eyebrow">STUDY THESE VERIFIED ANSWERS</span><h2>What the answers were, and why.</h2>
      {v.teaching.map((t, i) => <div className="sample-step" key={i} style={{textAlign: 'left'}}><span className="step-dot">{i + 1}</span><div><strong><MathText value={t.equation}/> = <MathText value={t.answer}/></strong><p>{t.hint}</p></div></div>)}
      <p className="tiny">Three wrong answers stops the mission — answers are given, not guessed. Start a gentler mission when ready.</p></section>}
    <section className="card"><span className="eyebrow">AGENT THINKING · FULL TRACE</span>{mission.trace.map((line, i) => <div className="review-step" key={i}><p>{line}</p></div>)}</section></div>;}

  const drill = mission.current;
  return <div className="stack">
    <section className="card"><div className="row between"><span className="eyebrow">✦ MISSION RUNNING · DRILL {mission.drills_done + 1} OF {mission.max_drills}</span>
      <span className="pill green"><ShieldCheck size={13}/> Verified</span></div>
      <h2>{mission.goal}</h2>{mission.briefing && <p className="info-box">Mia: {mission.briefing}</p>}<p>Exit test: {mission.exit_wins} correct in a row. Current streak: {mission.consecutive}. Difficulty {mission.difficulty}. Three wrong answers stops the mission and reveals the verified answers.</p>
      <div className="step-progress">{Array.from({length: mission.exit_wins}).map((_, i) => <button key={i} aria-hidden="true" tabIndex={-1} className={i < mission.consecutive ? 'filled' : ''}/>)}</div></section>
    {mission.example && <section className="card"><span className="eyebrow">WORKED EXAMPLE · STUDY THIS FIRST</span>
      <div className="board-grid"><div className="board-equation"><MathText value={mission.example.equation}/></div>
      {mission.example.steps.map((s, i) => <div className="sample-step" key={i} style={{textAlign: 'left'}}><span className="step-dot">{i + 1}</span><div><strong><MathText value={s.equation}/></strong><p>{s.explanation}</p></div></div>)}
      <p className="tiny">Verified answer: <MathText value={mission.example.answer}/></p></div></section>}
    {drill && <section className="card quiz-card"><span className="eyebrow">{drill.kind === 'spot_mistake' ? "CATCH MIA'S MISTAKE · ENTER THE LINE NUMBER" : `YOUR TURN · ${drill.kind === 'comparison' ? 'ENTER <, = OR >' : 'FIND THE VALUE'}`}</span>
      {drill.kind === 'spot_mistake' && drill.steps ? <div className="board-grid">
        {drill.steps.map((s, i) => <div className="sample-step" key={i} style={{textAlign: 'left'}}><span className="step-dot">{i + 1}</span><div><strong><MathText value={s}/></strong></div></div>)}
      </div> : <div className="quiz-equation"><MathText value={drill.equation}/></div>}
      <form onSubmit={e => {e.preventDefault(); void submit();}}><label>{drill.kind === 'spot_mistake' ? 'Which line is wrong?' : 'Your answer'}<input value={answer} onChange={e => setAnswer(e.target.value)} placeholder={drill.kind === 'spot_mistake' ? 'Line number, e.g. 2' : drill.kind === 'comparison' ? '<, = or >' : 'e.g. 4 or 3/2'} autoComplete="off" inputMode={drill.kind === 'spot_mistake' ? 'numeric' : 'text'}/></label>
      <p className="tiny">Hint: {drill.hint}</p>
      <div className="row"><Button disabled={busy || !answer.trim()}>{busy ? 'Checking…' : 'Check answer'} <ArrowRight size={16}/></Button></div></form>
      {feedback && <p className={feedback.startsWith('Correct') ? 'success-box' : 'info-box'}>{feedback}</p>}
      {error && <p role="alert" className="error-box">{error}</p>}</section>}
    <section className="card"><span className="eyebrow">AGENT THINKING · LIVE TRACE</span><h2>Why Mia does what she does.</h2>
      {mission.trace.map((line, i) => <div className="review-step" key={i}><p>{line}</p></div>)}</section>
  </div>;
}
