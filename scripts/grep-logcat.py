import subprocess
result = subprocess.run(
    [r'C:\Android\platform-tools\adb.exe', '-s', '54231JEBF06373', 'logcat', '-d'],
    capture_output=True, timeout=30
)
log = result.stdout.decode('utf-8', errors='replace')
keywords = ['mobile-bex', 'Omnibox', 'omnibox', 'onInputEntered',
            'ProcessExtensionKeyword', 'AutocompleteMediator',
            'cr_Autocomplete', 'TemplateURL', 'extension_omnibox']
print(f"Total log lines: {len(log.splitlines())}")
matched = []
for line in log.splitlines():
    if any(k in line for k in keywords):
        matched.append(line)
print(f"Matched lines: {len(matched)}")
print("---")
for line in matched[-50:]:
    print(line)
