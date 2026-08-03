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
import android.content.Context;
import android.os.Looper;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.robolectric.Robolectric;
import org.robolectric.Shadows;

import org.chromium.base.test.BaseRobolectricTestRunner;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetContent;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetController;
import org.chromium.components.browser_ui.bottomsheet.BottomSheetObserver;
import org.chromium.components.thinwebview.ThinWebView;
import org.chromium.content_public.browser.WebContents;
import org.chromium.ui.base.WindowAndroid;

import java.lang.ref.WeakReference;

/** Tests for {@link ExtensionBottomSheetCoordinator}. */
@RunWith(BaseRobolectricTestRunner.class)
public class ExtensionBottomSheetCoordinatorTest {
    @Mock private WindowAndroid mWindowAndroid;
    @Mock private BottomSheetController mBottomSheetController;
    @Mock private ExtensionActionPopupContents mContents;
    @Mock private WebContents mWebContents;
    @Mock private ThinWebView mThinWebView;

    private Activity mActivity;
    private ExtensionBottomSheetCoordinator mCoordinator;

    /**
     * Chromium の Robolectric は静的モックに対応していないため、静的な取得を行う
     * メソッドをサブクラスで差し替える。
     */
    private class TestCoordinator extends ExtensionBottomSheetCoordinator {
        @Override
        protected BottomSheetController getBottomSheetController(WindowAndroid windowAndroid) {
            return mBottomSheetController;
        }

        @Override
        protected ThinWebView createThinWebView(Context context, WindowAndroid windowAndroid) {
            return mThinWebView;
        }
    }

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);

        // Activity はモックだと getResources() が null になり、View の生成や
        // DisplayMetrics の参照で落ちるため、Robolectric の実インスタンスを使う。
        mActivity = Robolectric.buildActivity(Activity.class).setup().get();

        mCoordinator = new TestCoordinator();

        // Mock WindowAndroid.getActivity() -> Activity.
        WeakReference<Activity> activityRef = new WeakReference<>(mActivity);
        doReturn(activityRef).when(mWindowAndroid).getActivity();

        // Mock contents.
        when(mContents.getWebContents()).thenReturn(mWebContents);

        // Mock ThinWebView.getView() for FrameLayout.addView.
        when(mThinWebView.getView())
                .thenReturn(new android.view.View(mActivity));

        // Default: requestShowContent succeeds.
        when(mBottomSheetController.requestShowContent(any(), eq(true))).thenReturn(true);
    }

    @Test
    public void testShowPopup_activityNull_returnsFalse() {
        WeakReference<Activity> nullRef = new WeakReference<>(null);
        doReturn(nullRef).when(mWindowAndroid).getActivity();

        assertFalse(mCoordinator.showPopup(mWindowAndroid, mContents));
    }

    @Test
    public void testShowPopup_bottomSheetControllerNull_returnsFalse() {
        ExtensionBottomSheetCoordinator coordinator =
                new ExtensionBottomSheetCoordinator() {
                    @Override
                    protected BottomSheetController getBottomSheetController(
                            WindowAndroid windowAndroid) {
                        return null;
                    }
                };

        assertFalse(coordinator.showPopup(mWindowAndroid, mContents));
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

        // 初期ページの読み込みは View.post() 経由。View.post() はビューが
        // ウィンドウに接続されるまで実行されないため、シートの表示を模して
        // コンテンツビューを接続してから Looper を回す。
        ArgumentCaptor<BottomSheetContent> captor =
                ArgumentCaptor.forClass(BottomSheetContent.class);
        verify(mBottomSheetController).requestShowContent(captor.capture(), eq(true));
        mActivity.setContentView(captor.getValue().getContentView());
        Shadows.shadowOf(Looper.getMainLooper()).idle();

        verify(mContents).loadInitialPage();
    }

    @Test
    public void testShowPopup_requestShowContentFails_returnsFalseAndCleanup() {
        when(mBottomSheetController.requestShowContent(any(), eq(true))).thenReturn(false);

        assertFalse(mCoordinator.showPopup(mWindowAndroid, mContents));
        Shadows.shadowOf(Looper.getMainLooper()).idle();
        verify(mContents).destroy();
        verify(mContents, never()).loadInitialPage();
    }

    @Test
    public void testHide_hidesContentAndCleansUp() {
        mCoordinator.showPopup(mWindowAndroid, mContents);
        mCoordinator.hide();

        verify(mBottomSheetController).hideContent(any(), eq(false));
        verify(mContents).destroy();
    }

    @Test
    public void testHide_withoutShow_doesNotCrash() {
        // Should not throw.
        mCoordinator.hide();
    }

    @Test
    public void testHide_twice_destroysContentsOnce() {
        mCoordinator.showPopup(mWindowAndroid, mContents);
        mCoordinator.hide();
        mCoordinator.hide();

        verify(mContents).destroy();
    }

    /**
     * スワイプで閉じた場合など hide() を経由しない閉じ方でも WebContents が破棄される
     * ことを確認する。検知していないと、見えないままポップアップの JS が動き続ける。
     */
    @Test
    public void testSheetContentReplaced_cleansUp() {
        mCoordinator.showPopup(mWindowAndroid, mContents);

        ArgumentCaptor<BottomSheetObserver> captor =
                ArgumentCaptor.forClass(BottomSheetObserver.class);
        verify(mBottomSheetController).addObserver(captor.capture());

        // 別のコンテンツに差し替わった = 自分のシートは閉じられた。
        captor.getValue().onSheetContentChanged(mock(BottomSheetContent.class));

        verify(mContents).destroy();
    }

    @Test
    public void testSheetContentUnchanged_doesNotCleanUp() {
        mCoordinator.showPopup(mWindowAndroid, mContents);

        ArgumentCaptor<BottomSheetContent> contentCaptor =
                ArgumentCaptor.forClass(BottomSheetContent.class);
        verify(mBottomSheetController).requestShowContent(contentCaptor.capture(), eq(true));

        ArgumentCaptor<BottomSheetObserver> observerCaptor =
                ArgumentCaptor.forClass(BottomSheetObserver.class);
        verify(mBottomSheetController).addObserver(observerCaptor.capture());

        // 自分のコンテンツが通知された場合は閉じられていないので破棄しない。
        observerCaptor.getValue().onSheetContentChanged(contentCaptor.getValue());

        verify(mContents, never()).destroy();
    }
}
