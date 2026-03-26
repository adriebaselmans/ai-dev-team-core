param(
    [string]$Python = "python"
)

$requirementsPath = "framework/runtime/requirements.txt"

if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    Write-Error "Python executable '$Python' was not found. Install Python 3.12+ first, then rerun this script."
    exit 1
}

& $Python -m pip install -r $requirementsPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install runtime dependencies from $requirementsPath."
    exit $LASTEXITCODE
}

Write-Host "Runtime dependencies installed successfully."
