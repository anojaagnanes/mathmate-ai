def recommend(attempts, difficulty=1):
    recent = attempts[-5:]
    if not recent:
        return 1, 0, 'Start with a short practice to find your rhythm.'
    accuracy = sum(a.correct for a in recent) / len(recent)
    if len(recent) >= 5 and accuracy >= .8 and not any(a.hinted for a in recent):
        if difficulty == 3:
            return 3, accuracy, 'You are consistently successful at the hardest level. Keep practising to consolidate your skills.'
        return min(3, difficulty + 1), accuracy, 'At least 4 of your last 5 answers were correct without hints. Try a harder equation.'
    if len(recent) >= 3 and accuracy < .5:
        return max(1, difficulty - 1), accuracy, 'Recent accuracy is below 50%. Revisit balancing both sides, then try gentler practice.'
    return difficulty, accuracy, 'Keep practising at this level. Build consistency before moving up.'
