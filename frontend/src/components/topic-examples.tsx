'use client';
import { exampleTopics } from '@/lib/topic-examples';

export function TopicExamples({onSelect}: {onSelect: (example: string) => void}) {
  return <section className="topic-example-section" aria-labelledby="practice-examples-heading">
    <h2 id="practice-examples-heading">Choose a practice question</h2>
    <p>Select an example to fill your question box, then press Submit question. You can edit it first.</p>
    <div className="two-cols">
      {exampleTopics.map(topic => <article className="card topic-example-card" key={topic.title}>
        <span className="pill green">Supported now</span>
        <h3>{topic.title}</h3>
        <p>{topic.description}</p>
        {topic.review && <small className="tiny">Written questions include an interpretation review step.</small>}
        <div className="topic-example-list">
          {topic.examples.map(example => <button type="button" key={example} className="topic-example-button" onClick={() => onSelect(example)} aria-label={`Use example: ${example}`}>
            <span>{example}</span><span aria-hidden="true">→</span>
          </button>)}
        </div>
      </article>)}
    </div>
    <aside className="info-box" aria-label="Features not yet available">
      <strong>Not yet supported</strong>
      <p>Unrestricted word problems, understanding uploaded geometry diagrams, and arbitrary advanced mathematics are not available. Handwritten maths recognition is best-effort and always needs review.</p>
    </aside>
  </section>;
}
