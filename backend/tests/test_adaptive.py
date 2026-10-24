from types import SimpleNamespace
from app.adaptive import recommend


def outcomes(values, hinted=False):
    return [SimpleNamespace(correct=v, hinted=hinted) for v in values]


def test_adaptation():
    assert recommend([], 1)[0] == 1
    assert recommend(outcomes([1,1,1,1,0]), 1)[0] == 2
    assert recommend(outcomes([1,1,1,1,1], True), 1)[0] == 1
    assert recommend(outcomes([0,0,1]), 2)[0] == 1
    assert recommend(outcomes([1,1,1,1,1]), 3)[0] == 3
