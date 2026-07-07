# Timeline / Evidence Visualization UI

Milestone 12 introduces activity-level evidence visualization in the dashboard.

## Purpose

Investigators should not rely only on text summaries. They need to see how activity versions changed across System, Agent, Supervisor, Manager, and Payroll.

## Added UI

- timeline lane visualization
- source lanes
- activity blocks
- risk coloring
- timeline-specific findings
- demo timeline evidence

## Supported risk indicators

- normal
- inserted
- extended
- deleted / missing
- type changed
- shifted

## Current limitation

Milestone 12 uses demo timeline data in the frontend. Backend-backed timeline APIs already exist as scaffolds, but full persistence-backed timeline retrieval should be wired in a later milestone.
