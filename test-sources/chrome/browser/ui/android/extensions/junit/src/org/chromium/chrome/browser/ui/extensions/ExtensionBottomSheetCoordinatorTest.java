// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.ui.extensions;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import android.app.Activity;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;

import org.chromium.base.test.BaseRobolectricTestRunner;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetController;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetControllerProvider;
import org.chromium.components.thinwebview.ThinWebView;
import org.chromium.components.thinwebview.ThinWebViewFactory;
import org.chromium.content_public.browser.WebContents;
import org.chromium.ui.base.IntentRequestTracker;
import org.chromium.ui.base.WindowAndroid;

import java.lang.ref.WeakReference;

/** Tests for {@link ExtensionBottomSheetCoordinator}. */
@RunWith(BaseRobolectricTestRunner.class)
public class ExtensionBottomSheetCoordinatorTest {
    @Mock private WindowAndroid mWindowAndroid;
    @Mock private BottomSheetController mBottomSheetController;
    @Mock private ExtensionActionPopupContents mContents;
    @Mock private WebContents mWebContents;
    @Mock private Activity mActivity;
    @Mock private ThinWebView mThinWebView;
    @Mock private IntentRequestTracker mIntentRequestTracker;

    private MockedStatic<BottomSheetControllerProvider> mBottomSheetControllerProviderMock;
    private MockedStatic<ThinWebViewFactory> mThinWebViewFactoryMock;

    private ExtensionBottomSheetCoordinator mCoordinator;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);

        mCoordinator = new ExtensionBottomSheetCoordinator();

        // Mock WindowAndroid.getActivity() -> Activity.
        WeakReference<Activity> activityRef = new WeakReference<>(mActivity);
        doReturn(activityRef).when(mWindowAndroid).getActivity();
        when(mWindowAndroid.getIntentRequestTracker()).thenReturn(mIntentRequestTracker);

        // Mock static providers.
        mBottomSheetControllerProviderMock =
                Mockito.mockStatic(BottomSheetControllerProvider.class);
        mBottomSheetControllerProviderMock
                .when(() -> BottomSheetControllerProvider.from(mWindowAndroid))
                .thenReturn(mBottomSheetController);

        mThinWebViewFactoryMock = Mockito.mockStatic(ThinWebViewFactory.class);
        mThinWebViewFactoryMock
                .when(() -> ThinWebViewFactory.create(any(), any(), any()))
                .thenReturn(mThinWebView);

        // Mock contents.
        when(mContents.getWebContents()).thenReturn(mWebContents);

        // Mock ThinWebView.getView() for FrameLayout.addView.
        when(mThinWebView.getView()).thenReturn(new android.view.View(mActivity));

        // Default: requestShowContent succeeds.
        when(mBottomSheetController.requestShowContent(any(), eq(true))).thenReturn(true);
    }

    @After
    public void tearDown() {
        mBottomSheetControllerProviderMock.close();
        mThinWebViewFactoryMock.close();
    }

    @Test
    public void testShowPopup_activityNull_returnsFalse() {
        WeakReference<Activity> nullRef = new WeakReference<>(null);
        doReturn(nullRef).when(mWindowAndroid).getActivity();

        assertFalse(mCoordinator.showPopup(mWindowAndroid, mContents));
    }

    @Test
    public void testShowPopup_bottomSheetControllerNull_returnsFalse() {
        mBottomSheetControllerProviderMock
                .when(() -> BottomSheetControllerProvider.from(mWindowAndroid))
                .thenReturn(null);

        assertFalse(mCoordinator.showPopup(mWindowAndroid, mContents));
    }

    @Test
    public void testShowPopup_success_returnsTrue() {
        assertTrue(mCoordinator.showPopup(mWindowAndroid, mContents));
    }

    @Test
    public void testShowPopup_success_setsDelegate() {
        mCoordinator.showPopup(mWindowAndroid, mContents);
        verify(mContents).setDelegate(any(ExtensionActionPopupContents.Delegate.class));
    }

    @Test
    public void testShowPopup_success_attachesWebContents() {
        mCoordinator.showPopup(mWindowAndroid, mContents);
        verify(mThinWebView).attachWebContents(eq(mWebContents), any(), any());
    }

    @Test
    public void testShowPopup_success_loadsInitialPage() {
        mCoordinator.showPopup(mWindowAndroid, mContents);
        verify(mContents).loadInitialPage();
    }

    @Test
    public void testShowPopup_requestShowContentFails_returnsFalseAndCleanup() {
        when(mBottomSheetController.requestShowContent(any(), eq(true))).thenReturn(false);

        assertFalse(mCoordinator.showPopup(mWindowAndroid, mContents));
        verify(mContents).destroy();
        verify(mContents, never()).loadInitialPage();
    }

    @Test
    public void testHide_hidesContentAndCleansUp() {
        mCoordinator.showPopup(mWindowAndroid, mContents);
        mCoordinator.hide();

        verify(mBottomSheetController).hideContent(any(), eq(true));
        verify(mContents).destroy();
    }

    @Test
    public void testHide_withoutShow_doesNotCrash() {
        // Should not throw.
        mCoordinator.hide();
    }
}
