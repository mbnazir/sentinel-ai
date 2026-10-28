#!/usr/bin/env python3
"""Apply the narrow Sentinel AI chunk-id rollback fix to backend/app/workers/tasks.py."""
from pathlib import Path
import ast
import difflib
import hashlib
import shutil
import sys

source = Path('app/workers/tasks.py')
backup_dir = Path('backups/worker-recovery-uat')
backup = backup_dir / 'tasks-before-missinggreenlet-fix.py'
if not source.is_file():
    sys.exit('ERROR: Run from backend directory; app/workers/tasks.py not found.')
original = source.read_text(encoding='utf-8')
needle_before = '                        await db.commit()\n                        try:\n                            keys = (await db.execute('
replacement_before = '                        await db.commit()\n                        chunk_id = chunk.id\n                        try:\n                            keys = (await db.execute('
needle_after = '                            chunk = await db.get(ScanChunkModel, chunk.id)'
replacement_after = '                            chunk = await db.get(ScanChunkModel, chunk_id)'
if original.count(needle_before) != 1 or original.count(needle_after) != 1:
    sys.exit('ERROR: Expected source patterns not found exactly once; no changes made.')
updated = original.replace(needle_before, replacement_before, 1).replace(needle_after, replacement_after, 1)
try:
    ast.parse(updated, filename=str(source))
except SyntaxError as exc:
    sys.exit(f'ERROR: Updated source fails syntax check: {exc}; no changes made.')
backup_dir.mkdir(parents=True, exist_ok=True)
if backup.exists():
    sys.exit(f'ERROR: Backup already exists at {backup}; no changes made. Inspect before proceeding.')
shutil.copy2(source, backup)
source.write_text(updated, encoding='utf-8')
print('PATCH APPLIED: saved chunk ID before inner try; used saved ID after rollback.')
print('Backup:', backup)
print('Updated SHA256:', hashlib.sha256(updated.encode()).hexdigest())
print('--- Diff ---')
print(''.join(difflib.unified_diff(original.splitlines(keepends=True), updated.splitlines(keepends=True), fromfile='tasks.py (before)', tofile='tasks.py (after)')))
