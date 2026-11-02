from .maths import MathsAgent
from .vision import VisionAgent
from .teaching import TeachingAgent

class TeachingSession:
    """Routes only requested work: no automatic agent loops or model fan-out."""
    def __init__(self,provider=None):self.provider=provider
    async def extract(self,image,mime):return await VisionAgent(self.provider).extract(image,mime)
    async def review(self,steps):return await MathsAgent().review(steps)
    async def teach(self,review,language):return await TeachingAgent(self.provider).explain(review,language)
