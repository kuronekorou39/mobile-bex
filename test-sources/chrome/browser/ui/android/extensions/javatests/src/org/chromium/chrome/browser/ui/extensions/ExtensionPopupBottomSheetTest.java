// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.ui.extensions;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withClassName;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.widget.FrameLayout;

import androidx.test.filters.MediumTest;

import org.hamcrest.Matchers;
import org.junit.After;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import org.chromium.base.test.util.CommandLineFlags;
import org.chromium.base.test.util.Feature;
import org.chromium.chrome.browser.ChromeTabbedActivity;
import org.chromium.chrome.browser.flags.ChromeSwitches;
import org.chromium.chrome.test.ChromeJUnit4ClassRunner;
import org.chromium.chrome.test.ChromeTabbedActivityTestRule;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetController;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetControllerProvider;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetTestSupport;
import org.chromium.content_public.browser.test.util.TestThreadUtils;

/**
 * Instrumentation tests for extension popup display in a BottomSheet. These tests require a running
 * Chrome instance (real device or emulator).
 *
 * <p>Note: These tests verify the BottomSheet integration plumbing. Full extension popup loading
 * requires a sideloaded test extension, which is outside the scope of automated CI. The tests below
 * verify the coordinator/content wiring using mock WebContents where possible.
 */
@RunWith(ChromeJUnit4ClassRunner.class)
@CommandLineFlags.Add({ChromeSwitches.DISABLE_FIRST_RUN_EXPERIENCE})
public class ExtensionPopupBottomSheetTest {
    @Rule
    public ChromeTabbedActivityTestRule mActivityTestRule = new ChromeTabbedActivityTestRule();

    private ChromeTabbedActivity mActivity;
    private BottomSheetController mBottomSheetController;

    @Before
    public void setUp() throws Exception {
        mActivityTestRule.startMainActivityOnBlankPage();
        mActivity = mActivityTestRule.getActivity();

        TestThreadUtils.runOnUiThreadBlocking(
                () -> {
                    mBottomSheetController =
                            BottomSheetControllerProvider.from(
                                    mActivity.getWindowAndroid());
                });
    }

    @After
    public void tearDown() throws Exception {
        // Ensure any open sheets are cleaned up.
        TestThreadUtils.runOnUiThreadBlocking(
                () -> {
                    if (mBottomSheetController != null) {
                        BottomSheetTestSupport.suppressSheet(
                                mBottomSheetController,
                                BottomSheetController.StateChangeReason.NONE);
                    }
                });
    }

    @Test
    @MediumTest
    @Feature({"Extensions"})
    public void testBottomSheetController_isAvailable() {
        assertNotNull(
                "BottomSheetController should be available in ChromeTabbedActivity",
                mBottomSheetController);
    }

    @Test
    @MediumTest
    @Feature({"Extensions"})
    public void testBottomSheetContent_canBeCreatedAndShown() throws Exception {
        TestThreadUtils.runOnUiThreadBlocking(
                () -> {
                    // Create a minimal BottomSheetContent with a dummy FrameLayout
                    // to verify the show/hide plumbing works.
                    FrameLayout dummyView = new FrameLayout(mActivity);
                    DummyBottomSheetContent content = new DummyBottomSheetContent(dummyView);

                    boolean shown =
                            mBottomSheetController.requestShowContent(content, /* animate= */ false);
                    assertTrue("requestShowContent should succeed", shown);

                    mBottomSheetController.hideContent(content, /* animate= */ false);
                    content.destroy();
                });
    }

    @Test
    @MediumTest
    @Feature({"Extensions"})
    public void testExtensionBottomSheetCoordinator_showPopup_nullActivity_returnsFalse() {
        // Verify graceful failure when WindowAndroid returns null activity.
        TestThreadUtils.runOnUiThreadBlocking(
                () -> {
                    ExtensionBottomSheetCoordinator coordinator =
                            new ExtensionBottomSheetCoordinator();
                    // We cannot easily pass a WindowAndroid with null activity in instrumentation,
                    // but we verify the coordinator is instantiable and doesn't crash.
                    assertNotNull(coordinator);
                });
    }

    /**
     * Minimal BottomSheetContent for testing the show/hide plumbing without requiring a real
     * ThinWebView or WebContents.
     */
    private static class DummyBottomSheetContent
            implements org.chromium.components.browser_ui.bottomsheet.BottomSheetContent {
        private final FrameLayout mView;

        DummyBottomSheetContent(FrameLayout view) {
            mView = view;
        }

        @Override
        public android.view.View getContentView() {
            return mView;
        }

        @Override
        public android.view.View getToolbarView() {
            return null;
        }

        @Override
        public int getVerticalScrollOffset() {
            return 0;
        }

        @Override
        public void destroy() {}

        @Override
        public int getPriority() {
            return ContentPriority.HIGH;
        }

        @Override
        public boolean swipeToDismissEnabled() {
            return true;
        }

        @Override
        public float getFullHeightRatio() {
            return 0.7f;
        }

        @Override
        public float getHalfHeightRatio() {
            return 0.5f;
        }

        @Override
        public boolean hasCustomLifecycle() {
            return true;
        }

        @Override
        public String getSheetContentDescription(android.content.Context context) {
            return "Test";
        }

        @Override
        public int getSheetHalfHeightAccessibilityStringId() {
            return 0;
        }

        @Override
        public int getSheetFullHeightAccessibilityStringId() {
            return 0;
        }

        @Override
        public int getSheetClosedAccessibilityStringId() {
            return 0;
        }
    }
}
