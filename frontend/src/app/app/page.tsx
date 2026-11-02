'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, ArrowLeft, BookOpen, ChartNoAxesCombined, ChevronRight, CircleCheck, GraduationCap, LayoutDashboard, LogOut, Map as MapIcon, PenLine, Rocket, Settings2, ShieldCheck, Sparkles, Target, TrendingUp } from 'lucide-react';
import { api, post, setToken } from '@/lib/api';
import type { User, Topic, Solution, Progress } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { MathText } from '@/components/math';
import { GeometryDiagram } from '@/components/geometry-diagram';
import { teachingLessons } from '@/lib/teaching-lessons';
import { TeachingLesson } from '@/components/teaching-lesson';
import { Teacher } from '@/components/teacher';
import { GraphPlayground } from '@/components/graph';
import { Quiz } from '@/components/quiz';
import { ExploreTopics } from '@/components/explore-topics';
import {QuestionTeaching} from '@/components/question-teaching';
import { QuestionInput } from '@/components/question-input';
import { Handwriting } from '@/components/handwriting';
import { MiaPanel } from '@/components/mia-panel';
import { Mission } from '@/components/mission';
import { Journey } from '@/components/journey';
import { ProgressView } from '@/components/progress';
import { Settings } from '@/components/settings';
import { ProfileEditor } from '@/components/profile-editor';
const navigation = [{id: 'topics', name: 'Home', icon: LayoutDashboard}, {id: 'learn', name: 'Learning studio', icon: GraduationCap}, {id: 'graph', name: 'Graph playground', icon: ChartNoAxesCombined}, {id: 'quiz', name: 'Practice & grow', icon: Target}, {id: 'mission', name: 'Mastery mission', icon: Rocket}, {id: 'journey', name: 'Math Treasure Journey', icon: MapIcon}, {id: 'handwriting', name: 'Check my work', icon: PenLine}, {id: 'progress', name: 'My progress', icon: TrendingUp}, {id: 'settings', name: 'Settings', icon: Settings2}];
export default function Workspace() {
  const focusQuestion = useRef(false);
  const [teachingIndex, setTeachingIndex] = useState(0);
  const [guided, setGuided] = useState(false);
  const [variable, setVariable] = useState(''); const [narrating, setNarrating] = useState(false); const solveRequest = useRef(0); const router = useRouter(); const queryClient = useQueryClient(); const [user, setUser] = useState<User | null>(null); const [view, setView] = useState('topics'); const [equation, setEquation] = useState('2x + 3 = 11'); const [solution, setSolution] = useState<Solution | null>(null); const [step, setStep] = useState(0); const [lessonId, setLessonId] = useState('balance'); const [lessonEquation, setLessonEquation] = useState('2x + 3 = 11'); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [engine, setEngine] = useState('Local engine'); const [engineOn, setEngineOn] = useState(false);
  useEffect(() => {let active = true; api<User>('/me').then(u => {if (active) setUser(u);}).catch(() => {if (active) router.replace('/login');}); return () => {active = false;};}, [router]);
  useEffect(() => {api<{configured: boolean}>('/tutor/status').then(s => {setEngineOn(s.configured); if (s.configured) setEngine('Meta Muse Spark');}).catch(() => {});}, []);
  const topics = useQuery({queryKey: ['topics'], queryFn: () => api<Topic[]>('/topics'), enabled: !!user});
  const progress = useQuery({queryKey: ['progress'], queryFn: () => api<Progress>('/progress'), enabled: !!user});
  async function solve(value = equation, target = variable) {const request = ++solveRequest.current; setBusy(true); setError(''); try {const result = await post<Solution>('/math/solve', {equation: value, variable: target || null}); if (request === solveRequest.current) {setSolution(result); setStep(0);}} catch(e) {if (request === solveRequest.current) setError((e as Error).message);} finally {if (request === solveRequest.current) setBusy(false);}}
  function openLesson(id: string, value: string) {setVariable(''); setLessonId(id); setLessonEquation(value); setEquation(value); setGuided(false); setSolution(null); setView('learn'); void post('/sessions', {lesson_id: id}).catch(e => setError(e.message)); void solve(value, '');}
  function chooseExample(example: string) {
    solveRequest.current += 1; setBusy(false); setError(''); setGuided(false);
    setVariable(''); setEquation(example); setSolution(null); setStep(0);
    setLessonId(''); setLessonEquation(''); focusQuestion.current = true; setView('learn');
  }
  useEffect(() => {window.scrollTo({top: 0, behavior: 'instant'});}, [view]);
  useEffect(() => {
    if (view === 'learn' && focusQuestion.current) {
      focusQuestion.current = false; document.getElementById('math-question')?.focus();
    }
  }, [view, equation]);
  if (!user) return <main className="loading-page"><span className="brand-icon"><img src="/logo-icon.png" alt="MathMate AI logo"/></span><h2>Opening your learning space…</h2></main>;
  const data = progress.data; const current = solution?.steps[step];
  return <div className="app-shell"><a href="#main-content" className="skip-link">Skip to main content</a><aside className="sidebar"><Link href="/" className="brand"><span className="brand-icon"><img src="/logo-icon.png" alt="MathMate AI logo"/></span>MathMate<span className="ai-label">AI</span></Link><span className="nav-caption">YOUR LEARNING SPACE</span><nav>{navigation.map(n => <button key={n.id} onClick={() => {setGuided(false); setView(n.id); setError('');}} className={view === n.id || (view === 'whiteboard' && n.id === 'topics') ? 'active' : ''} aria-current={view === n.id || (view === 'whiteboard' && n.id === 'topics') ? 'page' : undefined}><n.icon size={19}/>{n.name}{view === n.id && <span className="nav-dot"/>}</button>)}</nav><div className="sidebar-note"><Sparkles size={21}/><strong>A little every day<br/>goes a long way.</strong><p>Your only competition<br/>is yesterday’s you.</p></div><button className="profile-button" onClick={() => setView('settings')}><span className="user-avatar">{user.name.slice(0, 1).toUpperCase()}</span><span><strong>{user.name}</strong><small>Curious mind</small></span><ChevronRight size={17}/></button><button className="logout" onClick={async () => {try {await post('/auth/logout'); setToken(null); queryClient.clear(); router.replace('/login');} catch(e) {setError((e as Error).message);}}}><LogOut size={15}/> Sign out</button></aside><div className="main-shell"><header className="app-header"><span>My learning space <ChevronRight size={13}/> <strong>{(view === 'whiteboard' ? 'Mia’s whiteboard' : navigation.find(n => n.id === view)?.name)}</strong></span><div className="row"><span className="pill green"><ShieldCheck size={13}/> Verified maths</span><span className={engineOn ? 'pill green' : 'pill'}>{engine}</span><span className="user-avatar small">{user.name.slice(0, 1)}</span></div></header><main id="main-content" tabIndex={-1} className={`app-main ${view === 'learn' ? 'studio-main' : view === 'topics' ? 'topics-main' : ''}`}><div className="page-heading"><div><span className="eyebrow">{view === 'topics' ? 'LET’S MAKE SOMETHING CLICK TODAY' : 'ONE STEP CLOSER TO UNDERSTANDING'}</span><h1>{view === 'topics' ? `Hi, ${user.name.split(' ')[0]}.` : (view === 'whiteboard' ? 'Mia’s whiteboard' : navigation.find(n => n.id === view)?.name)}<span className="heading-spark">✦</span></h1><p>{view === 'topics' ? 'A fresh start, a curious mind, and a little maths magic.' : 'A calm space to explore, practise, and grow.'}</p></div>{view === 'topics' && <span className="pill">Your personal learning journey</span>}</div>{error && <p role="alert" className="error-box">{error}</p>}{(topics.error || progress.error) && <p role="alert" className="error-box">Could not load your learning data. <button onClick={() => {void topics.refetch(); void progress.refetch();}}>Try again</button></p>}

  {view === 'whiteboard' && <TeachingLesson key={teachingIndex} lesson={teachingLessons[teachingIndex]} onAskQuestion={chooseExample}/>}{view === 'topics' && <ExploreTopics topics={topics.data||[]} completed={data?.completed_lessons||[]} recommendation={data?.recommendation||''} onPractice={()=>setView('quiz')} onSelect={chooseExample} onLesson={openLesson} onWhiteboard={index=>{setTeachingIndex(index);setView('whiteboard');}} onGraph={()=>setView('graph')}/>}
  {view === 'learn' && <div className="student-teaching-studio">
    <section className="card lesson-nav"><span className="eyebrow">YOUR LESSONS</span>{topics.data?.flatMap(t=>t.lessons).map(l=><button key={l.id} className={lessonId===l.id?'selected':''} onClick={()=>openLesson(l.id,l.equation)}><BookOpen size={16}/>{l.title}</button>)}</section>
    <section className="card whiteboard"><div className="row between"><span className="eyebrow">LET’S WORK IT OUT</span><span className="pill green"><ShieldCheck size={13}/>{solution?.verified?'Verified · real domain':'Exact maths · real domain'}</span></div><h2>Let’s explore the maths.</h2>
    <QuestionInput onExploreTopics={()=>{solveRequest.current+=1;setBusy(false);setGuided(false);setError('');setView('topics');}} key={lessonId} value={equation} variable={variable} onChange={text=>{solveRequest.current+=1;setBusy(false);setError('');setEquation(text);setGuided(false);setSolution(null);}} onVariable={value=>{solveRequest.current+=1;setBusy(false);setVariable(value);setGuided(false);setSolution(null);}} onSolution={result=>{setSolution(result);setStep(0);}}/>
    </section>
    {solution ? <QuestionTeaching key={equation+JSON.stringify(solution)} question={equation} solution={solution} onComplete={equation===lessonEquation && !data?.completed_lessons.includes(lessonId) ? async()=>{try {await post(`/lessons/${lessonId}/complete`);await queryClient.invalidateQueries({queryKey:['progress']});}catch(e){setError((e as Error).message);}}:undefined}/> : <p className="info-box">Submit your question above. Mia will explain its verified steps here.</p>}
  </div>}
  {view === 'graph' && <div className="stack"><GraphPlayground/><MiaPanel question="y=x" compact /></div>}{view === 'quiz' && <div className="stack"><Quiz/><MiaPanel compact /></div>}{view === 'mission' && <div className="stack"><Mission/><MiaPanel compact /></div>}{view === 'journey' && <div className="stack"><Journey/><MiaPanel compact /></div>}{view === 'handwriting' && <div className="stack"><Handwriting/><MiaPanel compact /></div>}{view === 'progress' && (data ? <div className="stack"><ProgressView data={data}/><MiaPanel compact /></div> : <p>Loading your progress…</p>)}{view === 'settings' && <div className="stack"><ProfileEditor user={user} onUpdate={setUser}/><Settings user={user}/></div>}</main><footer className="app-footer">© 2026 MathMate AI <span>Built for the Meta Global AI Developer Hackathon 2026</span></footer></div></div>;
}
