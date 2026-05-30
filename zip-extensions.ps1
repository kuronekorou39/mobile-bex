$dirs = @(
    'test-extension',
    'test-extension-contextmenu',
    'test-extension-devtools',
    'test-extension-fulltab',
    'test-extension-newtab',
    'test-extension-notifications',
    'test-extension-omnibox',
    'test-extension-options',
    'test-extension-phase2',
    'test-extension-sidepanel'
)
foreach ($d in $dirs) {
    $src = "C:\projects\mobile-bex\$d\*"
    $dst = "C:\Users\kuronekorou39\Desktop\$d.zip"
    Compress-Archive -Path $src -DestinationPath $dst -Force
    Write-Host "Done: $d.zip"
}
