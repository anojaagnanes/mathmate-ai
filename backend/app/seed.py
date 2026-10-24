from sqlalchemy import select
from .db import SessionLocal
from .models import Topic, Lesson, LessonStep
from .maths import solve


def seed():
    with SessionLocal() as db:
        for topic_id, title, description in [('equations', 'Linear equations', 'Bring balance to algebra, one step at a time.'), ('graphs', 'Linear functions', 'See how slope and intercept shape a straight line.')]:
            if not db.get(Topic, topic_id):
                db.add(Topic(id=topic_id, title=title, description=description))
        db.flush()
        for id, topic, title, equation in [('balance', 'equations', 'The art of balance', '2x + 3 = 11'), ('both-sides', 'equations', 'Variables on both sides', '3x + 2 = x + 10'), ('intercepts', 'graphs', 'Find the x-intercept', '2x + 4 = 0')]:
            if not db.get(Lesson, id):
                db.add(Lesson(id=id, topic_id=topic, title=title, equation=equation))
                db.flush()
                for i, step in enumerate(solve(equation)['steps']):
                    db.add(LessonStep(lesson_id=id, position=i, content=step))
        db.commit()


if __name__ == '__main__':
    seed()
