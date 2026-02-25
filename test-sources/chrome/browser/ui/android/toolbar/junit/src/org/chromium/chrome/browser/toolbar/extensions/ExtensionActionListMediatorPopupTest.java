// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package org.chromium.chrome.browser.toolbar.extensions;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.spy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import android.content.Context;
import android.view.View;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockedConstruction;
import org.mockito.MockedStatic;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.robolectric.RuntimeEnvironment;

import org.chromium.base.test.BaseRobolectricTestRunner;
import org.chromium.chrome.browser.profiles.Profile;
import org.chromium.chrome.browser.tab.Tab;
import org.chromium.chrome.browser.ui.extensions.ExtensionActionPopupContents;
import org.chromium.chrome.browser.ui.extensions.ExtensionBottomSheetCoordinator;
import org.chromium.chrome.browser.ui.extensions.ExtensionsToolbarBridge;
import org.chromium.components.browser_ui.widget.NullableObservableSupplier;
import org.chromium.ui.base.WindowAndroid;
import org.chromium.ui.modelutil.MVCListAdapter.ModelList;

import java.lang.reflect.Method;

/**
 * Tests for the popup-related changes in {@link ExtensionActionListMediator}: triggerPopup,
 * closeCurrentSheet, and destroy cleanup.
 */
@RunWith(BaseRobolectricTestRunner.class)
public class ExtensionActionListMediatorPopupTest {
    @Mock private WindowAndroid mWindowAndroid;
    @Mock private Profile mProfile;
    @Mock private NullableObservableSupplier<Tab> mTabSupplier;
    @Mock private ExtensionActionListCoordinator.ActionAnchorViewProvider mAnchorViewProvider;
    @Mock private ExtensionsToolbarBridge mExtensionsToolbarBridge;
    @Mock private View mFallbackAnchorView;
    @Mock private ExtensionActionPopupContents mContents;

    private MockedStatic<ExtensionActionPopupContents> mContentsStaticMock;
    private MockedConstruction<ExtensionBottomSheetCoordinator> mCoordinatorConstruction;
    private ExtensionBottomSheetCoordinator mMockCoordinator;

    private ExtensionActionListMediator mMediator;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);

        Context context = RuntimeEnvironment.application;
        ModelList models = new ModelList();

        // Mock static ExtensionActionPopupContents.create().
        mContentsStaticMock = Mockito.mockStatic(ExtensionActionPopupContents.class);
        mContentsStaticMock
                .when(() -> ExtensionActionPopupContents.create(any(Long.class)))
                .thenReturn(mContents);

        // Mock construction of ExtensionBottomSheetCoordinator.
        mCoordinatorConstruction =
                Mockito.mockConstruction(
                        ExtensionBottomSheetCoordinator.class,
                        (mock, ctx) -> {
                            mMockCoordinator = mock;
                            when(mock.showPopup(any(), any())).thenReturn(true);
                        });

        mMediator =
                new ExtensionActionListMediator(
                        context,
                        mWindowAndroid,
                        models,
                        null, // ChromeAndroidTask
                        mProfile,
                        mTabSupplier,
                        mAnchorViewProvider,
                        mExtensionsToolbarBridge,
                        mFallbackAnchorView);
    }

    @After
    public void tearDown() {
        mContentsStaticMock.close();
        mCoordinatorConstruction.close();
    }

    @Test
    public void testTriggerPopup_success_showsBottomSheet() throws Exception {
        invokeTriggerPopup("test-action-id", 12345L);

        verify(mMockCoordinator).showPopup(mWindowAndroid, mContents);
        verify(mContents, never()).destroy();
    }

    @Test
    public void testTriggerPopup_showPopupFails_destroysContents() throws Exception {
        // Override to fail.
        mCoordinatorConstruction.close();
        mCoordinatorConstruction =
                Mockito.mockConstruction(
                        ExtensionBottomSheetCoordinator.class,
                        (mock, ctx) -> {
                            mMockCoordinator = mock;
                            when(mock.showPopup(any(), any())).thenReturn(false);
                        });

        invokeTriggerPopup("test-action-id", 12345L);

        verify(mContents).destroy();
    }

    @Test
    public void testCloseCurrentSheet_hidesCoordinator() throws Exception {
        // First trigger a popup so mCurrentSheetCoordinator is set.
        invokeTriggerPopup("test-action-id", 12345L);

        invokeCloseCurrentSheet();

        verify(mMockCoordinator).hide();
    }

    @Test
    public void testDestroy_closesCurrentSheet() throws Exception {
        // Trigger a popup first.
        invokeTriggerPopup("test-action-id", 12345L);

        mMediator.destroy();

        verify(mMockCoordinator).hide();
    }

    /**
     * Invokes the private triggerPopup method via reflection. This is necessary because
     * triggerPopup is called internally by the toolbar delegate callback.
     */
    private void invokeTriggerPopup(String actionId, long nativeHostPtr) throws Exception {
        Method method =
                ExtensionActionListMediator.class.getDeclaredMethod(
                        "triggerPopup", String.class, long.class);
        method.setAccessible(true);
        method.invoke(mMediator, actionId, nativeHostPtr);
    }

    private void invokeCloseCurrentSheet() throws Exception {
        Method method =
                ExtensionActionListMediator.class.getDeclaredMethod("closeCurrentSheet");
        method.setAccessible(true);
        method.invoke(mMediator);
    }
}
