import katex from 'katex';
export function MathText({value, latex = false}: {value: string; latex?: boolean}) {
  const input = latex ? value : value.replace(/\*/g, '\\cdot ');
  return <span className="math" dangerouslySetInnerHTML={{__html: katex.renderToString(input, {throwOnError: false, trust: false, strict: 'ignore', output: 'htmlAndMathml'})}}/>;
}
