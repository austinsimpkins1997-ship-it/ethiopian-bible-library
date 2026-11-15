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

# Verify first, then copy only the canonical public manifest inventory.
Push-Location -LiteralPath $sourceRoot
try {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -B verify_archive_manifest.py
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -B verify_archive_manifest.py
    } else { throw 'Python 3 is required to verify this package before copying.' }
    if ($LASTEXITCODE -ne 0) { throw 'Source manifest failed; no destination files were changed.' }
} finally { Pop-Location }
$manifest = Get-Content -LiteralPath $sourceManifest -Raw -Encoding UTF8 | ConvertFrom-Json
$sourceFiles = @($manifest.files | ForEach-Object {
    Get-Item -LiteralPath (Join-Path $sourceRoot $_.path)
}) + @(Get-Item -LiteralPath $sourceManifest)
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

foreach ($sourceFile in $sourceFiles) {
    $relative = Get-PackageRelativePath $sourceFile.FullName
    $target = [System.IO.Path]::GetFullPath((Join-Path $destinationRoot $relative))
    if (-not $target.StartsWith($destinationRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Destination path is outside the clone: $relative"
    }
    $parent = [System.IO.Path]::GetDirectoryName($target)
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile.FullName -Destination $target -Force
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
