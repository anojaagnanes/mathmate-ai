class TeachingAgent:
    def __init__(self,provider):self.provider=provider
    async def explain(self,review,language):
        if not review.get('corrected',{}).get('verified'):
            raise ValueError('Verified mathematical context is required.')
        return await self.provider.teach_work(review,language)
