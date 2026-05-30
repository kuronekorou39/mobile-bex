import sys, os

path = os.path.expanduser("~/chromium/src/chrome/browser/ui/extensions/extension_action_view_model.cc")
content = open(path).read()

# Fix 1: IsEnabled() - add SidePanelInfo check for Android
old1 = '#endif  // BUILDFLAG(ENABLE_EXTENSIONS)}\n  return false;\n}'
new1 = (
    '#else   // BUILDFLAG(ENABLE_EXTENSIONS)\n'
    '  // On desktop-android, SidePanelService is not available.\n'
    '  // Use manifest data to check if the extension has a side panel.\n'
    '  if (extensions::SidePanelInfo::HasSidePanel(extension_.get())) {\n'
    '    return true;\n'
    '  }\n'
    '#endif  // BUILDFLAG(ENABLE_EXTENSIONS)\n'
    '  return false;\n'
    '}'
)
if old1 in content:
    content = content.replace(old1, new1)
    print("Fix 1: IsEnabled() patched")
else:
    print("Fix 1: NOT FOUND")

# Fix 2: has_side_panel_action grayscale
old2 = '  bool has_side_panel_action = false;\n#endif  // BUILDFLAG(ENABLE_EXTENSIONS)'
new2 = (
    '  bool has_side_panel_action =\n'
    '      extensions::SidePanelInfo::HasSidePanel(extension_.get());\n'
    '#endif  // BUILDFLAG(ENABLE_EXTENSIONS)'
)
if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2: has_side_panel_action patched")
else:
    print("Fix 2: NOT FOUND")

# Fix 3: Add include
inc_str = 'chrome/common/extensions/api/side_panel/side_panel_info.h'
if inc_str not in content:
    content = content.replace(
        '#include "chrome/browser/extensions/api/side_panel/side_panel_service.h"',
        '#include "chrome/browser/extensions/api/side_panel/side_panel_service.h"\n#include "' + inc_str + '"'
    )
    print("Fix 3: include added")
else:
    print("Fix 3: already present")

with open(path, "w") as f:
    f.write(content)
print("All done")
