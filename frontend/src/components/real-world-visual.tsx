'use client';
import {useState} from 'react';
import type {RealWorldExample} from '@/lib/real-world-example';

/** SVG geometry is derived only from validated scenario values. */
export function RealWorldVisual({example,step,onInteract,boardOnly=false}:{example:RealWorldExample;step:number;onInteract:()=>void;boardOnly?:boolean}) {
  const [explore,setExplore]=useState<number|null>(null);
  const [a,b,c,d]=example.values;
  const change=(value:number)=>{onInteract();setExplore(value);};
  return <section className="real-world-visual" aria-label={example.title}>
    {!boardOnly&&<><h3>{example.title}</h3><p className="tiny">{example.context}</p></>}
    {example.visual==='shopping'&&<>
      <svg viewBox="0 0 360 120" role="img" aria-label={`${a} notebooks, pen Rs. ${b}, total Rs. ${c}`}>
        {Array.from({length:a},(_,i)=>{const x=10+i*Math.min(39,230/a);return <g key={i} transform={`translate(${x},18)`}><rect x="2" y="4" width="30" height="58" rx="4" fill="#ddd4f6"/><rect width="28" height="58" rx="3" fill={step>=2?'#6846e8':'#9981cc'}/><path d="M5 2v54M10 18h13M10 24h13" stroke="white" opacity=".8"/><text x="14" y="82" textAnchor="middle" fontSize="11" fill="#191b37">{step>=3?`Rs.${d}`:'?'}</text></g>;})}
        <g opacity={step===1?.3:1}><path d="M270 22l9 2-14 52-7 9 1-12z" fill="#3a476a"/><path d="M270 22l9 2 2-8-9-2z" fill="#bdb4ca"/><text x="264" y="100" textAnchor="middle" fontSize="12">Rs. {b}</text></g>
        <text x="355" y="20" textAnchor="end" fontSize="12" fill="#6846e8">Total</text><text x="355" y="40" textAnchor="end" fontSize="14">Rs. {c}</text>
      </svg>
      {step>=3&&<label className="example-experiment">Explore a different basket: {explore??a} notebooks<input type="range" min="1" max="8" value={explore??a} onChange={e=>change(+e.target.value)}/><output>Total: Rs. {(explore??a)*d+b} — same Rs. {d} per notebook + Rs. {b} pen</output></label>}
    </>}
    {example.visual==='fraction'&&<><svg viewBox="0 0 360 180" role="img" aria-label={`${explore??(step===0?0:a)} of ${b} equal pizza slices selected`}>
      <circle cx="180" cy="85" r="74" fill="#c58a40"/>
      {Array.from({length:b},(_,i)=>{const start=i*2*Math.PI/b-Math.PI/2,end=(i+1)*2*Math.PI/b-Math.PI/2;const x=(t:number)=>180+68*Math.cos(t),y=(t:number)=>85+68*Math.sin(t);return <path key={i} d={`M180 85 L${x(start)} ${y(start)} A68 68 0 ${b===1?1:0} 1 ${x(end)} ${y(end)} Z`} fill={i<(explore??(step===0?0:a))?'#f0bb52':'#eee5d5'} stroke="#fff" strokeWidth="2"/>;})}
      <text x="180" y="175" textAnchor="middle" fontSize="14">{explore??(step===0?0:a)} / {b}</text>
    </svg><label>Explore selected slices<input type="range" min="0" max={b} value={explore??(step===0?0:a)} onChange={e=>change(+e.target.value)}/><output>{explore??(step===0?0:a)}/{b} selected; {b-(explore??(step===0?0:a))} remaining</output></label></>}
    {example.visual==='room'&&<svg viewBox="0 0 360 180" role="img" aria-label={`Rectangle ${a} metres by ${b} metres, area ${a*b} square metres`}>
      <rect x="65" y="25" width={a*Math.min(220/a,110/b)} height={b*Math.min(220/a,110/b)} fill="#eeeafe" stroke="#6846e8" strokeWidth="3"/>
      <text x="65" y="17" fontSize="13">{a} m</text><text x="8" y="70" fontSize="13">{b} m</text><text x="65" y="166" fontSize="14">{step>0?`${a*b} m²`:'Area = length × width'}</text>
    </svg>}
    {example.visual==='discount'&&<svg viewBox="0 0 360 130" role="img" aria-label={`Rs. ${b} original price, Rs. ${c} saving, Rs. ${b-c} final price`}>
      <text x="20" y="20" fontSize="13">Rs. {b} original</text><rect x="20" y="35" width="320" height="35" rx="5" fill="#eeeafe"/>
      <rect x="20" y="35" width={320*a/100} height="35" fill="#6846e8"/><text x="20" y="95" fontSize="13">{a}% off: save Rs. {c}</text><text x="20" y="117" fontSize="13">Final price: Rs. {(b-c).toFixed(2)}</text>
    </svg>}
    {example.visual==='journey'&&<><svg viewBox="0 0 360 190" role="img" aria-label={`Distance-time graph: constant speed ${a} kilometres per hour`}>
      <path d="M50 20v130h280" fill="none" stroke="#514865"/>
      {Array.from({length:5},(_,i)=><g key={i}><text x={50+i*65} y="167" fontSize="11" textAnchor="middle">{i}</text><text x="43" y={154-i*32} textAnchor="end" fontSize="11">{i*a}</text><path d={`M50 ${150-i*32}h260`} stroke="#eeeafe"/></g>)}
      <path d="M50 150L310 22" stroke="#6846e8" strokeWidth="3"/>
      <circle cx={50+(explore??(step===0?0:2))*65} cy={150-(explore??(step===0?0:2))*32} r="6" fill="#6846e8" stroke="white" strokeWidth="2"/>
      <text x="190" y="186" textAnchor="middle" fontSize="12">Time (hours)</text><text x="50" y="12" fontSize="12">Distance (km)</text>
    </svg><label>Explore time: {explore??(step===0?0:2)} hours<input type="range" min="0" max="4" value={explore??(step===0?0:2)} onChange={e=>change(+e.target.value)}/><output>{a*(explore??(step===0?0:2))} km</output></label></>}
    {!boardOnly&&explore!==null&&<p className="tiny">Exploration only — your original question and answer stay unchanged.</p>}
  </section>;
}
