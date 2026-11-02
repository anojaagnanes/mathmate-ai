import type {Solution} from './types';

export type TeachingPlayback = {step:number; progress:number; playing:boolean; paused:boolean};

export type ClassroomPhase='READY'|'TEACHING'|'INTERRUPTED'|'ANSWERING'|'WAITING_FOR_STUDENT'|'RESUMING'|'COMPLETE';
export type ClassroomSession={step:number;progress:number;segmentStart:number;phase:ClassroomPhase};
export const initialClassroom:ClassroomSession={step:0,progress:0,segmentStart:0,phase:'READY'};
export type ClassroomEvent={type:'resume'|'started'|'interrupt'|'answering'|'waiting'|'replay'|'read'}|{type:'progress';value:number}|{type:'ended';count:number}|{type:'move';step:number};
export function classroomTransition(state:ClassroomSession,event:ClassroomEvent):ClassroomSession {
  switch(event.type) {
    case 'resume':return {...state,segmentStart:state.progress,phase:'RESUMING'};
    case 'started':return state.phase==='RESUMING'?{...state,phase:'TEACHING'}:state;
    case 'interrupt':return {...state,phase:'INTERRUPTED'};
    case 'answering':return {...state,phase:'ANSWERING'};
    case 'waiting':return {...state,phase:'WAITING_FOR_STUDENT'};
    case 'read':return {...state,progress:1,phase:'WAITING_FOR_STUDENT'};
    case 'replay':return {...state,progress:0,segmentStart:0,phase:'RESUMING'};
    case 'move':return {...initialClassroom,step:Math.max(0,event.step)};
    case 'progress':return state.phase!=='TEACHING'&&state.phase!=='RESUMING'?state:{...state,progress:Math.max(state.progress,Math.min(1,state.segmentStart+(1-state.segmentStart)*event.value))};
    case 'ended':return state.phase!=='TEACHING'&&state.phase!=='RESUMING'?state:state.step+1<event.count?{...initialClassroom,step:state.step+1,phase:'RESUMING'}:{...state,progress:1,phase:'COMPLETE'};
  }
}

export function remainingNarration(text:string,progress:number) {
  if(progress<=0)return text;
  const index=Math.min(text.length,Math.floor(progress*text.length));
  const boundary=text.lastIndexOf(' ',index);
  return text.slice(Math.max(0,boundary+1)) || 'This step is complete. Let’s continue.';
}
export type TeachingAction = {type:'play'|'pause'|'resume'|'stop'|'replay'|'reveal'} | {type:'move'; step:number} | {type:'progress'; progress:number};
export const initialTeaching: TeachingPlayback = {step:0,progress:0,playing:false,paused:false};
export function teachingTransition(state:TeachingPlayback, action:TeachingAction):TeachingPlayback {
  switch(action.type) {
    case 'play': return {...state,playing:true,paused:false};
    case 'pause': return {...state,paused:true};
    case 'resume': return {...state,paused:false};
    case 'stop': return {...state,playing:false,paused:false};
    case 'replay': return {...state,progress:0,playing:true,paused:false};
    case 'move': return {...initialTeaching,step:Math.max(0,action.step)};
    case 'reveal': return {...state,progress:1};
    case 'progress': return state.paused || !state.playing || action.progress<=state.progress ? state : {...state,progress:Math.max(state.progress,Math.max(0,Math.min(1,action.progress)))};
  }
}

/** Only an exact bounded positive-integer linear model receives this analogy. */
export function equalGroupsExample(question:string, solution:Solution) {
  if (!solution.verified || solution.kind!=='unique' || !solution.variable) return null;
  const match=question.replace(/\s/g,'').match(/^(\d{1,2})\*?([a-z])\+(\d{1,4})=(\d{1,4})$/);
  if(!match || match[2]!==solution.variable) return null;
  const quantity=Number(match[1]), extra=Number(match[3]), total=Number(match[4]), answer=Number(solution.solution);
  if(quantity<1 || quantity>8 || !Number.isSafeInteger(answer) || answer<0 || quantity*answer+extra!==total) return null;
  return {quantity,extra,total,answer,variable:match[2],narration:`Imagine ${quantity} equal boxes of counters, with ${extra} loose counters. There are ${total} counters altogether. ${match[2]} means the number in each box. Remove the ${extra} loose counters, then share the remaining ${total-extra} equally across ${quantity} boxes. Each box contains ${answer}. Checking: ${quantity} times ${answer}, plus ${extra}, equals ${total}.`};
}

/** Shared text layout for the scene's board and writing-hand target. */
export function writingLayout(text:string,progress:number) {
  const chars=Array.from(text), count=Math.floor(chars.length*Math.max(0,Math.min(1,progress)));
  const columns=Math.min(28,Math.max(1,chars.length)), rows=Math.max(1,Math.ceil(chars.length/columns));
  const visible=chars.slice(0,count), lines=[];
  for(let i=0;i<visible.length;i+=columns) lines.push(visible.slice(i,i+columns).join(''));
  const cursor=Math.max(0,count-1);
  return {lines,columns,rows,x:(cursor%columns+.5)/columns,y:(Math.floor(cursor/columns)+.5)/rows};
}

/** Omit only successful substitution checks. The board always starts with
 *  the submitted question, then shows every solving step in order. */
export function teachingSteps(steps:Solution['steps']) {
  const solving=steps.filter(step=>!(/^Substitute\b/i.test(step.explanation) && /original equation.*Both sides agree/i.test(step.explanation)));
  return solving.length?solving:steps;
}

/** True when the current row is outside the board viewport and the board must scroll.
 *  When the row is already visible the student's own scroll position is never stolen. */
export function rowNeedsScroll(rowTop:number,rowBottom:number,boardTop:number,boardBottom:number){
  return rowTop<boardTop||rowBottom>boardBottom;
}

/** Preserve every revealed line when pausing, replaying, or revisiting a step. */
export function recordBoardProgress(history:Record<number,number>,step:number,progress:number):Record<number,number> {
  const next={...history};
  for(let i=0;i<step;i++)next[i]=1;
  next[step]=Math.max(next[step]||0,Math.min(1,Math.max(0,progress)));
  return next;
}
