export type Gesture = 'rest' | 'open' | 'point' | 'count' | 'celebrate' | 'reassure';
/** Finite, event-relative gestures, with quiet gaps instead of repeating arm waves. */
export function gestureAt(state: string, elapsed: number, step?: number): Gesture {
  if(state==='correct')return elapsed<2.8?'celebrate':'rest';
  if(state==='incorrect'||state==='confused')return elapsed<3?'reassure':'rest';
  if(state!=='explaining')return 'rest';
  if(elapsed<.35)return 'rest';
  if(elapsed<2.8)return step && step<=5 ? 'count':'open';
  if(elapsed<4)return 'rest';
  if(elapsed<6.8)return step?'point':'open';
  if(elapsed<9)return 'rest';
  if(elapsed<11.5)return 'open';
  return 'rest';
}
