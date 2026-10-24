export type TeacherState = 'idle' | 'listening' | 'thinking' | 'explaining' | 'encouraging' | 'correct' | 'incorrect' | 'confused' | 'paused';
export const encouragement = {
  correct: "Wonderful! You solved that beautifully. Let's try the next step together.",
  incorrect: "That's a good attempt. Let's look at this step together and see what we can improve.",
  confused: "That's completely okay. We'll take just one step at a time. Keep both sides balanced by doing the same operation on each side.",
};
