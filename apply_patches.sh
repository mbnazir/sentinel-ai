#!/bin/bash

set -euo pipefail

PATCHES=(
  "$HOME/Downloads/milestone-25-anomaly-risk-integration.patch"
  "$HOME/Downloads/milestone-26-persisted-anomaly-findings.patch"
  "$HOME/Downloads/milestone-27-anomaly-case-attachment.patch"
  "$HOME/Downloads/milestone-28-investigation-queue-intelligence.patch"
  "$HOME/Downloads/milestone-29-router-registry-platform-refactor.patch"
  "$HOME/Downloads/milestone-30-background-job-framework.patch"
  "$HOME/Downloads/milestone-31-persistent-jobs-real-handlers.patch"
  "$HOME/Downloads/milestone-32-scheduled-job-automation.patch"
  "$HOME/Downloads/milestone-33-worker-runtime.patch"
  "$HOME/Downloads/milestone-34-worker-reliability.patch"
  "$HOME/Downloads/milestone-35-reliable-worker-execution.patch"
  "$HOME/Downloads/milestone-36-domain-event-bus.patch"
  "$HOME/Downloads/milestone-37-event-emitting-workflows.patch"
  "$HOME/Downloads/milestone-38-event-driven-job-runtime.patch"
  "$HOME/Downloads/milestone-39-investigation-workspace-backend.patch"
)

echo "Starting patch application..."
echo

for p in "${PATCHES[@]}"; do
    echo "============================================================"
    echo "Checking: $(basename "$p")"

    if [[ ! -f "$p" ]]; then
        echo "ERROR: Patch file not found:"
        echo "  $p"
        exit 1
    fi

    if git apply --check "$p" >/dev/null 2>&1; then
        echo "✓ Applying..."
        git apply "$p"
        echo "✓ Applied successfully."

    elif git apply --reverse --check "$p" >/dev/null 2>&1; then
        echo "✓ Already applied."

    else
        echo "✗ Conflict or partial state detected."
        echo "Patch:"
        echo "  $p"
        echo
        echo "Run the following to see the exact conflicts:"
        echo "git apply --check \"$p\""
        exit 1
    fi

    echo
done

echo "============================================================"
echo "All patches processed successfully."