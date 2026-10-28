from datetime import date
from uuid import uuid4
from app.workers.chunking import split_date_range
from app.workers.pipeline import ENGINE_VERSION,RULE_VERSION

def test_engine_versions_are_explicit():
    assert ENGINE_VERSION=="0.9.0"
    assert RULE_VERSION.startswith("builtin-24")

def test_chunks_have_stable_indices_for_resume():
    sid=uuid4()
    a=split_date_range(sid,date(2026,8,1),date(2026,8,4),1)
    b=split_date_range(sid,date(2026,8,1),date(2026,8,4),1)
    assert [(x.chunk_index,x.date_from,x.date_to) for x in a]==[(x.chunk_index,x.date_from,x.date_to) for x in b]
