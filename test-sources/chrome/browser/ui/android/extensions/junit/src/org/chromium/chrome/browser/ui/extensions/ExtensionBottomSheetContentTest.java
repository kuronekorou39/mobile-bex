// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.ui.extensions;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import android.view.View;
import android.widget.FrameLayout;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.robolectric.RuntimeEnvironment;

import org.chromium.base.test.BaseRobolectricTestRunner;
import org.chromium.chrome.browser.ui.extensions.R;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetContent;
import org.chromium.components.thinwebview.ThinWebView;

/** Tests for {@link ExtensionBottomSheetContent}. */
@RunWith(BaseRobolectricTestRunner.class)
public class ExtensionBottomSheetContentTest {
    @Mock private ThinWebView mThinWebView;
    @Mock private View mMockView;

    private boolean mCallbackCalled;
    private ExtensionBottomSheetContent mContent;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        when(mThinWebView.getView()).thenReturn(mMockView);
        mCallbackCalled = false;
        mContent =
                new ExtensionBottomSheetContent(
                        RuntimeEnvironment.application,
                        mThinWebView,
                        () -> mCallbackCalled = true);
    }

    @Test
    public void testGetContentView_returnsFrameLayout() {
        View contentView = mContent.getContentView();
        assertNotNull(contentView);
        assertTrue(contentView instanceof FrameLayout);
    }

    @Test
    public void testGetContentView_containsThinWebView() {
        FrameLayout contentView = (FrameLayout) mContent.getContentView();
        assertEquals(1, contentView.getChildCount());
        assertEquals(mMockView, contentView.getChildAt(0));
    }

    @Test
    public void testGetToolbarView_returnsNull() {
        assertNull(mContent.getToolbarView());
    }

    @Test
    public void testGetVerticalScrollOffset_returnsZero() {
        assertEquals(0, mContent.getVerticalScrollOffset());
    }

    @Test
    public void testGetFullHeightRatio() {
        assertEquals(0.7f, mContent.getFullHeightRatio(), 0.001f);
    }

    @Test
    public void testGetHalfHeightRatio() {
        assertEquals(0.5f, mContent.getHalfHeightRatio(), 0.001f);
    }

    @Test
    public void testGetPriority_returnsHigh() {
        assertEquals(BottomSheetContent.ContentPriority.HIGH, mContent.getPriority());
    }

    @Test
    public void testSwipeToDismissEnabled_returnsTrue() {
        assertTrue(mContent.swipeToDismissEnabled());
    }

    @Test
    public void testHasCustomLifecycle_returnsTrue() {
        assertTrue(mContent.hasCustomLifecycle());
    }

    @Test
    public void testHandleBackPress_invokesCallback() {
        assertTrue(mContent.handleBackPress());
        assertTrue(mCallbackCalled);
    }

    @Test
    public void testDestroy_destroysThinWebView() {
        mContent.destroy();
        verify(mThinWebView).destroy();
    }

    @Test
    public void testGetSheetContentDescription() {
        assertEquals(
                "Extension popup",
                mContent.getSheetContentDescription(RuntimeEnvironment.application));
    }

    @Test
    public void testAccessibilityStringIds_returnValidResources() {
        assertEquals(
                R.string.extension_popup_sheet_opened_half,
                mContent.getSheetHalfHeightAccessibilityStringId());
        assertEquals(
                R.string.extension_popup_sheet_opened_full,
                mContent.getSheetFullHeightAccessibilityStringId());
        assertEquals(
                R.string.extension_popup_sheet_closed,
                mContent.getSheetClosedAccessibilityStringId());
    }
}
