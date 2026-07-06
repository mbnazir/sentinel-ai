# Rule Engine

Milestone 5 introduces the deterministic integrity rule engine.

## Design

Each rule is a small plugin-style Python class implementing `BaseRule`.

```python
class SomeRule(BaseRule):
    def evaluate(self, context: RuleContext) -> list[RuleResult]:
        ...
```

## Rule input

Rules consume:

- reconstructed timelines
- activity matches
- source comparisons
- normalized evidence

Rules do not access raw Quartz tables.

## Initial deterministic rules

- inserted manual activity
- deleted baseline activity
- extended manual activity
- changed activity type
- manual source duration increase

## Output

Every rule returns structured `RuleResult` objects:

- rule id
- rule name
- severity
- score
- reason
- evidence

## Important

Sentinel AI should never claim fraud as a legal conclusion. It should report integrity risk and evidence.
