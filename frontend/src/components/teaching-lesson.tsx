'use client';
import {useEffect,useState} from 'react';
import {post} from '@/lib/api';
import type {Feedback,Solution} from '@/lib/types';
import {firstAlgebraLesson,type TeachingLessonData} from '@/lib/teaching-lessons';
import {QuestionTeaching} from './question-teaching';
import {Button} from './ui/button';

// Curated lessons use the same classroom, languages and contextual examples as student questions.
export function TeachingLesson({lesson=firstAlgebraLesson,onAskQuestion}:{lesson?:TeachingLessonData;onAskQuestion?:(question:string)=>void}){
 const [solution,setSolution]=useState<Solution|null>(null),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 useEffect(()=>{let active=true;setSolution(null);setError('');Promise.all([
  post<Feedback>('/math/validate',{steps:lesson.steps.map(s=>s.equation),verify_only:true}),
  post<Solution>('/math/solve',{equation:lesson.equation,variable:'x'})
 ]).then(([check,result])=>{if(!check.valid||!result.verified||result.solution!==lesson.answer)throw new Error('The lesson could not be mathematically verified.');if(active)setSolution(result);}).catch(e=>{if(active)setError((e as Error).message);});return()=>{active=false;};},[lesson,retry]);
 return <section><h2>{lesson.title}</h2>{onAskQuestion&&<Button variant="outline" onClick={()=>onAskQuestion(lesson.equation)}>Ask / solve your own question</Button>}{error?<p role="alert">{error} <button onClick={()=>setRetry(n=>n+1)}>Retry verification</button></p>:solution?<QuestionTeaching key={lesson.equation} question={lesson.equation} solution={solution}/>:<p role="status">Checking the mathematical steps…</p>}</section>;
}
