"""Killable, concurrency-bounded workers for untrusted mathematical calculations."""
import multiprocessing as mp
from threading import BoundedSemaphore
from .math_parser import MathError

SLOTS = BoundedSemaphore(4)
TIMEOUT_SECONDS = 8
STARTUP_TIMEOUT_SECONDS = 20


def _worker(connection, operation, args):
    try:
        from . import maths
        connection.send(('ready', None))
        result = getattr(maths, operation)(*args)
        connection.send(('ok', result))
    except MathError as exc:
        connection.send(('error', str(exc)))
    except Exception:
        connection.send(('error', 'This expression could not be processed safely. Try a simpler supported question.'))
    finally:
        connection.close()


def calculate(operation, *args, timeout=TIMEOUT_SECONDS):
    if operation not in ('solve', 'analyze', 'expression', 'function_graph', 'review_work'):
        raise MathError('Unsupported calculation.')
    if not SLOTS.acquire(blocking=False):
        raise MathError('The maths engine is busy. Please try again shortly.')
    context = mp.get_context('spawn')
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(child, operation, args), daemon=True)
    try:
        if timeout <= 0:
            raise MathError('Calculation timed out. Please simplify the question.')
        process.start()
        child.close()
        # Windows starts a fresh interpreter for each worker. Importing SymPy on
        # a busy laptop must not consume the student's calculation budget.
        # Startup and calculation both remain bounded and killable.
        if not parent.poll(STARTUP_TIMEOUT_SECONDS):
            raise MathError('The maths worker could not start in time. Please try again.')
        try:
            status, value = parent.recv()
            if status == 'ready':
                if not parent.poll(timeout):
                    raise MathError('Calculation timed out. Please simplify the question.')
                status, value = parent.recv()
        except EOFError:
            raise MathError('Calculation stopped safely. Please simplify the question.')
        if status == 'error':
            raise MathError(value)
        return value
    finally:
        if process.pid:
            process.join(.1)
            if process.is_alive():
                process.terminate()
                process.join()
            process.close()
        parent.close()
        child.close()
        SLOTS.release()


def solve(equation, variable=None):
    return calculate('solve', equation, variable)


def analyze(steps):
    return calculate('analyze', steps)


def expression(source):
    return calculate('expression', source)


def answer_value(text):
    """Numeric value of a student answer: 4, 3/2, x = 4 or 4 = x.

    Accepts the natural variable = value form children actually type.
    Untrusted input stays inside the maths worker: each side of a single
    = is parsed separately and only a symbol-free side is accepted.
    """
    text = text.strip()
    if text.count('=') == 1:
        for side in text.split('=', 1):
            try:
                value = expression(side)
            except MathError:
                continue
            if not value.free_symbols:
                return value
        raise MathError('Enter a number or fraction, such as 4 or 3/2.')
    return expression(text)
