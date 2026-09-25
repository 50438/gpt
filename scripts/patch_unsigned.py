from pathlib import Path
import re
import subprocess

root = Path('deepseek-harness')
path = root / 'apps/desktop/electron-builder.config.mjs'
text = path.read_text(encoding='utf-8')

def sub_once(pattern: str, repl: str, label: str) -> None:
    global text
    text, count = re.subn(pattern, repl, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f'Patch anchor count for {label}: {count}, expected 1')

sub_once(
    r"^  const packagesWindows = targetPlatform === 'win32'$",
    "  const packagesWindows = targetPlatform === 'win32'\n"
    "  const unsigned = env.DSH_DESKTOP_UNSIGNED === '1'\n"
    "  if (unsigned && !packagesWindows) throw new Error('desktop package: unsigned builds require Windows')",
    'unsigned flag',
)

sub_once(
    r"^  const windowsSigner = packagesWindows\r?\n    \? createWindowsTokenSigner\(\{$",
    "  const windowsSigner = packagesWindows && !unsigned\n    ? createWindowsTokenSigner({",
    'skip Windows signer',
)

sub_once(
    r"^  const update = resolveDesktopAutoUpdateConfig\(env, resolvedPlatform, resolvedArch\)\r?\n  const buildPaths = desktopTargetBuildPaths\(update\.target\)$",
    "  const update = unsigned ? undefined : resolveDesktopAutoUpdateConfig(env, resolvedPlatform, resolvedArch)\n"
    "  const buildPaths = desktopTargetBuildPaths(unsigned ? 'win-x64' : update.target)",
    'disable updater for unsigned build',
)

sub_once(
    r"^    artifactName: 'deepseek-harness-\$\{version\}-\$\{os\}-\$\{arch\}\.\$\{ext\}',$",
    "    artifactName: `deepseek-harness-${version}-${os}-${arch}${unsigned ? '-unsigned' : ''}.${ext}`,",
    'unsigned artifact suffix',
)

sub_once(
    r"^    win: \{\r?\n      forceCodeSigning: true,$",
    "    win: {\n      forceCodeSigning: !unsigned,",
    'disable Windows forceCodeSigning',
)

sub_once(
    r"^    publish: \[\{ provider: 'generic', url: update\.publicUrl \}\],$",
    "    publish: update === undefined ? null : [{ provider: 'generic', url: update.publicUrl }],",
    'disable publish config',
)

path.write_text(text, encoding='utf-8', newline='\n')

changed = subprocess.check_output(['git', 'diff', '--name-only'], cwd=root, text=True).splitlines()
if changed != ['apps/desktop/electron-builder.config.mjs']:
    subprocess.run(['git', 'diff', '--name-status'], cwd=root, check=False)
    raise SystemExit(f'Unexpected source changes: {changed}')
subprocess.run(['git', 'diff', '--check'], cwd=root, check=True)
subprocess.run(['git', 'diff', '--', 'apps/desktop/electron-builder.config.mjs'], cwd=root, check=True)
