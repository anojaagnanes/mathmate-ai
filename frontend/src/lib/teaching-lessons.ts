export type TeachingStep = {equation: string; narration: string; simple: string};
export type TeachingLessonData = {title: string; equation: string; answer: string; steps: TeachingStep[]; verification: TeachingStep; shopping?: {item: string; quantity: number; extra: number; total: number; narration: string}};

export const firstAlgebraLesson: TeachingLessonData = {
  title: 'Two notebooks and a little algebra', equation: '2x + 6 = 14', answer: '4',
  steps: [
    {equation: '2x + 6 = 14', narration: 'Let’s take this slowly. Two times x, plus six, equals fourteen. We want to find x. Think of the equals sign as a balanced scale.', simple: 'There are two equal unknown amounts and six extra. Together they make fourteen.'},
    {equation: '2x = 14 - 6', narration: 'Subtract six from both sides. On the left, plus six and minus six cancel. On the right, we have fourteen minus six. The balance stays the same.', simple: 'Take away the extra six from each side. Now only two x are left on the left side.'},
    {equation: '2x = 8', narration: 'Fourteen minus six is eight. So two times x equals eight.', simple: 'Two equal amounts add up to eight.'},
    {equation: 'x = 8 / 2', narration: 'Divide both sides by two. Two x divided by two is x. On the right, divide eight by two.', simple: 'Share eight equally between two groups. Each group is x.'},
    {equation: 'x = 4', narration: 'Eight divided by two is four. So x equals four. You’re doing well. Let’s check that answer in the original equation.', simple: 'Each equal group contains four. Our answer is four.'},
  ],
  verification: {equation: '2(4) + 6 = 8 + 6 = 14', narration: 'Replace x with four in the original equation. Two times four is eight. Eight plus six is fourteen, matching the right side. The solution is verified. Wonderful work!', simple: 'Put four back in place of x. Four plus four plus six makes fourteen. It works!'},
  shopping: {item: 'Notebook', quantity: 2, extra: 6, total: 14, narration: 'Imagine buying two notebooks at x rupees each and a pen costing six rupees. The bill is fourteen rupees. Take away the pen’s six rupees, leaving eight for the notebooks. Share eight equally between two notebooks: each costs four rupees.'},
};

/** Additional bounded linear lessons share the same player, not custom UI. */
function shoppingLesson(quantity: number, extra: number, total: number): TeachingLessonData {
  const remainder = total - extra;
  const answer = remainder / quantity;
  const equation = `${quantity}x + ${extra} = ${total}`;
  return {
    title: `${quantity} notebooks: find the price`, equation, answer: String(answer),
    steps: [
      {equation, narration: `We have ${quantity} equal notebook prices and a pen costing ${extra} rupees. Together they cost ${total} rupees. Let x be the price of one notebook.`, simple: `Find the price of one of the ${quantity} identical notebooks.`},
      {equation: `${quantity}x = ${total} - ${extra}`, narration: `Subtract ${extra} from both sides. This removes the pen cost without changing the balance.`, simple: `Take away the pen cost from the total.`},
      {equation: `${quantity}x = ${remainder}`, narration: `${total} minus ${extra} is ${remainder}. That is the cost of all ${quantity} notebooks.`, simple: `The notebooks together cost ${remainder} rupees.`},
      {equation: `x = ${remainder} / ${quantity}`, narration: `Divide both sides by ${quantity}. We split the notebook total into ${quantity} equal parts.`, simple: `Share ${remainder} equally between ${quantity} notebooks.`},
      {equation: `x = ${answer}`, narration: `Each notebook costs ${answer} rupees. Let’s check our answer.`, simple: `One notebook costs ${answer} rupees.`},
    ],
    verification: {equation: `${quantity}(${answer}) + ${extra} = ${remainder} + ${extra} = ${total}`, narration: `${quantity} times ${answer} is ${remainder}. Add ${extra} for the pen and we get ${total}. This matches the original total. Well done!`, simple: `Put ${answer} back for x. Both sides give ${total}. It works!`},
    shopping: {item: 'Notebook', quantity, extra, total, narration: `Buy ${quantity} notebooks at x rupees each and a pen for ${extra} rupees. The total is ${total}. Remove the pen cost to get ${remainder}, then divide equally by ${quantity}. Each notebook costs ${answer} rupees.`},
  };
}
export const teachingLessons = [firstAlgebraLesson, shoppingLesson(3, 5, 20), shoppingLesson(4, 8, 32)];
