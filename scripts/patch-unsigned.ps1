$ErrorActionPreference = 'Stop'
$path = Join-Path $PWD 'deepseek-harness\apps\desktop\electron-builder.config.mjs'
$text = [System.IO.File]::ReadAllText($path)

function Replace-Exact([string]$old, [string]$new, [string]$label) {
  if (-not $script:text.Contains($old)) { throw "Patch anchor not found: $label" }
  $script:text = $script:text.Replace($old, $new)
}

Replace-Exact @'
  const packagesWindows = targetPlatform === 'win32'
'@ @'
  const packagesWindows = targetPlatform === 'win32'
  const unsigned = env.DSH_DESKTOP_UNSIGNED === '1'
  if (unsigned && !packagesWindows) throw new Error('desktop package: unsigned builds require Windows')
'@ 'unsigned flag'

Replace-Exact @'
  const windowsSigner = packagesWindows
    ? createWindowsTokenSigner({
'@ @'
  const windowsSigner = packagesWindows && !unsigned
    ? createWindowsTokenSigner({
'@ 'skip Windows signer'

Replace-Exact @'
  const update = resolveDesktopAutoUpdateConfig(env, resolvedPlatform, resolvedArch)
'@ @'
  const update = unsigned ? undefined : resolveDesktopAutoUpdateConfig(env, resolvedPlatform, resolvedArch)
'@ 'disable updater for unsigned build'

Replace-Exact @'
    artifactName: 'deepseek-harness-${version}-${os}-${arch}.${ext}',
'@ @'
    artifactName: `deepseek-harness-${version}-${os}-${arch}${unsigned ? '-unsigned' : ''}.${ext}`,
'@ 'unsigned artifact suffix'

Replace-Exact @'
      forceCodeSigning: true,
'@ @'
      forceCodeSigning: !unsigned,
'@ 'disable forceCodeSigning'

Replace-Exact @'
    publish: [{ provider: 'generic', url: update.publicUrl }],
'@ @'
    publish: update === undefined ? null : [{ provider: 'generic', url: update.publicUrl }],
'@ 'disable publish config'

[System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))

Push-Location 'deepseek-harness'
$changed = @(git diff --name-only)
if ($changed.Count -ne 1 -or $changed[0] -ne 'apps/desktop/electron-builder.config.mjs') {
  git diff --name-status
  throw 'Unexpected source changes detected.'
}
git diff --check
git diff -- apps/desktop/electron-builder.config.mjs
Pop-Location
