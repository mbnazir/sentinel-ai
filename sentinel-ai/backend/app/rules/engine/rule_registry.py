from app.rules.engine.base_rule import BaseRule


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: list[BaseRule] = []

    def register(self, rule: BaseRule) -> None:
        self._rules.append(rule)

    def register_many(self, rules: list[BaseRule]) -> None:
        for rule in rules:
            self.register(rule)

    def all(self) -> list[BaseRule]:
        return list(self._rules)
