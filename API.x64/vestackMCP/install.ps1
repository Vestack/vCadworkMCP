<#
.SYNOPSIS
    Installs the vestackMCP plugin into a Cadwork user profile.

.DESCRIPTION
    - copies the plugin files into <profile>\3d\API.x64\vestackMCP,
    - writes mcp_home.txt there, pointing at this repository checkout,
    - optionally removes the old ...\API.x64\MCPBridge folder (-RemoveOld),
    - creates a desktop shortcut that starts Cadwork and runs the plugin, which
      starts the bridge on port 53002 (skipped with -NoShortcut).

    Run it from anywhere:  powershell -ExecutionPolicy Bypass -File <checkout>\API.x64\vestackMCP\install.ps1
    Restart Cadwork afterwards so it rescans its plugin folder.

.PARAMETER Profile
    Cadwork version of the user profile: 2026 (default) or 30.

.PARAMETER RemoveOld
    Remove the previous MCPBridge plugin folder of that profile if present.

.PARAMETER NoShortcut
    Do not create the desktop shortcut.
#>
[CmdletBinding()]
param(
    [ValidateSet('2026', '30')]
    [string]$Profile = '2026',

    [switch]$RemoveOld,

    [switch]$NoShortcut
)

$ErrorActionPreference = 'Stop'

$PluginName   = 'vestackMCP'
$CadworkDir   = 'C:\Program Files\cadwork.dir'
$CiStart      = Join-Path $CadworkDir 'ci_start.exe'
$ExeDir       = Join-Path $CadworkDir ('EXE_' + $Profile)
$ProfileDir   = Join-Path 'C:\Users\Public\Documents\cadwork' ('userprofil_' + $Profile)
$ApiDir       = Join-Path $ProfileDir '3d\API.x64'
$TargetDir    = Join-Path $ApiDir $PluginName
$OldDir       = Join-Path $ApiDir 'MCPBridge'
$PluginFiles  = @('vestackMCP.py', 'plugin_info.xml', 'Icon.png', 'icon.svg', 'README.md')

# This script sits in <checkout>\API.x64\vestackMCP; the checkout is two levels up.
$SourceDir = $PSScriptRoot
$RepoRoot  = Split-Path (Split-Path $SourceDir -Parent) -Parent

function Stop-Install([string]$Message) {
    Write-Error "vestackMCP install: $Message"
    exit 1
}

# Check everything before touching anything.
if (-not (Test-Path -LiteralPath $ProfileDir -PathType Container)) {
    Stop-Install "Cadwork profile folder not found: $ProfileDir (is Cadwork $Profile installed, and did it run once?)"
}
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'cadwork_bridge.py'))) {
    Stop-Install "cadwork_bridge.py not found in $RepoRoot. Run this script from a vCadworkMCP checkout."
}
foreach ($name in $PluginFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $SourceDir $name))) {
        Stop-Install "plugin file missing next to this script: $name"
    }
}
if (-not $NoShortcut) {
    if (-not (Test-Path -LiteralPath $CiStart)) {
        Stop-Install "ci_start.exe not found: $CiStart (use -NoShortcut to install the plugin only)"
    }
    if (-not (Test-Path -LiteralPath $ExeDir -PathType Container)) {
        Stop-Install "Cadwork executable folder not found: $ExeDir (use -NoShortcut to install the plugin only)"
    }
}

# Plugin files.
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
foreach ($name in $PluginFiles) {
    Copy-Item -LiteralPath (Join-Path $SourceDir $name) -Destination $TargetDir -Force
}
Write-Host "Copied $($PluginFiles.Count) files to $TargetDir"

# Checkout pointer. UTF-8 without BOM: the plugin reads the first line as is, and
# Windows PowerShell 5 would add a BOM with Set-Content -Encoding UTF8.
$pointer = Join-Path $TargetDir 'mcp_home.txt'
[System.IO.File]::WriteAllText($pointer, $RepoRoot + "`r`n", (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Wrote $pointer -> $RepoRoot"

# Old plugin folder.
if ($RemoveOld) {
    if (Test-Path -LiteralPath $OldDir) {
        Write-Host "Removing old plugin folder $OldDir"
        Remove-Item -LiteralPath $OldDir -Recurse -Force
    } else {
        Write-Host "No old plugin folder at $OldDir"
    }
}

# Desktop shortcut: Cadwork opens, then runs the plugin (ci_start.exe /PLUGIN=<folder name>).
if (-not $NoShortcut) {
    $desktop      = [Environment]::GetFolderPath('Desktop')
    $shortcutPath = Join-Path $desktop ("Cadwork $Profile + $PluginName.lnk")
    $shell        = New-Object -ComObject WScript.Shell
    $shortcut     = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath       = $CiStart
    $shortcut.Arguments        = '/EXE="' + $ExeDir + '" /PLUGIN=' + $PluginName
    $shortcut.WorkingDirectory = $CadworkDir
    $shortcut.Save()
    Write-Host "Created shortcut $shortcutPath"
}

Write-Host "Done. Restart Cadwork so it rescans its plugin folder."
