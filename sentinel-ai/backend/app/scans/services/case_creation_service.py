class CaseCreationService:
    """Creates investigation cases for high-risk scan results.

    Current scaffold:
    - threshold evaluation
    - duplicate suppression hook
    - evidence snapshot hook
    """

    def should_create_case(self, risk_score:int, threshold:int)->bool:
        return risk_score>=threshold
