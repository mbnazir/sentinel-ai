from app.rules.activity.deleted_baseline_activity_rule import DeletedBaselineActivityRule
from app.rules.activity.extended_manual_activity_rule import ExtendedManualActivityRule
from app.rules.activity.inserted_manual_activity_rule import InsertedManualActivityRule
from app.rules.activity.type_changed_activity_rule import TypeChangedActivityRule
from app.rules.session.manual_source_duration_increase_rule import ManualSourceDurationIncreaseRule
from app.timeline.domain.source import DataSource


def build_default_rules():
    return [
        InsertedManualActivityRule(DataSource.SYSTEM, DataSource.AGENT),
        InsertedManualActivityRule(DataSource.SYSTEM, DataSource.SUPERVISOR),
        InsertedManualActivityRule(DataSource.SYSTEM, DataSource.MANAGER),
        InsertedManualActivityRule(DataSource.SYSTEM, DataSource.PAYROLL),
        DeletedBaselineActivityRule(DataSource.SYSTEM, DataSource.AGENT),
        DeletedBaselineActivityRule(DataSource.SYSTEM, DataSource.SUPERVISOR),
        ExtendedManualActivityRule(DataSource.SYSTEM, DataSource.AGENT),
        ExtendedManualActivityRule(DataSource.SYSTEM, DataSource.SUPERVISOR),
        ExtendedManualActivityRule(DataSource.SYSTEM, DataSource.MANAGER),
        ExtendedManualActivityRule(DataSource.SYSTEM, DataSource.PAYROLL),
        TypeChangedActivityRule(DataSource.SYSTEM, DataSource.AGENT),
        TypeChangedActivityRule(DataSource.SYSTEM, DataSource.SUPERVISOR),
        ManualSourceDurationIncreaseRule(DataSource.SYSTEM, DataSource.AGENT, threshold_seconds=1800),
        ManualSourceDurationIncreaseRule(DataSource.SYSTEM, DataSource.SUPERVISOR, threshold_seconds=1800),
        ManualSourceDurationIncreaseRule(DataSource.SYSTEM, DataSource.MANAGER, threshold_seconds=1800),
        ManualSourceDurationIncreaseRule(DataSource.SYSTEM, DataSource.PAYROLL, threshold_seconds=1800),
    ]
