// Run with Node's TypeScript stripping (Node 22+) and the existing backend venv.
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {teachingLessons} from '../src/lib/teaching-lessons.ts';

const backend = fileURLToPath(new URL('../../backend/', import.meta.url));
const python = path.join(backend, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const result = execFileSync(python, ['-c', `
import json, sys
from app.maths import analyze, solve
lessons = json.load(sys.stdin)
assert len(lessons) == 3
for lesson in lessons:
    assert analyze([s['equation'] for s in lesson['steps']])['valid']
    result = solve(lesson['equation'])
    assert result['verified'] and result['solution'] == lesson['answer']
    assert not analyze([lesson['equation'], 'x = 999'])['valid']
    shop = lesson['shopping']
    assert shop['quantity'] * int(lesson['answer']) + shop['extra'] == shop['total']
    for expression in lesson['verification']['equation'].split('='):
        assert solve(expression.strip())['solution'] == str(shop['total'])
print('PASS: all 3 lessons: transformations, verified answer, wrong-step rejection, shopping equivalence, substitution')
`], {cwd: backend, input: JSON.stringify(teachingLessons), encoding: 'utf8'});
process.stdout.write(result);
