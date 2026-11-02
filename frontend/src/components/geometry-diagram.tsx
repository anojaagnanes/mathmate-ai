'use client';
import type { Solution } from '@/lib/types';

export function GeometryDiagram({diagram, active}: {diagram: NonNullable<Solution['diagram']>; active: boolean}) {
  return <figure className={`geometry-diagram ${active ? 'geometry-explaining' : ''}`}>
    <svg viewBox="0 0 320 200" role="img" aria-label={`${diagram.shape.replace('_', ' ')}. ${diagram.labels.join('. ')}. ${diagram.caption}`}>
      <g fill="#eeeafe" stroke="#6846e8" strokeWidth="3" strokeLinejoin="round">
        {diagram.shape === 'rectangle' && <rect className="geometry-outline" x="60" y="35" width="200" height="120" rx="2"/>}
        {diagram.shape === 'circle' && <><circle className="geometry-outline" cx="160" cy="95" r="65"/><path d="M160 95H225" strokeDasharray="5 4"/><circle cx="160" cy="95" r="3"/></>}
        {diagram.shape === 'triangle' && <><path className="geometry-outline" d="M55 155L265 155L125 30Z"/><path d="M125 30V155M125 140H140V155" fill="none" strokeDasharray="5 4"/></>}
        {diagram.shape === 'right_triangle' && <><path className="geometry-outline" d="M70 30V155H260Z"/><path d="M70 140H85V155" fill="none"/></>}
      </g>
    </svg>
    <figcaption>{diagram.labels.map(label => <span key={label}>{label}</span>)}<small>{diagram.caption}</small></figcaption>
  </figure>;
}
