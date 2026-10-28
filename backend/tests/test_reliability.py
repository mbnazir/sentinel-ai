from app.reliability.metrics import ScanMetrics
from app.reliability.recovery import should_dead_letter

def test_dead_letter_threshold():
    assert not should_dead_letter(3,4)
    assert should_dead_letter(4,4)

def test_completion_ratio():
    m=ScanMetrics(10,7,1,100,50)
    assert m.completion_ratio==0.7
    assert ScanMetrics(0,0,0,0,0).completion_ratio==1.0
