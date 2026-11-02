'use client';
import type {Solution} from '@/lib/types';
import {equalGroupsExample} from '@/lib/question-teaching';
import {realWorldExample} from '@/lib/real-world-example';
import {ContextIllustration, contextKind, type ContextKind} from './context-illustration';
import {RealWorldVisual} from './real-world-visual';

type Lang = 'en' | 'ta';
const NOUNS: Record<ContextKind, {group: [string, string]; loose: [string, string]; whole: [string, string]}> = {
  pizza: {group: ['pizza', 'பீட்சா'], loose: ['slice', 'துண்டு'], whole: ['pizza', 'பீட்சா']},
  chocolate: {group: ['bar', 'சாக்லெட்'], loose: ['piece', 'துண்டு'], whole: ['chocolate bar', 'சாக்லெட்']},
  cake: {group: ['cake', 'கேக்'], loose: ['slice', 'துண்டு'], whole: ['cake', 'கேக்']},
  coffee: {group: ['cup', 'காபி'], loose: ['spoon', 'ஸ்பூன்'], whole: ['cup', 'காபி']},
  objects: {group: ['box', 'பெட்டி'], loose: ['counter', 'பொருள்'], whole: ['whole', 'முழுமை']},
};
const SLICE: Record<ContextKind, string> = {pizza: '#f0bb52', chocolate: '#8a5a3b', cake: '#e79ec4', coffee: '#9981cc', objects: '#9981cc'};
const DOT: Record<ContextKind, string> = {pizza: '#e8a251', chocolate: '#765044', cake: '#edb4cd', coffee: '#a38aed', objects: '#a38aed'};
const SHOW_LOOSE = 12;

function count(n: number, word: [string, string], lang: Lang) {
  return lang === 'ta' ? `${n} ${word[1]}` : `${n} ${word[0]}${n === 1 ? '' : 's'}`;
}

function GroupItem({kind}: {kind: ContextKind}) {
  if (kind === 'pizza') return <g><circle cx="0" cy="0" r="16" fill="#e8a251"/><circle cx="0" cy="0" r="12" fill="#ffe18c"/><path d="M0-12V12M-12 0H12" stroke="#fff8df" strokeWidth="2"/><circle cx="-4" cy="-5" r="2.2" fill="#d56a6a"/><circle cx="5" cy="4" r="2.2" fill="#d56a6a"/></g>;
  if (kind === 'chocolate') return <g><rect x="-15" y="-13" width="30" height="26" rx="4" fill="#765044"/><path d="M-5-13v26M5-13v26M-15 0h30" stroke="#b48a75" strokeWidth="2"/></g>;
  if (kind === 'cake') return <g><path d="M-14 10L14 10L14-12Z" fill="#edb4cd"/><path d="M-14 10L14-12l0 6-22 12z" fill="#b88be3"/><circle cx="14" cy="-12" r="2.4" fill="#d56a6a"/></g>;
  if (kind === 'coffee') return <g><path d="M8-8h6a7 7 0 010 14h-6" fill="none" stroke="#6846e8" strokeWidth="3"/><path d="M-13-10h21v14q0 10-10.5 10T-13 4z" fill="#a38aed"/><ellipse cx="-2.5" cy="-10" rx="10.5" ry="3.4" fill="#765444"/></g>;
  return <g><rect x="-14" y="-14" width="28" height="28" rx="7" fill="#a38aed"/><circle cx="0" cy="0" r="5" fill="#eeeafe"/></g>;
}

/** Board visual for a generated example. Quantities come only from verified maths, never parsed from prose. */
export function ThemedExampleVisual({context, question, solution, language}: {context: string; question: string; solution: Solution; language: Lang}) {
  const kind = contextKind(context);
  const nouns = NOUNS[kind];
  const groups = equalGroupsExample(question, solution);
  if (groups) {
    const {quantity: a, extra, total, answer} = groups;
    const shown = Math.min(extra, SHOW_LOOSE);
    return <div className="themed-example">
      <p className="themed-example-title">{count(a, nouns.group, language)} + {count(extra, nouns.loose, language)} = {count(total, nouns.loose, language)}</p>
      <svg viewBox="0 0 360 104" aria-hidden="true">
        {Array.from({length: a}, (_, i) => <g key={i} transform={`translate(${22 + i * Math.min(42, 316 / a)},30)`} className="themed-qty-item" style={{animationDelay: `${i * 70}ms`}}><GroupItem kind={kind}/></g>)}
        {Array.from({length: shown}, (_, i) => <g key={`l${i}`} transform={`translate(${22 + i * 22},82)`} className="themed-qty-item" style={{animationDelay: `${(a + i) * 70}ms`}}><circle cx="0" cy="0" r="8" fill={DOT[kind]}/></g>)}
        {extra > SHOW_LOOSE && <text x={22 + SHOW_LOOSE * 22} y="87" fontSize="12" fill="#514865">+{extra - SHOW_LOOSE} {language === 'ta' ? 'மேலும்' : 'more'}</text>}
      </svg>
      <p className="tiny">{language === 'ta' ? `ஒவ்வொரு ${nouns.group[1]} = ${answer} ${nouns.loose[1]} · சரிபார்க்கப்பட்ட விடையின் எடுத்துக்காட்டுப் படம்` : `Each ${nouns.group[0]} = ${answer} ${nouns.loose[0]}${answer === 1 ? '' : 's'} · illustrative picture of your verified answer`}</p>
    </div>;
  }
  const local = realWorldExample(question, solution, 'en');
  if (local?.visual === 'fraction' && kind === 'pizza')
    return <RealWorldVisual example={local} step={local.steps.length - 1} onInteract={() => {}} />;
  if (local && local.visual !== 'fraction')
    return <RealWorldVisual example={local} step={local.steps.length - 1} onInteract={() => {}} />;
  if (local?.visual === 'fraction') {
    const [a, b] = local.values;
    const x = (t: number) => 180 + 68 * Math.cos(t), y = (t: number) => 85 + 68 * Math.sin(t);
    return <div className="themed-example">
      <p className="themed-example-title">{a}/{b} {language === 'ta' ? nouns.whole[1] : `of a ${nouns.whole[0]}`}</p>
      <svg viewBox="0 0 360 170" aria-hidden="true">
        <circle cx="180" cy="85" r="74" fill="#c58a40"/>
        {Array.from({length: b}, (_, i) => {
          const start = i * 2 * Math.PI / b - Math.PI / 2, end = (i + 1) * 2 * Math.PI / b - Math.PI / 2;
          return <path key={i} d={`M180 85 L${x(start)} ${y(start)} A68 68 0 0 1 ${x(end)} ${y(end)} Z`} fill={i < a ? SLICE[kind] : '#eee5d5'} stroke="#fff" strokeWidth="2" className="themed-qty-item" style={{animationDelay: `${i * 60}ms`}}/>;
        })}
      </svg>
      <p className="tiny">{language === 'ta' ? `${a} தேர்வு · ${b - a} மீதம் · சரிபார்க்கப்பட்ட விடையின் எடுத்துக்காட்டுப் படம்` : `${a} selected · ${b - a} remaining · illustrative picture of your verified answer`}</p>
    </div>;
  }
  return <ContextIllustration context={context}/>;
}
