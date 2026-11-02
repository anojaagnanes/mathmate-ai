from pydantic import BaseModel, Field

class VisionResult(BaseModel):
    steps: list[str] = Field(max_length=30)
    ambiguous_lines: list[int]
    requires_confirmation: bool = True
    provider: str

class VisionAgent:
    def __init__(self, provider): self.provider=provider
    async def extract(self, image: bytes, mime: str):
        steps=await self.provider.transcribe(image,mime)
        return VisionResult(steps=steps,ambiguous_lines=[i+1 for i,line in enumerate(steps) if '?' in line],provider=getattr(self.provider,'name','Configured recognizer'))
