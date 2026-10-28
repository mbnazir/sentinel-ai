from typing import Protocol

from app.rules.context import RuleContext
from app.rules.models import RuleFinding


class IntegrityRule(Protocol):
    rule_id: str
    name: str

    def evaluate(self, context: RuleContext) -> tuple[RuleFinding, ...]: ...
