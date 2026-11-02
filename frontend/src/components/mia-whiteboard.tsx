'use client';
import { useEffect, useRef, useState } from 'react';
import { MathText } from './math';
import { GeometryDiagram } from './geometry-diagram';
import { displayEquation } from '@/lib/teaching-language';
import type { Solution } from '@/lib/types';

/** Lesson board. Animates verified equations and diagrams character by character,
 *  and writes Mia's spoken answers out line by line while she says them. */
export function MiaWhiteboard({ items, step, playing, diagram, handwritten = false }: {
  items: { equation: string; latex?: string | null; plain?: boolean }[];
  step: number; playing: boolean; diagram?: Solution['diagram']; handwritten?: boolean;
}) {
  const [progress, setProgress] = useState(0);
  const [reduced, setReduced] = useState(false);
  const raf = useRef(0);

  useEffect(() => {
    const query = matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  useEffect(() => { setProgress(0); }, [step, items.length]);

  useEffect(() => {
    if (!playing || reduced) {
      if (reduced) setProgress(1);
      return;
    }
    const start = performance.now();
    const duration = 1400;
    const tick = (now: number) => {
      const v = Math.min(1, (now - start) / duration);
      setProgress(v);
      if (v < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [playing, reduced, step]);

  const current = items[step];
  if (!current) return <div className="mia-board" aria-label="Mia whiteboard"><p className="tiny">Board is ready.</p></div>;
  const display = items.map(s => s.plain ? s.equation : displayEquation(s.equation));
  const chars = Array.from(display[step]);
  const shown = reduced || !playing ? chars.length : Math.floor(chars.length * progress);

  return (
    <div className="mia-board" aria-label="Mia whiteboard, maths only" tabIndex={0}>
      <span className="eyebrow">Step {step + 1} / {items.length}</span>
      <ol className="mia-steps">
        {items.map((s, i) => {
          if (i > step) return null;
          const active = i === step;
          const text = active ? chars.slice(0, shown).join('') : handwritten ? display[i] : s.equation;
          return (
            <li key={i} aria-current={active ? 'step' : undefined} className={active ? 'mia-current' : 'mia-done'}>
              <span className="mia-step-no">{i + 1}</span>
              <span className="mia-equation">
                {handwritten ? text : <MathText value={s.latex && !active ? s.latex : text} latex={!!s.latex && !active} />}
                {active && playing && !reduced && <span className="mia-pen" aria-hidden="true" />}
              </span>
            </li>
          );
        })}
      </ol>
      {diagram && <GeometryDiagram diagram={diagram} active={playing} />}
    </div>
  );
}
