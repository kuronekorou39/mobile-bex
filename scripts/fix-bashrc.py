#!/usr/bin/env python3
"""Clean up ~/.bashrc:
- Remove the corrupted Git Bash PATH paste line (contains '\\/c/Users/').
- Remove the heredoc-expanded depot_tools PATH line I appended earlier
  (a single huge static PATH starting with '/home/<user>/depot_tools:').
- Remove the stale '# depot_tools for Chromium build' comment.
Then append a proper, dynamic depot_tools PATH line at the end of the file.
A timestamped backup of the original .bashrc is created before editing.
"""
import os
import shutil
import subprocess
from datetime import datetime

bashrc = os.path.expanduser('~/.bashrc')
HOME = os.path.expanduser('~')

backup = f"{bashrc}.bak.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
shutil.copy(bashrc, backup)
print(f"Backup created: {backup}")

with open(bashrc, 'r') as f:
    original = f.read()

lines = original.split('\n')
cleaned = []
prev_removed = False
removed_log = []

for line in lines:
    reason = None
    if '\\/c/Users/' in line:
        reason = "corrupted Git Bash PATH paste"
    elif line.startswith(f'export PATH="{HOME}/depot_tools:'):
        reason = "heredoc-expanded depot_tools PATH"
    elif line.strip() == '# depot_tools for Chromium build':
        reason = "stale depot_tools comment"

    if reason is not None:
        removed_log.append((reason, line[:90]))
        prev_removed = True
        continue

    if prev_removed and line.strip() == '':
        prev_removed = False
        continue
    prev_removed = False
    cleaned.append(line)

while cleaned and cleaned[-1].strip() == '':
    cleaned.pop()

cleaned.append('')
cleaned.append('# depot_tools for Chromium build')
cleaned.append('export PATH="$HOME/depot_tools:$PATH"')
cleaned.append('')

new_content = '\n'.join(cleaned)
with open(bashrc, 'w') as f:
    f.write(new_content)

print(f"\nRemoved {len(removed_log)} broken line(s):")
for reason, snippet in removed_log:
    print(f"  [{reason}]")
    print(f"    {snippet}{'...' if len(snippet) >= 90 else ''}")
print()
print("=== Last 8 lines of new .bashrc ===")
for line in cleaned[-8:]:
    print(line if line else '(blank)')

print()
print("=== Verifying autoninja resolution in a fresh login shell ===")
result = subprocess.run(
    ['bash', '-lc', 'which autoninja && autoninja --help 2>&1 | head -1'],
    capture_output=True, text=True
)
print(f"stdout: {result.stdout.strip()}")
if result.stderr.strip():
    print(f"stderr: {result.stderr.strip()}")
print(f"return code: {result.returncode}")
if result.returncode == 0 and 'depot_tools/autoninja' in result.stdout:
    print("\nautoninja is now resolved in new login shells.")
else:
    print("\nWARNING: autoninja still not resolved. See errors above.")
