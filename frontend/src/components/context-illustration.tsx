'use client';
/** Decorative context only: never represents unverified quantities or measurements. */
export type ContextKind='pizza'|'coffee'|'cake'|'chocolate'|'objects';
export function contextKind(context:string):ContextKind{return /pizza/i.test(context)?'pizza':/coffee/i.test(context)?'coffee':/cake/i.test(context)?'cake':/chocolate/i.test(context)?'chocolate':'objects';}
export function ContextIllustration({context}:{context:string}){
 const kind=contextKind(context);
 return <div className="context-illustration"><svg viewBox="0 0 360 120" role="img" aria-label={`${context}: decorative illustration, not to scale`}>
  <ellipse cx="180" cy="108" rx="100" ry="8" fill="#ded5fa"/>
  <g className="context-float">
   {kind==='pizza'?<><circle cx="180" cy="58" r="45" fill="#e8a251"/><circle cx="180" cy="58" r="37" fill="#ffe18c"/><path d="M180 21V95M143 58H217" stroke="#fff8df" strokeWidth="3"/><circle cx="164" cy="42" r="6" fill="#d56a6a"/><circle cx="198" cy="72" r="6" fill="#d56a6a"/></>:kind==='coffee'?<><path d="M220 44h12a16 16 0 010 32h-12" fill="none" stroke="#6846e8" strokeWidth="9"/><path d="M135 35h85v40q0 25-42 25t-43-25z" fill="#a38aed"/><ellipse cx="178" cy="35" rx="43" ry="10" fill="#765444"/><path d="M165 23q-10-10 0-20m27 20q-10-10 0-20" fill="none" stroke="#c7bbeb" strokeWidth="3"/></>:kind==='cake'?<><path d="M130 49l80-25 25 64-105 10z" fill="#edb4cd"/><path d="M130 67l105-10M130 85l105-10" stroke="#fff1e7" strokeWidth="9"/><path d="M130 49l80-25 25 20-105 22z" fill="#b88be3"/></>:kind==='chocolate'?<><rect x="115" y="22" width="130" height="76" rx="10" fill="#765044"/><path d="M158 22v76M202 22v76M115 60h130" stroke="#b48a75" strokeWidth="4"/></>:<><rect x="112" y="35" width="60" height="62" rx="12" fill="#a38aed"/><circle cx="210" cy="65" r="33" fill="#eab0cf"/><path d="M155 22l18-18 18 18" fill="#d7c5fa"/></>}
  </g></svg><p className="tiny">Illustrative setting · the verified quantities are in the explanation.</p></div>;
}
