import type {Solution} from './types';
import {equalGroupsExample} from './question-teaching.ts';

export type ExampleLanguage='en'|'ta';
export type RealWorldExample={
  source:'local'; title:string; context:string; check:string;
  visual:'shopping'|'fraction'|'discount'|'room'|'journey'; values:number[];
  steps:Solution['steps'];
};
const close=(a:number,b:number)=>Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<1e-8;
const numberResult=(s:Solution)=>{const value=s.solution||'';if(/^\d+\/\d+$/.test(value)){const [a,b]=value.split('/').map(Number);return a/b;}return Number(value);};

/** Bounded, deterministic analogies. Unknown notation never receives an invented scenario. */
export function realWorldExample(question:string,solution:Solution,language:ExampleLanguage='en'):RealWorldExample|null {
  if(!solution.verified)return null;
  const tr=(en:string,ta:string)=>language==='ta'?ta:en;
  const q=question.replace(/\s/g,'');
  const step=(equation:string,en:string,ta:string)=>({equation,explanation:tr(en,ta)});
  const shopping=equalGroupsExample(question,solution);
  if(shopping){
    const {quantity:a,extra:b,total:c,answer:x,variable:v}=shopping;
    return {source:'local',title:tr('A notebook shop','குறிப்பேட்டுக் கடை'),visual:'shopping',values:[a,b,c,x],
      context:tr('Imaginary prices in Sri Lankan rupees, not market prices.','இவை இலங்கை ரூபாயில் கற்பனை விலைகள்; சந்தை விலைகள் அல்ல.'),
      check:tr(`If you buy one more notebook, how much would the total increase?`,`மேலும் ஒரு குறிப்பேடு வாங்கினால் மொத்த விலை எவ்வளவு அதிகரிக்கும்?`),
      steps:[step(`${a}${v} + ${b} = ${c}`,`Imagine buying ${a} identical notebooks and a pen costing ${b} rupees. Your total is ${c} rupees. ${v} is the price of one notebook.`,`${a} ஒரே மாதிரியான குறிப்பேடுகளையும் ${b} ரூபாய் பேனாவையும் வாங்குகிறீர்கள். மொத்தம் ${c} ரூபாய். ஒரு குறிப்பேட்டின் விலை ${v}.`),
        step(`${a}${v} = ${c} - ${b}`,`Set aside the pen's ${b} rupees. Subtract the same amount from both sides. The remaining money pays only for the notebooks.`,`பேனாவிற்கான ${b} ரூபாயை ஒதுக்குங்கள். இரு பக்கங்களிலும் அதே தொகையைக் கழிக்கிறோம். மீதிப் பணம் குறிப்பேடுகளுக்கு மட்டுமே.`),
        step(`${a}${v} = ${c-b}`,`That leaves ${c-b} rupees for ${a} identical notebooks.`,`${a} குறிப்பேடுகளுக்கு ${c-b} ரூபாய் மீதம் உள்ளது.`),
        step(`${v} = ${c-b} / ${a} = ${x}`,`Share ${c-b} rupees equally between ${a} notebooks. Each notebook costs ${x} rupees. If you buy one more, how much does the total increase?`,`${c-b} ரூபாயை ${a} குறிப்பேடுகளுக்குச் சமமாகப் பிரிக்கவும். ஒவ்வொன்றின் விலை ${x} ரூபாய். மேலும் ஒன்று வாங்கினால் மொத்தம் எவ்வளவு அதிகரிக்கும்?`)]};
  }
  let m=q.match(/^(\d{1,2})\/(\d{1,2})$/);
  if(m){const a=+m[1],b=+m[2];if(b<2||b>12||a<1||a>b||!close(numberResult(solution),a/b))return null;
    return {source:'local',title:tr('Sharing a pizza','பீட்சாவைப் பகிர்வோம்'),visual:'fraction',values:[a,b],context:tr('Every slice has the same area.','ஒவ்வொரு துண்டின் பரப்பளவும் சமம்.'),check:tr('How many slices are left?','எத்தனை துண்டுகள் மீதம் உள்ளன?'),steps:[step(`${a}/${b}`,`Cut one pizza into ${b} equal slices. Each slice is one ${b}th of the whole.`,`ஒரு பீட்சாவை ${b} சம துண்டுகளாகப் பிரிக்கவும். ஒவ்வொரு துண்டும் முழுப் பீட்சாவின் 1/${b} பங்கு.`),step(`${a}/${b}`,`Select ${a} of those ${b} slices. The selected fraction is ${a} over ${b}. How many slices are left?`,`${b} துண்டுகளில் ${a} துண்டுகளைத் தேர்ந்தெடுக்கவும். தேர்ந்தெடுத்த பங்கு ${a}/${b}. எத்தனை துண்டுகள் மீதம் உள்ளன?`)]};
  }
  m=q.match(/^rectangle_area\((\d{1,3}),(\d{1,3})\)$/);
  if(m){const a=+m[1],b=+m[2];if(!a||!b||!close(numberResult(solution),a*b))return null;
    return {source:'local',title:tr('Measuring a room','அறையை அளப்போம்'),visual:'room',values:[a,b],context:tr('For this illustration, lengths are metres.','இந்த எடுத்துக்காட்டில் நீளம் மீட்டரில் உள்ளது.'),check:tr('If the width doubles, what happens to the floor area?','அகலம் இரட்டிப்பானால் பரப்பளவு என்ன ஆகும்?'),steps:[step(`${a} × ${b}`,`Imagine a rectangular room ${a} metres long and ${b} metres wide. We want its floor area.`,`${a} மீட்டர் நீளமும் ${b} மீட்டர் அகலமும் கொண்ட செவ்வக அறையை நினைத்துப் பாருங்கள். தரையின் பரப்பளவைக் காண்போம்.`),step(`${a} × ${b} = ${a*b}`,`Multiply length by width. The floor covers ${a*b} square metres. If the width doubles, what happens to the area?`,`நீளத்தை அகலத்தால் பெருக்கவும். பரப்பளவு ${a*b} சதுர மீட்டர். அகலம் இரட்டிப்பானால் பரப்பளவு என்ன ஆகும்?`)]};
  }
  m=q.match(/^(\d{1,3})\/100\*(\d{1,5})$/);
  if(m){const p=+m[1],price=+m[2],saving=p*price/100;if(p>100||p<=0||!price||!close(numberResult(solution),saving))return null;
    return {source:'local',title:tr('A shop discount','கடைத் தள்ளுபடி'),visual:'discount',values:[p,price,saving],context:tr('Illustrative Sri Lankan rupee prices. The original question calculates the saving.','கற்பனை இலங்கை ரூபாய் விலைகள். அசல் கேள்வி சேமிப்பைக் கணக்கிடுகிறது.'),check:tr('Is the discount the amount saved or the final price?','தள்ளுபடி என்பது சேமிப்பா அல்லது இறுதி விலையா?'),steps:[step(`${p}/100 × ${price}`,`Imagine a ${price} rupee item with ${p} percent off. Percent means out of one hundred.`,`${price} ரூபாய் பொருளுக்கு ${p} சதவீதத் தள்ளுபடி. சதவீதம் என்பது நூற்றில் ஒரு பங்கு.`),step(`${p}/100 × ${price} = ${saving}`,`You save ${saving} rupees. The final price is ${(price-saving).toFixed(2)} rupees. The answer to the original question is the saving, not the final price.`,`${saving} ரூபாய் சேமிக்கிறீர்கள். இறுதி விலை ${(price-saving).toFixed(2)} ரூபாய். அசல் கேள்வியின் விடை சேமிப்புத் தொகையாகும்.`)]};
  }
  m=q.match(/^y=(\d{1,2})\*?x$/);
  if(m){const speed=+m[1];const result=(solution.solution||'').replace(/\s/g,'');
    if(speed<1||!['unique','parametric'].includes(solution.kind)||solution.variable!=='y'||result!==`${speed}*x`)return null;
    return {source:'local',title:tr('A steady journey','சீரான பயணம்'),visual:'journey',values:[speed],context:tr('Interpret x as hours and y as kilometres, at a constant speed.','x என்பது மணிநேரம்; y என்பது கிலோமீட்டர். வேகம் மாறாது.'),check:tr('What distance is reached after four hours?','நான்கு மணி நேரத்தில் எவ்வளவு தூரம் செல்லலாம்?'),steps:[step(`y = ${speed}x`,`Imagine travelling at ${speed} kilometres per hour. Distance is speed times time.`,`${speed} கிலோமீட்டர் மணிவேகத்தில் பயணம் செய்வதாக நினைக்கவும். தூரம் என்பது வேகமும் நேரமும் பெருக்கப்பட்ட மதிப்பு.`),step(`y = ${speed} × 2 = ${speed*2}`,`After two hours, you have travelled ${speed*2} kilometres. The graph rises evenly because the speed stays constant. What happens after four hours?`,`இரண்டு மணி நேரத்தில் ${speed*2} கிலோமீட்டர் சென்றுள்ளீர்கள். வேகம் மாறாததால் வரைபடம் சீராக உயர்கிறது. நான்கு மணி நேரத்தில் எவ்வளவு தூரம் செல்லலாம்?`)]};
  }
  return null;
}
