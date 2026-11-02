from starlette.concurrency import run_in_threadpool
from ..math_runtime import calculate

class MathsAgent:
    async def review(self, steps):
        return await run_in_threadpool(calculate,'review_work',steps)
