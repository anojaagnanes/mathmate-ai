'use client';
import { useEffect, useState } from 'react';
import { ArrowRight, Check, CircleHelp, Eye, Lightbulb, Lock, Play, RotateCcw, ShieldCheck, Sparkles, Star } from 'lucide-react';
import { api, post } from '@/lib/api';
import { MathText } from '@/components/math';
import { Button } from '@/components/ui/button';

type Island = {key: string; title: string; subtitle: string; topic: string; state: string; gems: number; asked: number};
type Drill = {number: number; equation: string; hint: string; difficulty: number; kind: string; prompt: string; steps?: string[]; lifelines: string[]};
type Step = {equation: string; explanation: string};
type Journey = {id: string; state: string; story: string | null; island_index: number; islands: Island[]; gems_needed: number;
  questions_done: number; correct_count: number; assists: number; current: Drill | null; trace: string[]; verdict: {
    treasure: boolean; gems: number; accuracy_before: number; accuracy_after: number; questions: number; assists: number;
    message: string; islands: {title: string; state: string; gems: number}[]} | null};
type Turn = {correct: boolean; message: string; event: string | null; story: string | null; advanced: boolean; state: string; island_index: number; islands: Island[];
  gems_needed: number; questions_done: number; correct_count: number; assists: number; current: Drill | null; trace: string[]; verdict: Journey['verdict']};
type Lifeline = {kind: string; text: string; step: Step | null; steps: Step[]; answer: string | null; revealed: boolean};

const LEVEL_NAMES = ['', 'Easy', 'Medium', 'Advanced'];
const STATE_LABELS: Record<string, string> = {locked: 'Locked', current: 'Play', conquered: 'Done', cursed: 'Retry'};
// Node centres in the 600x760 roadmap space: start bottom, treasure top.
const NODE_POS = [{x: 350, y: 660}, {x: 200, y: 540}, {x: 400, y: 420}, {x: 200, y: 300}, {x: 380, y: 180}];
const TREASURE_POS = {x: 300, y: 62};
const TRAIL = 'M 350 665 C 280 635 210 605 200 540 C 190 475 300 460 400 420 C 490 385 320 340 200 300 C 100 268 280 225 380 180 C 440 155 370 100 300 62';

function NodeIcon({state}: {state: string}) {
  if (state === 'conquered') return <Check size={24}/>;
  if (state === 'current') return <Star size={24}/>;
  if (state === 'cursed') return <RotateCcw size={22}/>;
  return <Lock size={22}/>;
}

function GemDots({done, needed}: {done: number; needed: number}) {
  return <span className="map-gems" aria-label={`${done} of ${needed} correct`}>
    {Array.from({length: needed}).map((_, i) => <span key={i} className={i < done ? 'got' : ''}/>)}
  </span>;
}

export function Journey() {
  const [journey, setJourney] = useState<Journey | null>(null);
  const [started, setStarted] = useState(false);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
  const [good, setGood] = useState(false);
  const [event, setEvent] = useState<string | null>(null);
  const [story, setStory] = useState('');
  const [lifeline, setLifeline] = useState<Lifeline | null>(null);
  const [hintShown, setHintShown] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [revealed, setRevealed] = useState(false);
  const qkey = journey ? `${journey.island_index}-${journey.questions_done}` : '';

  useEffect(() => {let active = true;
    api<Journey>('/journey/current').then(j => {if (active) {setJourney(j); setStarted(true); if (j.story) setStory(j.story);}}).catch(() => {if (active) setStarted(false);});
    return () => {active = false;};}, []);

  useEffect(() => {setLifeline(null); setHintShown(false);}, [qkey]);

  async function start() {setBusy(true); setError(''); setStory(''); setRevealed(false); try {const j = await post<Journey>('/journey/start'); setJourney(j); setStarted(true); setRevealed(false); if (j.story) setStory(j.story);} catch (e) {setError((e as Error).message);} finally {setBusy(false);}}
  async function restart() {setBusy(true); setError(''); setRevealed(false); try {const j = await post<Journey>('/journey/restart'); setJourney(j); setStarted(true); setRevealed(false); setFeedback(''); setEvent(null); setAnswer(''); setLifeline(null); setHintShown(false); if (j.story) setStory(j.story); else setStory('');} catch (e) {setError((e as Error).message);} finally {setBusy(false);}}
  function goPlay() {
    const reduce = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.getElementById('journey-player')?.scrollIntoView({behavior: reduce ? 'instant' : 'smooth', block: 'start'});
    document.getElementById('journey-answer')?.focus({preventScroll: true});
  }
  function goMap() {
    const reduce = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.getElementById('journey-map')?.scrollIntoView({behavior: reduce ? 'instant' : 'smooth', block: 'start'});
  }
  function tapBadge() {setRevealed(true); setFeedback(''); setEvent(null); setTimeout(goPlay, 80);}
  async function submit() {if (!journey || !answer.trim()) return; setBusy(true); setError(''); setFeedback(''); setEvent(null);
    try {const turn = await post<Turn>(`/journey/${journey.id}/answer`, {answer: answer.trim()});
      setJourney({...journey, state: turn.state, island_index: turn.island_index, islands: turn.islands, gems_needed: turn.gems_needed,
        questions_done: turn.questions_done, correct_count: turn.correct_count, assists: turn.assists, current: turn.current, trace: turn.trace, verdict: turn.verdict});
      setFeedback(turn.message); setGood(turn.correct); setEvent(turn.event); setAnswer(''); setLifeline(null); setHintShown(false);
      if (turn.story) setStory(turn.story);
      if (turn.state === 'complete') {window.scrollTo(0, 0); return;}
      if (turn.advanced !== false) {setRevealed(false); setTimeout(goMap, 80);}
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}}
  async function callLifeline(kind: string) {if (!journey) return; setBusy(true); setError('');
    try {const out = await post<Lifeline>(`/journey/${journey.id}/lifeline`, {kind});
      setLifeline(out); if (kind === 'hint') setHintShown(true);
      if (journey.current && !journey.current.lifelines.includes(kind)) {
        setJourney({...journey, current: {...journey.current, lifelines: [...journey.current.lifelines, kind]}});
      }
    } catch (e) {setError((e as Error).message);} finally {setBusy(false);}}

  if (!started || !journey) return <section className="card"><span className="eyebrow">✦ MATH TREASURE JOURNEY · MIA PLANS YOUR PATH</span>
    <h2>Follow the trail to the treasure.</h2>
    <p>Five levels wind up the mountain, from easy to advanced. Press play, answer the question, and pass to unlock the next one. Three correct answers clear each level — and hints, guided steps, and worked solutions are always here when you get stuck.</p>
    {error && <p role="alert" className="error-box">{error}</p>}
    <div className="row"><Button onClick={start} disabled={busy}>{busy ? 'Planning your journey…' : 'Start my journey'} <Play size={16}/></Button></div></section>;

  if (journey.state === 'complete' && journey.verdict) {const v = journey.verdict;
    return <div className="stack"><div className={v.treasure ? 'success-box' : 'info-box'}>
      {v.treasure && <img src="/treasure-chest.jpg" alt="Treasure chest" className="treasure-win-img"/>}
      <h3>{v.treasure ? 'Treasure won — every level cleared!' : 'Journey complete — some levels need another try.'}</h3><p>{v.message}</p></div>
    <section className="card"><span className="eyebrow">BEFORE → AFTER</span><h2>Your proof of progress.</h2>
      <div className="stats"><article><strong>{Math.round(v.accuracy_before * 100)}% → {Math.round(v.accuracy_after * 100)}%</strong><span>accuracy</span></article>
      <article><strong>{v.gems}</strong><span>correct answers</span></article><article><strong>{v.assists}</strong><span>solutions shown</span></article></div>
      <div className="journey-results">{v.islands.map((i, n) => <div key={i.title} className={`journey-result ${i.state}`}><strong>Level {n + 1} · {i.title}</strong><span>{i.state === 'conquered' ? `${i.gems}/${journey.gems_needed} · Cleared` : 'Needs another try'}</span></div>)}</div>
      <div className="row" style={{marginTop: 20}}><Button onClick={() => {setJourney(null); setStarted(false); setFeedback(''); setEvent(null); setStory(''); setRevealed(false);}}>Play again <ArrowRight size={16}/></Button></div></section>
    <section className="card"><span className="eyebrow">AGENT THINKING · FULL TRACE</span>{journey.trace.map((line, i) => <div className="review-step" key={i}><p>{line}</p></div>)}</section></div>;}

  const drill = journey.current;
  const island = journey.islands[journey.island_index];
  const [eventKind, eventStage] = event ? (event.split(':') as [string, string]) : [null, null];
  return <div className="stack">
    <section id="journey-map" className="card roadmap-card"><div className="row between"><span className="eyebrow">YOUR ROADMAP · LEVEL {Math.min(journey.island_index + 1, journey.islands.length)} OF {journey.islands.length}</span>
      <span className="pill green"><ShieldCheck size={13}/> Verified</span></div>
      <div className="roadmap" role="list" aria-label="Journey levels">
        <svg viewBox="0 0 600 760" preserveAspectRatio="none" aria-hidden="true"><path d={TRAIL} className="roadmap-trail"/></svg>
        <div className="map-node treasure" style={{left: `${TREASURE_POS.x / 6}%`, top: `${TREASURE_POS.y / 7.6}%`}}>
          <img src="/treasure-chest.jpg" alt="Treasure chest" className="map-treasure-img"/>
          <span className="map-label"><strong>Treasure</strong></span>
        </div>
        {journey.islands.map((isl, i) => <button type="button" key={isl.key} role="listitem" className={`map-node ${isl.state}`}
            style={{left: `${NODE_POS[i].x / 6}%`, top: `${NODE_POS[i].y / 7.6}%`}}
            onClick={tapBadge} disabled={isl.state !== 'current'}
            aria-label={isl.state === 'current' ? `Play level ${i + 1}: ${isl.title}` : `Level ${i + 1} ${isl.title} locked`}>
          <span className="map-badge"><NodeIcon state={isl.state}/></span>
          <span className="map-label"><strong>Level {i + 1}</strong><small>{isl.title}</small></span>
          <GemDots done={isl.gems} needed={journey.gems_needed}/>
          <span className="map-state">{STATE_LABELS[isl.state] || isl.state}</span>
        </button>)}
      </div><div className="row between" style={{marginTop: 12}}><span className="tiny">Tap the glowing badge to play your level.</span><button type="button" className="text-button" onClick={() => void restart()}>Restart journey</button></div></section>
    {story && <p className="info-box">Mia: {story}</p>}
    {eventKind === 'conquered' && <div className="success-box"><h3>{eventStage} cleared!</h3><p>On to the next level — the questions keep coming.</p></div>}
    {eventKind === 'passage' && <div className="info-box"><h3>{eventStage} needs another try.</h3><p>Moving on so your journey continues. Clear it next time.</p></div>}
    {feedback && <p className={good ? 'success-box' : 'info-box'}>{feedback}</p>}
    {drill && island && revealed && <section id="journey-player" className="card quiz-card"><span className="eyebrow">LEVEL {journey.island_index + 1} · {island.title.toUpperCase()} · QUESTION {drill.number}</span>
      <div className="row between"><p style={{margin: 0}}>{drill.prompt}</p>
        <span className={`pill level-${drill.difficulty}`}><Sparkles size={12}/> {LEVEL_NAMES[drill.difficulty] || ''}</span></div>
      {drill.kind === 'spot_mistake' && drill.steps ? <div className="board-grid">
        {drill.steps.map((s, i) => <div className="sample-step" key={i} style={{textAlign: 'left'}}><span className="step-dot">{i + 1}</span><div><strong><MathText value={s}/></strong></div></div>)}
      </div> : <div className="quiz-equation"><MathText value={drill.equation}/></div>}
      <form onSubmit={e => {e.preventDefault(); void submit();}}>
        <label>Your answer<input id="journey-answer" value={answer} onChange={e => setAnswer(e.target.value)} placeholder={drill.kind === 'spot_mistake' ? 'Line number, e.g. 2' : drill.kind === 'comparison' ? '<, = or >' : 'e.g. 4 or 3/2'} autoComplete="off" inputMode={drill.kind === 'spot_mistake' ? 'numeric' : 'text'}/></label>
        <div className="row"><Button disabled={busy || !answer.trim()}>{busy ? 'Checking…' : 'Check answer'} <ArrowRight size={16}/></Button></div>
      </form>
      <div className="journey-help"><span className="eyebrow">NEED HELP?</span>
        <div className="row">
          <Button type="button" className="outline" onClick={() => void callLifeline('hint')} disabled={busy || hintShown}><CircleHelp size={15}/> {hintShown ? 'Hint shown' : 'Show hint'}</Button>
          <Button type="button" className="outline" onClick={() => void callLifeline('nudge')} disabled={busy || drill.lifelines.includes('nudge')}><Lightbulb size={15}/> Guided step</Button>
          <Button type="button" className="outline" onClick={() => void callLifeline('reveal')} disabled={busy || drill.lifelines.includes('reveal')}><Eye size={15}/> Show solution</Button>
        </div></div>
      {hintShown && <p className="info-box">Hint: {drill.hint}</p>}
      {lifeline && lifeline.kind === 'nudge' && <div className="info-box"><p>{lifeline.text}</p>
        {lifeline.step && <div className="sample-step" style={{textAlign: 'left'}}><span className="step-dot">1</span><div><strong><MathText value={lifeline.step.equation}/></strong><p>{lifeline.step.explanation}</p></div></div>}</div>}
      {lifeline && lifeline.kind === 'reveal' && <div className="info-box"><p>{lifeline.text} It does not count toward the level — but the journey continues.</p>
        {lifeline.steps.map((s, i) => <div className="sample-step" key={i} style={{textAlign: 'left'}}><span className="step-dot">{i + 1}</span><div><strong><MathText value={s.equation}/></strong><p>{s.explanation}</p></div></div>)}
        {lifeline.answer && <p><strong>Answer: <MathText value={lifeline.answer}/></strong></p>}</div>}

      {error && <p role="alert" className="error-box">{error}</p>}</section>}
    <section className="card"><span className="eyebrow">AGENT THINKING · LIVE TRACE</span><h2>Why Mia does what she does.</h2>
      {journey.trace.map((line, i) => <div className="review-step" key={i}><p>{line}</p></div>)}</section>
  </div>;
}
