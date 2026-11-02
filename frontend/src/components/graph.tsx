'use client';
import { useEffect, useRef, useState } from 'react';
import { post } from '@/lib/api';
import { MathText } from './math';
function LinearGraph() {
  const ref = useRef<HTMLDivElement>(null); const [slope, setSlope] = useState(2); const [intercept, setIntercept] = useState(1); const [error, setError] = useState(''); const [root, setRoot] = useState<number | null>(-.5);
  useEffect(() => {let dispose: (() => void) | undefined; let cancelled = false; import('jsxgraph').then(({default: JXG}) => {if (!ref.current || cancelled) return; const el = ref.current; const board = JXG.JSXGraph.initBoard(el, {boundingbox: [-6, 8, 6, -6], axis: true, showCopyright: false, showNavigation: true, keepaspectratio: true}); board.create('functiongraph', [(x: number) => slope * x + intercept], {strokeColor: '#6846E8', strokeWidth: 3}); board.create('point', [0, intercept], {name: '(0, b)', fixed: true, size: 4, fillColor: '#16a56a', strokeColor: '#16a56a'}); let timer = 0; const onResize = () => {window.clearTimeout(timer); timer = window.setTimeout(() => {board.resizeContainer(el.clientWidth, el.clientHeight);}, 150);}; window.addEventListener('resize', onResize); dispose = () => {window.removeEventListener('resize', onResize); window.clearTimeout(timer); JXG.JSXGraph.freeBoard(board);};}).catch(() => setError('The interactive graph could not load.')); post<{x_intercept: number | null}>('/math/graph', {slope, intercept}).then(r => {if (!cancelled) {setRoot(r.x_intercept); setError('');}}).catch(e => {if (!cancelled) setError(e.message);}); return () => {cancelled = true; dispose?.();};}, [slope, intercept]);
  return <section className="card"><span className="eyebrow">MAKE THE CONNECTION</span><h2>A small change. A different line.</h2><p>Move the sliders and watch what happens. Drag the graph to explore.</p><div className="graph-equation"><MathText value={`y = ${slope}x + (${intercept})`}/></div><div ref={ref} className="graph-board" aria-label={`Graph of y equals ${slope} x plus ${intercept}`}/><div className="two-cols"><label>Slope · m = {slope}<input type="range" min="-5" max="5" step=".5" value={slope} onChange={e => setSlope(Number(e.target.value))}/></label><label>Intercept · b = {intercept}<input type="range" min="-5" max="5" step=".5" value={intercept} onChange={e => setIntercept(Number(e.target.value))}/></label></div><p className="info-box">{slope === 0 ? intercept === 0 ? 'This line lies on the x-axis: every point is an x-intercept.' : 'A horizontal line above or below the x-axis has no x-intercept.' : `The line crosses the x-axis at x = ${root}. Each step right changes y by ${slope}.`}</p>{error && <p className="error" role="alert">{error}</p>}</section>;
}


type Plot = {segments: {x: number; y: number}[][]; latex: string; domain_conditions: string[]; note: string};
function FunctionGraph() {
  const ref = useRef<HTMLDivElement>(null);
  const request = useRef(0);
  const [expression, setExpression] = useState('x^2');
  const [plot, setPlot] = useState<Plot | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!plot) return;
    let cancelled = false;
    let dispose: (() => void) | undefined;
    import('jsxgraph').then(({default: JXG}) => {
      if (cancelled || !ref.current) return;
      const el = ref.current; const board = JXG.JSXGraph.initBoard(el, {boundingbox: [-5.5, 10, 5.5, -5], axis: true, showCopyright: false, showNavigation: true});
      plot.segments.forEach(segment => {
        if (segment.length === 1) board.create('point', [segment[0].x, segment[0].y], {name: '', fixed: true, size: 2});
        else board.create('curve', [segment.map(p => p.x), segment.map(p => p.y)], {strokeColor: '#6846E8', strokeWidth: 3});
      });
      let timer = 0; const onResize = () => {window.clearTimeout(timer); timer = window.setTimeout(() => {board.resizeContainer(el.clientWidth, el.clientHeight);}, 150);}; window.addEventListener('resize', onResize); dispose = () => {window.removeEventListener('resize', onResize); window.clearTimeout(timer); JXG.JSXGraph.freeBoard(board);};
    }).catch(() => {if (!cancelled) setError('The function graph could not load.');});
    return () => {cancelled = true; dispose?.();};
  }, [plot]);
  useEffect(() => () => {request.current += 1;}, []);
  async function draw(value = expression) {
    const id = ++request.current;
    setBusy(true); setError(''); setPlot(null);
    try {const result = await post<Plot>('/math/function-graph', {expression: value}); if (request.current === id) setPlot(result);}
    catch (e) {if (request.current === id) setError((e as Error).message);}
    finally {if (request.current === id) setBusy(false);}
  }
  return <section className="card"><span className="eyebrow">EXPLORE A FUNCTION</span><h2>From a formula to a curve.</h2><p>Enter a function of x. Try powers, sin, cos, tan, log, exp or sqrt. Angles are in radians and log is the natural logarithm. Samples cover −5 to 5.</p>
    <form onSubmit={e => {e.preventDefault(); void draw();}}><label>Function of x<input value={expression} maxLength={200} required onChange={e => {request.current += 1; setBusy(false); setExpression(e.target.value); setPlot(null); setError('');}}/></label><button className="pill" disabled={busy}>{busy ? 'Plotting…' : 'Plot function'}</button></form>
    <div className="actions">{['x^2','sin(x)','tan(x)','log(x)','sqrt(x)','exp(x)'].map(value => <button type="button" className="pill" key={value} onClick={() => {setExpression(value); void draw(value);}}>{value}</button>)}</div>
    {error && <p className="error-box" role="alert">{error}</p>}
    {plot ? <><MathText value={'y='+plot.latex} latex/><div ref={ref} className="graph-board" aria-label="Sampled function graph"/><p className="info-box">{plot.note}{plot.domain_conditions.length > 0 && ` Domain: ${plot.domain_conditions.join('; ')}.`}</p></> : <p className="tiny" aria-live="polite">{busy ? 'Calculating real graph points…' : 'Choose a function and press Plot function.'}</p>}
  </section>;
}

export function GraphPlayground() {return <div className="stack"><FunctionGraph/><LinearGraph/></div>;}
