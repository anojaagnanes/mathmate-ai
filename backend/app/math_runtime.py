"""Killable, concurrency-bounded workers for untrusted mathematical calculations."""
import multiprocessing as mp
from threading import BoundedSemaphore
from .math_parser import MathError

SLOTS = BoundedSemaphore(4)
TIMEOUT_SECONDS = 8


def _worker(connection, operation, args):
    try:
        from . import maths
        result = getattr(maths, operation)(*args)
        connection.send(('ok', result))
    except MathError as exc:
        connection.send(('error', str(exc)))
    except Exception:
        connection.send(('error', 'This expression could not be processed safely. Try a simpler supported question.'))
    finally:
        connection.close()


def calculate(operation, *args, timeout=TIMEOUT_SECONDS):
    if operation not in ('solve', 'analyze', 'expression'):
        raise MathError('Unsupported calculation.')
    if not SLOTS.acquire(blocking=False):
        raise MathError('The maths engine is busy. Please try again shortly.')
    context = mp.get_context('spawn')
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(child, operation, args), daemon=True)
    try:
        process.start()
        child.close()
        if not parent.poll(timeout):
            raise MathError('Calculation timed out. Please simplify the question.')
        try:
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
