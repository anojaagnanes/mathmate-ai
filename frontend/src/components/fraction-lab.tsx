'use client';
import {useState} from 'react';
import {parseAddends, labModel, vulgar, type Addend} from '@/lib/fractions';

function Bar({of, fill, label, interactive, selected, onToggle}: {of: Addend; fill: number; label: string; interactive?: boolean; selected?: number[]; onToggle?: (i: number) => void}) {
  const cells = Array.from({length: of[1]}, (_, i) => i);
  return <div role={interactive ? 'group' : 'img'} aria-label={label} style={{display: 'grid', gridTemplateColumns: `repeat(${Math.min(of[1], 6)},1fr)`, gap: 4, marginBlock: 8}}>
    {cells.map(i => {
      const on = interactive ? (selected || []).includes(i) : i < fill;
      const body = <span style={{display: 'block', minHeight: 44, border: '1px solid #6846E8', borderRadius: 8, background: on ? '#6846E8' : '#EEEAFE', color: on ? 'white' : '#15163F', textAlign: 'center', padding: 10}}>{vulgar(1, of[1])}</span>;
      return interactive ? <button key={i} type="button" aria-label={`Piece ${i + 1} of ${of[1]}`} aria-pressed={on} onClick={() => onToggle && onToggle(i)} style={{background: 'none', border: 'none', padding: 0, cursor: 'pointer'}}>{body}</button> : <div key={i}>{body}</div>;
    })}
  </div>;
}

export function FractionLab({expression = ''}: {expression?: string}) {
  const [a, b] = parseAddends(expression) || [[1, 2], [1, 4]];
  const model = labModel(a, b);
  const [selected, setSelected] = useState<number[]>([]);
  const target = model.needA + model.needB;
  const done = selected.length === target && target > 0;
  const matchedA = selected.length === model.needA;
  const status = done
    ? `You built ${vulgar(model.sumN, model.sumD)}! The common denominator is ${model.lcm} — equal-sized pieces are why we need it.`
    : matchedA && model.needB > 0
      ? `That's ${vulgar(a[0], a[1])} = ${model.needA}/${model.lcm}. Now tap ${model.needB} more for ${vulgar(b[0], b[1])}.`
      : selected.length > target
        ? `Too many — tap extras to remove. You need ${target} of ${model.lcm}.`
        : `Tap ${model.needA} pieces to match ${vulgar(a[0], a[1])}. All bars are the same-sized whole.`;
  return <section className="card" aria-label="Fraction Lab">
    <h3>Fraction Lab · your sum: {vulgar(a[0], a[1])} + {vulgar(b[0], b[1])}</h3>
    <p>Build the sum yourself with equal-sized pieces — Mia only hints, never reveals.</p>
    <Bar of={a} fill={a[0]} label={`First addend ${vulgar(a[0], a[1])}`}/>
    <Bar of={b} fill={b[0]} label={`Second addend ${vulgar(b[0], b[1])}`}/>
    <p>Now build both on the shared grid:</p>
    <Bar of={[model.needA + model.needB, model.lcm]} fill={0} label={`Shared grid of ${model.lcm}`} interactive selected={selected} onToggle={i => setSelected(old => old.includes(i) ? old.filter(n => n !== i) : [...old, i])}/>
    <p role="status">{status}</p>
    <button type="button" className="text-button" onClick={() => setSelected([])}>Reset fraction bars</button>
    <p className="tiny">Interactive maths demonstration; works offline with no AI call.</p>
  </section>;
}
