#!/usr/bin/env python3
"""Apply patch 14: Omnibox onInputEntered fix for Android."""
import sys

CHROMIUM_SRC = "/home/kuronekorou39/chromium/src"

# --- File 1: autocomplete_controller_android.h --- ALREADY APPLIED
print("SKIP: autocomplete_controller_android.h (already applied)")

# --- File 2: autocomplete_controller_android.cc ---
filepath2 = f"{CHROMIUM_SRC}/chrome/browser/android/omnibox/autocomplete_controller_android.cc"
with open(filepath2, "r") as f:
    content2 = f.read()

# 2a. Add includes
assert '#include "chrome/browser/autocomplete/shortcuts_backend_factory.h"' in content2
content2 = content2.replace(
    '#include "chrome/browser/autocomplete/shortcuts_backend_factory.h"',
    '#include "chrome/browser/autocomplete/shortcuts_backend_factory.h"\n'
    '#include "base/strings/utf_string_conversions.h"\n'
    '#include "chrome/browser/extensions/api/omnibox/omnibox_api.h"'
)

# 2b. Add method implementation before Shutdown()
old2 = "void AutocompleteControllerAndroid::Shutdown() {"

new2 = """bool AutocompleteControllerAndroid::ProcessExtensionKeywordMatch(
    JNIEnv* env,
    uintptr_t match_ptr,
    const JavaRef<jobject>& j_web_contents) {
  const auto& match = *reinterpret_cast<AutocompleteMatch*>(match_ptr);

  TemplateURLService* template_url_service =
      TemplateURLServiceFactory::GetForProfile(profile_);
  if (!template_url_service) {
    return false;
  }

  TemplateURL* template_url = match.GetTemplateURL(template_url_service);
  if (!template_url ||
      template_url->type() != TemplateURL::OMNIBOX_API_EXTENSION) {
    return false;
  }

  content::WebContents* web_contents =
      content::WebContents::FromJavaWebContents(j_web_contents);
  if (!web_contents) {
    return false;
  }

  // Strip the keyword + leading space off the input, matching
  // ChromeOmniboxClient::ProcessExtensionMatch on desktop.
  std::u16string remaining_input;
  AutocompleteInput::SplitKeywordFromInput(
      match.fill_into_edit, true, &remaining_input);

  extensions::ExtensionOmniboxEventRouter::OnInputEntered(
      web_contents,
      template_url->GetExtensionId(),
      base::UTF16ToUTF8(remaining_input),
      WindowOpenDisposition::CURRENT_TAB);

  return true;
}

void AutocompleteControllerAndroid::Shutdown() {"""

assert old2 in content2, "Shutdown pattern not found in .cc"
content2 = content2.replace(old2, new2)
with open(filepath2, "w") as f:
    f.write(content2)
print("OK: autocomplete_controller_android.cc")

# --- File 3: AutocompleteController.java ---
filepath3 = f"{CHROMIUM_SRC}/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/suggestions/AutocompleteController.java"
with open(filepath3, "r") as f:
    content3 = f.read()

# 3a. Add wrapper method
old3 = """    /**
     * Pass the UI specific measurement information to Native code to aid Adaptive Suggestions."""

new3 = """    /**
     * Checks if the match is an extension keyword match and dispatches onInputEntered.
     *
     * @param match The AutocompleteMatch to check.
     * @param webContents The WebContents for the current tab.
     * @return true if the match was handled by an extension (caller should skip URL loading).
     */
    boolean processExtensionKeywordMatch(
            AutocompleteMatch match, @Nullable WebContents webContents) {
        if (mNativeController == 0) return false;
        if (match.getNativeObjectRef() == 0L) return false;
        if (webContents == null) return false;
        return AutocompleteControllerJni.get()
                .processExtensionKeywordMatch(
                        mNativeController, match.getNativeObjectRef(), webContents);
    }

    /**
     * Pass the UI specific measurement information to Native code to aid Adaptive Suggestions."""

assert old3 in content3, "Java wrapper pattern not found"
content3 = content3.replace(old3, new3)

# 3b. Add native method
old3b = """        /** Acquire an instance of AutocompleteController associated with the supplied profile. */
        AutocompleteController getForProfile(@JniType("Profile*") Profile profile);
    }
}"""

new3b = """        /** Acquire an instance of AutocompleteController associated with the supplied profile. */
        AutocompleteController getForProfile(@JniType("Profile*") Profile profile);

        boolean processExtensionKeywordMatch(
                long nativeAutocompleteControllerAndroid,
                long nativeAutocompleteMatch,
                @Nullable WebContents webContents);
    }
}"""

assert old3b in content3, "Natives interface pattern not found"
content3 = content3.replace(old3b, new3b)
with open(filepath3, "w") as f:
    f.write(content3)
print("OK: AutocompleteController.java")

# --- File 4: AutocompleteMediator.java ---
filepath4 = f"{CHROMIUM_SRC}/chrome/browser/ui/android/omnibox/java/src/org/chromium/chrome/browser/omnibox/suggestions/AutocompleteMediator.java"
with open(filepath4, "r") as f:
    content4 = f.read()

old4 = """            OmniboxMetrics.recordFocusToOpenTime(
                    System.currentTimeMillis()
                            - assumeNonNull(mAutocompleteInput).getUrlFocusTime());

            // Clear the deferred site load action in case it executes. Reclaims a bit of memory.
            mDeferredLoadAction = null;"""

new4 = """            OmniboxMetrics.recordFocusToOpenTime(
                    System.currentTimeMillis()
                            - assumeNonNull(mAutocompleteInput).getUrlFocusTime());

            // Check if this is an extension keyword match. If so, dispatch
            // onInputEntered to the extension instead of navigating.
            if (mAutocomplete != null) {
                var tab = mDataProvider.getTab();
                WebContents webContents = tab != null ? tab.getWebContents() : null;
                if (mAutocomplete.processExtensionKeywordMatch(suggestion, webContents)) {
                    mDeferredLoadAction = null;
                    mOmniboxFocusResultedInNavigation = true;
                    recordMetrics(
                            suggestion, null, matchIndex, WindowOpenDisposition.CURRENT_TAB);
                    return;
                }
            }

            // Clear the deferred site load action in case it executes. Reclaims a bit of memory.
            mDeferredLoadAction = null;"""

assert old4 in content4, "Mediator pattern not found"
content4 = content4.replace(old4, new4)
with open(filepath4, "w") as f:
    f.write(content4)
print("OK: AutocompleteMediator.java")

print("\nAll patch 14 files applied successfully!")
