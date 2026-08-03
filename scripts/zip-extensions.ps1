# テスト拡張機能をデスクトップに zip 化するスクリプト
# 注: devtools は含めない。devtools_page 持ち拡張を読み込むと Chromium が
#     起動ハングする既知問題があるため（復旧: scripts/strip-devtools-extension.py）。
#     検証する場合のみ個別に zip 化すること。
$names = @(
    'basic',
    'contextmenu',
    'fulltab',
    'newtab',
    'notifications',
    'omnibox',
    'options',
    'phase2',
    'sidepanel'
)
$root = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$failed = 0
foreach ($n in $names) {
    $src = Join-Path $root "test-extensions\$n\*"
    $dst = Join-Path $desktop "bex-test-$n.zip"
    try {
        Compress-Archive -Path $src -DestinationPath $dst -Force -ErrorAction Stop
        Write-Host "Done: bex-test-$n.zip"
    } catch {
        Write-Host "FAILED: bex-test-$n.zip - $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}
if ($failed -gt 0) {
    Write-Host "$failed 件の zip 化に失敗しました" -ForegroundColor Red
    exit 1
}
