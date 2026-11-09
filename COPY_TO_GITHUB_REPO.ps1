param(
    [Parameter(Position = 0)]
    [string]$DestinationPath
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path.TrimEnd('\')
function Get-PackageRelativePath([string]$Path) {
    return $Path.Substring($sourceRoot.Length).TrimStart('\', '/')
}

Write-Host 'Ethiopian Bible Library package → GitHub clone' -ForegroundColor Cyan
Write-Host 'Use the repository root opened with GitHub Desktop: Repository → Show in Explorer.'
$destinationInput = $DestinationPath
if ([string]::IsNullOrWhiteSpace($destinationInput)) {
    Write-Host 'Tip: drag the GitHub clone folder onto COPY_TO_GITHUB_REPO.bat to fill this in.'
    $destinationInput = Read-Host 'GitHub clone folder'
}
if ([string]::IsNullOrWhiteSpace($destinationInput)) {
    throw 'No destination folder was entered.'
}
if (-not (Test-Path -LiteralPath $destinationInput -PathType Container)) {
    throw "Destination folder does not exist: $destinationInput"
}
$destinationRoot = (Resolve-Path -LiteralPath $destinationInput).Path.TrimEnd('\')
if ($sourceRoot -eq $destinationRoot) {
    throw 'The package folder cannot also be the destination clone.'
}
$gitMetadata = Join-Path $destinationRoot '.git'
if (-not (Test-Path -LiteralPath $gitMetadata)) {
    throw 'Destination is not a Git clone: its root has no .git directory or worktree marker.'
}

$sourceManifest = Join-Path $sourceRoot 'archive-manifest.json'
$verifier = Join-Path $sourceRoot 'verify_package_copy.py'
if (-not (Test-Path -LiteralPath $sourceManifest) -or -not (Test-Path -LiteralPath $verifier)) {
    throw 'The package manifest or verifier is missing from this folder.'
}

$sourceFiles = Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Force | Where-Object {
    $relative = Get-PackageRelativePath $_.FullName
    $parts = $relative -split '[\\/]'
    ($parts -notcontains '.git') -and ($parts -notcontains '__pycache__') -and ($parts -notcontains 'tmp') -and ($_.Extension -ne '.pyc')
}
$conflicts = @($sourceFiles | Where-Object {
    $relative = Get-PackageRelativePath $_.FullName
    Test-Path -LiteralPath (Join-Path $destinationRoot $relative) -PathType Leaf
})

Write-Host "`nPackage files to copy: $($sourceFiles.Count)"
Write-Host 'Destination-only files will be left untouched. The destination .git metadata will be preserved.'
if ($conflicts.Count -gt 0) {
    Write-Host "Matching paths to replace: $($conflicts.Count)" -ForegroundColor Yellow
    $conflicts | Select-Object -First 12 | ForEach-Object {
        Write-Host ('  ' + (Get-PackageRelativePath $_.FullName))
    }
    if ($conflicts.Count -gt 12) { Write-Host "  … and $($conflicts.Count - 12) more" }
    Write-Host 'Review these files in GitHub Desktop after the copy.' -ForegroundColor Yellow
}
$confirmation = Read-Host 'Type COPY to proceed; any other response cancels'
if ($confirmation -cne 'COPY') {
    Write-Host 'Copy cancelled. No destination files were changed.'
    exit 0
}

& robocopy $sourceRoot $destinationRoot /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XD '.git' '__pycache__' 'tmp' /XF '*.pyc' '*.pyo' /NFL /NDL /NJH /NJS /NP
$copyExitCode = $LASTEXITCODE
if ($copyExitCode -ge 8) {
    throw "Robocopy reported a copy failure (exit code $copyExitCode). Review its output; it did not delete destination files."
}

Push-Location -LiteralPath $destinationRoot
try {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -B verify_package_copy.py
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -B verify_package_copy.py
    } else {
        throw 'Files were copied, but Python 3 was not found, so the manifest could not be verified.'
    }
    if ($LASTEXITCODE -ne 0) {
        throw 'Files were copied, but the destination manifest verification failed.'
    }
} finally {
    Pop-Location
}
Write-Host "`nPackage copy and manifest verification completed. Inspect the change list in GitHub Desktop before committing or pushing." -ForegroundColor Green
