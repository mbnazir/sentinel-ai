# Activity Matching Engine

Milestone 4 adds confidence-based activity matching.

## Problem

Quartz activities from different sources should not be matched by ID. Agent, Supervisor, Manager, and Payroll versions may create new activity rows even when they represent edits to the same underlying time block.

## Matching signals

The matcher uses:

- time overlap
- start-time proximity
- end-time proximity
- duration similarity
- activity-type similarity

## Classification

The engine classifies matches as:

- exact
- extended
- shortened
- shifted
- type_changed
- partial_overlap
- inserted
- deleted
- no_match

## Why this matters

This makes activity-level fraud rules possible.

Examples:

- Agent inserted a manual activity not present in System.
- Supervisor extended an activity beyond what Agent requested.
- Manager changed activity type.
- Payroll inserted a payable block.
- A system/phone activity was deleted from a manual version.

## Next milestone

Milestone 5: Rule Engine and first deterministic integrity rules.
