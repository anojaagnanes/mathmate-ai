'use client';
import {useState} from 'react';
import {useMiaVoice} from '@/lib/mia-voice';
import {speechText} from '@/lib/teaching-language';
import {Button} from './ui/button';
import {Volume2} from 'lucide-react';

export type GuideStep = {en: string; ta: string; why_en: string; why_ta: string};
export type ConstructionGuide = {label: string; kind: string; title_en: string; title_ta: string; given: string; steps: GuideStep[]; checks: {en: string; ta: string}[]; diagram: Record<string, string>; source: string};

function Diagram({guide}: {guide: ConstructionGuide}) {
  const d = guide.diagram;
  const label = (x: number, y: number, text: string, anchor: 'start' | 'middle' = 'middle', size = 13) => <text x={x} y={y} textAnchor={anchor} fontSize={size} fill="#231454" fontWeight="600">{text}</text>;
  if (d.kind === 'perp_bisector') return <svg viewBox="0 0 360 200" role="img" aria-label={`Perpendicular bisector of ${d.p1}${d.p2}`}>
    <line x1="60" y1="110" x2="300" y2="110" stroke="#231454" strokeWidth="2.5"/>{label(52, 114, d.p1)}{label(308, 114, d.p2)}
    <path d="M95 55 A75 75 0 0 1 265 55 M95 165 A75 75 0 0 0 265 165" fill="none" stroke="#9981cc" strokeWidth="1.6" strokeDasharray="5,4"/>
    <line x1="180" y1="35" x2="180" y2="185" stroke="#6846e8" strokeWidth="2.5" strokeDasharray="7,4"/>
    <circle cx="180" cy="48" r="4" fill="#6846e8"/><circle cx="180" cy="172" r="4" fill="#6846e8"/>{label(196, 52, 'P')}{label(196, 176, 'Q')}
    <rect x="180" y="110" width="10" height="10" fill="none" stroke="#6846e8" strokeWidth="1.6"/>{label(180, 198, `locus: equidistant from ${d.p1}, ${d.p2}`, 'middle', 11)}
  </svg>;
  if (d.kind === 'tangent_circle') return <svg viewBox="0 0 360 200" role="img" aria-label={`Circle touching ${d.line} at ${d.at}, through ${d.thru}`}>
    <line x1="20" y1="150" x2="340" y2="150" stroke="#231454" strokeWidth="2.5"/>{label(330, 140, d.line, 'middle', 11)}
    <circle cx="150" cy="80" r="70" fill="none" stroke="#6846e8" strokeWidth="2.5"/>
    <circle cx="150" cy="150" r="4.5" fill="#d56a6a"/>{label(150, 168, d.at)}
    <circle cx="211" cy="45" r="4.5" fill="#d56a6a"/>{label(224, 48, d.thru)}
    <circle cx="150" cy="80" r="3.5" fill="#231454"/>{label(138, 84, 'O')}
    <line x1="150" y1="80" x2="150" y2="150" stroke="#9981cc" strokeWidth="1.4" strokeDasharray="5,4"/>
    <rect x="150" y="140" width="10" height="10" fill="none" stroke="#6846e8" strokeWidth="1.4"/>
  </svg>;
  if (d.kind === 'external_tangent') return <svg viewBox="0 0 360 200" role="img" aria-label={`Tangent from ${d.from} to the circle`}>
    <circle cx="140" cy="100" r="55" fill="none" stroke="#6846e8" strokeWidth="2.5"/>
    <circle cx="230" cy="100" r="90" fill="none" stroke="#9981cc" strokeWidth="1.4" strokeDasharray="5,4"/>
    <circle cx="320" cy="100" r="4.5" fill="#d56a6a"/>{label(320, 88, d.from)}
    <circle cx="140" cy="100" r="3.5" fill="#231454"/>{label(128, 104, 'O')}
    <line x1="320" y1="100" x2="157" y2="152" stroke="#231454" strokeWidth="2"/>{label(250, 150, d.given || 'given', 'middle', 11)}
    <line x1="320" y1="100" x2="157" y2="48" stroke="#d56a6a" strokeWidth="2.5" strokeDasharray="7,4"/>{label(250, 56, `new: ${d.from}T`, 'middle', 11)}
    <circle cx="157" cy="48" r="4" fill="#d56a6a"/>{label(145, 44, 'T')}
  </svg>;
  const right = d.right === '1';
  const leg = (v: string, seg: string) => v ? `${seg} = ${v} ${d.unit || 'cm'}` : `side ${seg}`;
  return <svg viewBox="0 0 360 200" role="img" aria-label={`Triangle ${d.a}${d.b}${d.c}`}>
    <line x1="70" y1="160" x2="300" y2="160" stroke="#231454" strokeWidth="2.5"/>
    <line x1="70" y1="160" x2="70" y2="45" stroke="#231454" strokeWidth="2.5"/>
    <line x1="70" y1="45" x2="300" y2="160" stroke="#6846e8" strokeWidth="2.5"/>
    {right && <rect x="70" y="144" width="16" height="16" fill="none" stroke="#6846e8" strokeWidth="1.8"/>}
    {label(62, 42, d.a)}{label(58, 178, d.b)}{label(310, 178, d.c)}
    {label(185, 182, leg(d.bc, `${d.b}${d.c}`), 'middle', 11)}{label(38, 105, leg(d.ab, `${d.a}${d.b}`), 'middle', 11)}
  </svg>;
}

export function ConstructionGuide({guides}: {guides: ConstructionGuide[]}) {
  const [index, setIndex] = useState(0);
  const guide = guides[Math.min(index, guides.length - 1)];
  const [lang, setLang] = useState<'en' | 'ta'>(() => /[\u0b80-\u0bff]/.test(guides[0]?.source || '') ? 'ta' : 'en');
  const voice = useMiaVoice(lang);
  const t = (en: string, ta: string) => lang === 'ta' ? ta : en;
  function hear() {
    const lines = [`${t('Guide', 'வழிகாட்டி')} ${guide.label}. ${t(guide.title_en, guide.title_ta)}.`];
    guide.steps.forEach((s, i) => lines.push(`${t('Step', 'படி')} ${i + 1}. ${t(s.en, s.ta)} ${t('Why?', 'ஏன்?')} ${t(s.why_en, s.why_ta)}`));
    voice.speak(speechText(lines.join(' ')));
  }
  return <section className="card construction-guide" aria-label="Construction guides">
    <span className="eyebrow">GEOMETRY · RULER + COMPASS</span>
    <div className="row between"><div className="row" role="tablist" aria-label="Construction parts">
      {guides.map((g, i) => <Button key={g.label} variant={i === index ? undefined : 'outline'} onClick={() => setIndex(i)} aria-selected={i === index} role="tab">{g.label}</Button>)}
    </div><label className="tiny">Language <select aria-label="Guide language" value={lang} onChange={e => setLang(e.target.value as 'en' | 'ta')}><option value="en">English</option><option value="ta">தமிழ்</option></select></label></div>
    <h3>{t(guide.title_en, guide.title_ta)}</h3>
    {guide.given && <p className="tiny">{t('Given:', 'கொடுத்தது:')} {guide.given}</p>}
    <Diagram guide={guide}/>
    <p className="tiny">{t('Schematic — not to scale. Follow the measurements in the steps.', 'விளக்கப் படம் — அளவில் இல்லை. படிகளிலுள்ள அளவுகளைப் பின்பற்றுக.')}</p>
    <ol className="construction-steps">{guide.steps.map((s, i) => <li key={i}><strong>{t(s.en, s.ta)}</strong><p className="tiny">{t('Why: ', 'ஏன்: ')}{t(s.why_en, s.why_ta)}</p></li>)}</ol>
    <div className="success-box"><strong>{t('Check your drawing', 'உங்கள் வரைபடத்தைச் சரிபார்க்கவும்')}</strong>{guide.checks.map((c, i) => <p key={i} className="tiny">{t(c.en, c.ta)}</p>)}
    <p className="tiny">{t('Instrument procedure — verify measurements on your drawing; this is not solver algebra.', 'கருவி-முறை படிகள் — உங்கள் வரைபடத்தில் அளவுகளைச் சரிபார்க்கவும்; இது தீர்வி கணிதம் அல்ல.')}</p></div>
    <div className="actions"><Button variant="outline" onClick={hear} disabled={voice.speaking}><Volume2 size={16}/>{voice.speaking ? t('Speaking…', 'பேசுகிறது…') : t('Hear Mia explain', 'மியா விளக்கக் கேளுங்கள்')}</Button></div>
    {voice.error && <p role="status" className="info-box">{voice.error}</p>}
  </section>;
}
