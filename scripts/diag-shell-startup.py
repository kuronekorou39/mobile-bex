#!/usr/bin/env python3
"""Diagnose why bash -lc does not pick up depot_tools PATH from .bashrc."""
import os
import subprocess

HOME = os.path.expanduser('~')
for fname in ['.bash_profile', '.bash_login', '.profile', '.bashrc']:
    path = os.path.join(HOME, fname)
    exists = os.path.exists(path)
    print(f"{'EXISTS' if exists else 'absent':>8} {path}")
    if exists and fname != '.bashrc':
        with open(path) as f:
            content = f.read()
        print(f"  --- content ({len(content)} bytes) ---")
        for i, line in enumerate(content.split('\n'), 1):
            print(f"  {i:3d}: {line}")
        print(f"  --- end ---")

print()
print("=== Login shell PATH ===")
result = subprocess.run(
    ['bash', '-lc', 'echo "PATH=$PATH"'],
    capture_output=True, text=True
)
print(result.stdout.strip())
if result.stderr.strip():
    print("STDERR:", result.stderr.strip())

print()
print("=== Interactive shell PATH ===")
result = subprocess.run(
    ['bash', '-ic', 'echo "PATH=$PATH"'],
    capture_output=True, text=True
)
print(result.stdout.strip())
if result.stderr.strip():
    print("STDERR:", result.stderr.strip())

print()
print("=== Login shell: which autoninja ===")
result = subprocess.run(
    ['bash', '-lc', 'which autoninja || echo NOT_FOUND'],
    capture_output=True, text=True
)
print(result.stdout.strip())

print()
print("=== Interactive shell: which autoninja ===")
result = subprocess.run(
    ['bash', '-ic', 'which autoninja || echo NOT_FOUND'],
    capture_output=True, text=True
)
print(result.stdout.strip())
