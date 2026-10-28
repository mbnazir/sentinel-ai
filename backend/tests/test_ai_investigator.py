import asyncio
import pytest
from app.ai.models import InvestigatorSummary
from app.ai.provider import DisabledProvider

def test_ai_summary_model_is_evidence_versioned():
    fields=InvestigatorSummary.model_fields
    assert "input_hash" in fields
    assert "prompt_version" in fields
    assert "narrative" in fields

def test_disabled_provider_fails_closed():
    with pytest.raises(RuntimeError):
        asyncio.run(DisabledProvider().summarize("evidence"))
