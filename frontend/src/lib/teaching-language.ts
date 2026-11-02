export type TeachingLanguage='en'|'ta';
export function matchesLanguage(lang:string,language:TeachingLanguage){return lang.toLowerCase().split(/[-_]/)[0]===language;}
export function selectNarrationVoice<T extends {lang:string;voiceURI:string;name?:string}>(voices:T[],saved:string,language:TeachingLanguage){
  const matching=voices.filter(v=>matchesLanguage(v.lang,language));
  const keep=matching.find(v=>v.voiceURI===saved);
  if(keep)return keep;
  if(language==='en'){const clara=matching.find(v=>/clara/i.test(v.name||''));if(clara)return clara;}
  return matching[0];
}
/** Translate known deterministic teaching operations, never generate a new mathematical step. */
export function tamilStep(explanation:string):string {
  if(/[\u0B80-\u0BFF]/.test(explanation))return explanation;
  const known:Record<string,string>={
    'Start with the original equation.':'அசல் சமன்பாட்டிலிருந்து தொடங்குவோம்.',
    'Read the fractions being added.':'கூட்ட வேண்டிய பின்னங்களைப் பாருங்கள்.',
    'Use a common denominator; multiply each numerator and denominator by the same factor.':'பொதுவான பகுதியை அமைக்கவும். ஒவ்வொரு பின்னத்தின் தொகுதியையும் பகுதியையும் ஒரே எண்ணால் பெருக்கவும்.',
    'Add the numerators and keep the common denominator.':'தொகுதிகளைக் கூட்டவும். பொதுவான பகுதியை மாற்ற வேண்டாம்.',
    'Simplify the resulting fraction.':'கிடைத்த பின்னத்தைச் சுருக்கவும்.',
    'Read the fraction.':'பின்னத்தைப் பாருங்கள்.',
    'Divide numerator and denominator by the same nonzero common factor.':'தொகுதியையும் பகுதியையும் ஒரே பொதுக் காரணியால் வகுத்துச் சுருக்கவும். பூஜ்ஜியத்தால் வகுக்கக் கூடாது.',
    'Compare the two fractions.':'இரண்டு பின்னங்களையும் ஒப்பிடுவோம்.',
    'Rewrite with a common denominator.':'பொதுவான பகுதியுடன் பின்னங்களை எழுதவும்.',
    'Compare the numerators with the common positive denominator.':'ஒரே நேர்மறைப் பகுதி உள்ளதால் தொகுதிகளை ஒப்பிடவும்.',
    "Let's slow down.":'மெதுவாகப் பார்ப்போம்.',
    'Here is another way to see it.':'இதை வேறு விதமாகப் பார்ப்போம்.',
    'Picture equal groups on the board.':'பலகையில் சமமான குழுக்களாகக் கற்பனை செய்யுங்கள்.',
    'Take your time. Tell me which step feels unclear.':'அவசரம் வேண்டாம். எந்தப் படி கடினமாக உள்ளது என்று சொல்லுங்கள்.',
    'Read the expression.':'கோவையைப் படியுங்கள்.',
    'Read the inequality over real numbers.':'மெய் எண்களில் சமனின்மையைப் படியுங்கள்.'
  };
  if(known[explanation])return known[explanation];
  let match=explanation.match(/^Subtract (.+) from both sides, then collect like terms\.$/);
  if(match)return `இரு பக்கங்களிலிருந்தும் ${match[1]} ஐக் கழிக்கவும். பின்னர் ஒத்த உறுப்புகளைச் சேர்க்கவும்.`;
  match=explanation.match(/^Subtract (.+) times (.+) from both sides and collect the (.+) terms\.$/);
  if(match)return `இரு பக்கங்களிலிருந்தும் ${match[1]} மடங்கு ${match[2]} ஐக் கழித்து, ${match[3]} உறுப்புகளைச் சேர்க்கவும்.`;
  match=explanation.match(/^Divide both sides by (.+), the nonzero coefficient of (.+)\.$/);
  if(match)return `இரு பக்கங்களையும் ${match[1]} ஆல் வகுக்கவும். இது ${match[2]} இன் பூஜ்ஜியமல்லாத கெழு.`;
  match=explanation.match(/^Simplify to isolate (.+)\.$/);
  if(match)return `${match[1]} ஐத் தனியாகப் பெற எளிமைப்படுத்தவும்.`;
  return 'இந்தப் படிக்கான விரிவான தமிழாக்கம் இன்னும் இல்லை. பலகையில் உள்ள சரிபார்க்கப்பட்ட கணிதத்தைப் பாருங்கள். விரிவான விளக்கத்திற்கு ஆங்கிலத்தைத் தேர்ந்தெடுக்கலாம்.';
}

/** Human-readable form of a verified solver equation for the whiteboard.
 *  The solver emits programmer notation (2*x, x**2, sqrt); the board must
 *  show the maths the student submitted (2x, x², √). Purely presentational:
 *  the verified equation underneath never changes. */
export function displayEquation(equation:string):string{
  const superDigits:Record<string,string>={'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','-':'⁻','+':'⁺'};
  const toSuper=(digits:string)=>digits.split('').map(c=>superDigits[c]||c).join('');
  return equation
    .replace(/sqrt\(/gi,'√(')
    .replace(/\*\*\s*(-?\d+)/g,(_,d:string)=>toSuper(d))
    .replace(/\^\s*(-?\d+)/g,(_,d:string)=>toSuper(d))
    .replace(/\s*\*\s*(?=[A-Za-z(])/g,'')
    .replace(/(\d)\s*\*\s*(\d)/g,'$1×$2')
    .replace(/\*/g,'×');
}

/** Board lines for a spoken answer: strip markdown, split into short written lines.
 *  No lookbehind: older browsers lack it, so sentences split via match. */
export function answerLines(text:string):string[]{
  const clean=text.replace(/```[\s\S]*?```/g,' ').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*_#`>]/g,'');
  return clean.split(/\r?\n+/).flatMap(line=>line.match(/[^.!?]+[.!?]+|[^.!?]+$/g)??[]).map(s=>s.replace(/\s+/g,' ').trim()).filter(s=>s.length>0);
}

/** True when the student asks for a picture, diagram or drawing (English or Tamil). */
export function wantsVisual(text:string):boolean{
  return /diagram|draw|picture|image|show|visual|figure|graph|sketch|illustrat|example|pizza|coffee|cake|chocolate|படம்|வரைபடம்|வரை|காட்டு|உதாரணம்|பீட்சா|காபி|கேக்|சாக்லெட்/i.test(text);
}

/** Spoken-word form of narration for young listeners.
 *  Emojis and decoration become silence; math operators become words.
 *  Tamil script is untouched; only ASCII decoration changes. */
export function speechText(text:string):string{
  return text
    .replace(/[\u2018\u2019]/g,"'")
    .replace(/[—–]/g,', ')
    .replace(/[©®™\u2000-\u206F\u2600-\u27BF\u2B00-\u2BFF\u{1F000}-\u{1FAFF}\uFE0F]/gu,' ')
    .replace(/(\d)\s*\/\s*(\d)/g,'$1 over $2')
    .replace(/\//g,', ')
    .replace(/([A-Za-z0-9)\]}])\s*=\s*/g,'$1 equals ')
    .replace(/\+/g,' plus ')
    .replace(/(\d|\s)-(\d|\s)/g,'$1 minus $2')
    .replace(/([A-Za-z0-9)\]}])\s*\*\s*(?=[A-Za-z0-9([{])/g,'$1 times ')
    .replace(/[×·⋅]/g,' times ')
    .replace(/\*/g,' ')
    .replace(/÷/g,' divided by ')
    .replace(/%/g,' percent ')
    .replace(/√/g,' square root of ')
    .replace(/sqrt\(/gi,' square root of ')
    .replace(/\^/g,' to the power of ')
    .replace(/["“”«»`#_~|\\]/g,' ')
    .replace(/[(){}\[\]]/g,' ')
    .replace(/\s+/g,' ')
    .trim();
}
