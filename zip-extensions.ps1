# テスト拡張機能をデスクトップに zip 化するスクリプト
# 注: test-extension-devtools は含めない。devtools_page 持ち拡張を読み込むと
#     Chromium が起動ハングする既知問題があるため（復旧: scripts/strip-devtools-extension.py）。
#     検証する場合のみ個別に zip 化すること。
$dirs = @(
    'test-extension',
    'test-extension-contextmenu',
    'test-extension-fulltab',
    'test-extension-newtab',
    'test-extension-notifications',
    'test-extension-omnibox',
    'test-extension-options',
    'test-extension-phase2',
    'test-extension-sidepanel'
)
$root = $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$failed = 0
foreach ($d in $dirs) {
    $src = Join-Path $root "$d\*"
    $dst = Join-Path $desktop "$d.zip"
    try {
        Compress-Archive -Path $src -DestinationPath $dst -Force -ErrorAction Stop
        Write-Host "Done: $d.zip"
    } catch {
        Write-Host "FAILED: $d.zip - $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}
if ($failed -gt 0) {
    Write-Host "$failed 件の zip 化に失敗しました" -ForegroundColor Red
    exit 1
}
