#!/usr/bin/env python3
"""logcat から拡張機能・omnibox 関連の行だけを抜き出す。"""
from bex_env import adb

KEYWORDS = [
    'mobile-bex', 'Omnibox', 'omnibox', 'onInputEntered',
    'ProcessExtensionKeyword', 'AutocompleteMediator',
    'cr_Autocomplete', 'TemplateURL', 'extension_omnibox',
]

result = adb('logcat', '-d', timeout=30)
log = result.stdout.decode('utf-8', errors='replace')

matched = [line for line in log.splitlines() if any(k in line for k in KEYWORDS)]
print(f"Total log lines: {len(log.splitlines())}")
print(f"Matched lines: {len(matched)}")
print("---")
for line in matched[-50:]:
    print(line)
