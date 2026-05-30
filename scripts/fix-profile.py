#!/usr/bin/env python3
"""Add depot_tools PATH to ~/.profile so that bash -lc (non-interactive login)
can resolve autoninja. Ubuntu's default .bashrc returns early when the shell
is non-interactive, so .bashrc-based exports do not apply to wsl -lc invocations."""
import os
import shutil
import subprocess
from datetime import datetime

profile = os.path.expanduser('~/.profile')
backup = f"{profile}.bak.{datetime.now().strftime('%Y%m%d-%H%M%S')}"
shutil.copy(profile, backup)
print(f"Backup created: {backup}")

with open(profile, 'r') as f:
    content = f.read()

if 'depot_tools' in content:
    print(".profile already contains 'depot_tools' string; skipping append.")
else:
    with open(profile, 'a') as f:
        if not content.endswith('\n'):
            f.write('\n')
        f.write('\n# depot_tools for Chromium build\n')
        f.write('export PATH="$HOME/depot_tools:$PATH"\n')
    print(f"Appended depot_tools export to {profile}")

print()
print("=== Last 6 lines of .profile ===")
with open(profile, 'r') as f:
    for line in f.readlines()[-6:]:
        print(line.rstrip() if line.rstrip() else '(blank)')

print()
print("=== Verifying autoninja in a fresh login non-interactive shell ===")
result = subprocess.run(
    ['bash', '-lc', 'which autoninja && autoninja --help 2>&1 | head -3'],
    capture_output=True, text=True
)
print(f"stdout:\n{result.stdout.strip()}")
if result.stderr.strip():
    print(f"stderr:\n{result.stderr.strip()}")
print(f"return code: {result.returncode}")
if result.returncode == 0 and 'depot_tools/autoninja' in result.stdout:
    print()
    print("SUCCESS: autoninja is now resolved by login non-interactive shells.")
else:
    print()
    print("FAILED. See errors above.")
