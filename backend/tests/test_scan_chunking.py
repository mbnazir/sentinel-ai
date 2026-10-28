from datetime import date
from uuid import uuid4
import pytest
from app.workers.chunking import split_date_range, progress

def test_split_daily_chunks():
    chunks=split_date_range(uuid4(),date(2026,8,1),date(2026,8,3))
    assert len(chunks)==3 and chunks[0].date_from==date(2026,8,1) and chunks[-1].date_to==date(2026,8,3)

def test_split_multi_day_chunks():
    chunks=split_date_range(uuid4(),date(2026,8,1),date(2026,8,5),2)
    assert [(c.date_from,c.date_to) for c in chunks]==[(date(2026,8,1),date(2026,8,2)),(date(2026,8,3),date(2026,8,4)),(date(2026,8,5),date(2026,8,5))]

def test_invalid_range_rejected():
    with pytest.raises(ValueError): split_date_range(uuid4(),date(2026,8,2),date(2026,8,1))

def test_progress_counts_terminal_chunks():
    p=progress(10,6,1,1)
    assert p.percent_complete==80.0
