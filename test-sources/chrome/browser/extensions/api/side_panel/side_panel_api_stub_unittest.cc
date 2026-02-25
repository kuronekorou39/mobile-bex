// Copyright 2025 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/extensions/api/side_panel/side_panel_api.h"

#include "base/values.h"
#include "chrome/common/extensions/api/side_panel.h"
#include "extensions/browser/api_test_utils.h"
#include "extensions/browser/extension_function_dispatcher.h"
#include "extensions/browser/extension_function.h"
#include "chrome/test/base/testing_browser_process.h"
#include "chrome/test/base/testing_profile.h"
#include "chrome/test/base/testing_profile_manager.h"
#include "content/public/test/browser_task_environment.h"
#include "testing/gtest/include/gtest/gtest.h"

namespace extensions {
namespace {

class SidePanelApiStubTest : public testing::Test {
 protected:
  void SetUp() override {
    profile_manager_ = std::make_unique<TestingProfileManager>(
        TestingBrowserProcess::GetGlobal());
    ASSERT_TRUE(profile_manager_->SetUp());
    profile_ = profile_manager_->CreateTestingProfile("test");
  }

  void TearDown() override {
    profile_ = nullptr;
    profile_manager_->DeleteAllTestingProfiles();
  }

  // Runs an extension function and returns the result value.
  // For functions that return NoArguments(), result will be nullptr.
  std::optional<base::Value> RunFunction(
      scoped_refptr<ExtensionFunction> function,
      const std::string& args = "[]") {
    function->set_has_callback(true);
    return api_test_utils::RunFunctionAndReturnSingleResult(
        function.get(), args, profile_);
  }

  content::BrowserTaskEnvironment task_environment_;
  std::unique_ptr<TestingProfileManager> profile_manager_;
  raw_ptr<TestingProfile> profile_;
};

TEST_F(SidePanelApiStubTest, SetOptions_ReturnsNoArguments) {
  auto function = base::MakeRefCounted<SidePanelSetOptionsFunction>();
  auto result = RunFunction(function, R"([{"path": "panel.html"}])");
  // NoArguments() returns no result value.
  EXPECT_FALSE(result.has_value());
}

TEST_F(SidePanelApiStubTest, GetOptions_ReturnsEnabledTrue) {
  auto function = base::MakeRefCounted<SidePanelGetOptionsFunction>();
  auto result = RunFunction(function, "[]");
  ASSERT_TRUE(result.has_value());
  ASSERT_TRUE(result->is_dict());

  const base::Value::Dict& dict = result->GetDict();
  std::optional<bool> enabled = dict.FindBool("enabled");
  ASSERT_TRUE(enabled.has_value());
  EXPECT_TRUE(enabled.value());
}

TEST_F(SidePanelApiStubTest, SetPanelBehavior_ReturnsNoArguments) {
  auto function = base::MakeRefCounted<SidePanelSetPanelBehaviorFunction>();
  auto result =
      RunFunction(function, R"([{"openPanelOnActionClick": true}])");
  EXPECT_FALSE(result.has_value());
}

TEST_F(SidePanelApiStubTest, GetPanelBehavior_ReturnsOpenPanelOnActionClickFalse) {
  auto function = base::MakeRefCounted<SidePanelGetPanelBehaviorFunction>();
  auto result = RunFunction(function, "[]");
  ASSERT_TRUE(result.has_value());
  ASSERT_TRUE(result->is_dict());

  const base::Value::Dict& dict = result->GetDict();
  std::optional<bool> open_on_click = dict.FindBool("openPanelOnActionClick");
  ASSERT_TRUE(open_on_click.has_value());
  EXPECT_FALSE(open_on_click.value());
}

TEST_F(SidePanelApiStubTest, Open_ReturnsNoArguments) {
  auto function = base::MakeRefCounted<SidePanelOpenFunction>();
  auto result = RunFunction(function, "[]");
  EXPECT_FALSE(result.has_value());
}

TEST_F(SidePanelApiStubTest, GetLayout_ReturnsDefault) {
  auto function = base::MakeRefCounted<SidePanelGetLayoutFunction>();
  auto result = RunFunction(function, "[]");
  ASSERT_TRUE(result.has_value());
  ASSERT_TRUE(result->is_dict());
  // Default PanelLayout should be a valid dict (may be empty or with defaults).
}

TEST_F(SidePanelApiStubTest, Close_ReturnsNoArguments) {
  auto function = base::MakeRefCounted<SidePanelCloseFunction>();
  auto result = RunFunction(function, "[]");
  EXPECT_FALSE(result.has_value());
}

}  // namespace
}  // namespace extensions
