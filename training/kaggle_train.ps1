# Push, monitor, and download the Kaggle GPU training run for the breed classifier.
#
#   .\training\kaggle_train.ps1 push     # upload kernel + start the GPU run
#   .\training\kaggle_train.ps1 status   # one-shot status check
#   .\training\kaggle_train.ps1 watch    # poll status until the run finishes
#   .\training\kaggle_train.ps1 output   # download weights into backend\models\breed
#
# Requires the kaggle CLI (python -m pip install kaggle) and ~/.kaggle/kaggle.json.

param(
    [ValidateSet("push", "status", "watch", "output")]
    [string]$Action = "push"
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"  # kaggle CLI writes logs with the console codepage otherwise

$kernelDir = Join-Path $PSScriptRoot "kaggle\breed_classifier"
$meta = Get-Content (Join-Path $kernelDir "kernel-metadata.json") -Raw | ConvertFrom-Json
$kernelRef = $meta.id
$repoRoot = Split-Path $PSScriptRoot
$modelDir = Join-Path $repoRoot "backend\models\breed"

function Resolve-KaggleCli {
    $cmd = Get-Command kaggle -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        $candidate = Join-Path (Split-Path $py.Source) "Scripts\kaggle.exe"
        if (Test-Path $candidate) { return $candidate }
    }
    throw "kaggle CLI not found. Install it with: python -m pip install kaggle"
}

$kaggle = Resolve-KaggleCli

switch ($Action) {
    "push" {
        & $kaggle kernels push -p $kernelDir
        Write-Host ""
        Write-Host "Run page: https://www.kaggle.com/code/$kernelRef"
        Write-Host "Check progress with: .\training\kaggle_train.ps1 watch"
    }
    "status" {
        & $kaggle kernels status $kernelRef
    }
    "watch" {
        while ($true) {
            $line = (& $kaggle kernels status $kernelRef) -join " "
            Write-Host ("{0}  {1}" -f (Get-Date -Format "HH:mm:ss"), $line)
            if ($line -notmatch '(?i)(running|queued)') { break }
            Start-Sleep -Seconds 60
        }
        Write-Host "Download outputs with: .\training\kaggle_train.ps1 output"
    }
    "output" {
        New-Item -ItemType Directory -Force $modelDir | Out-Null
        & $kaggle kernels output $kernelRef -p $modelDir
        Write-Host ""
        Write-Host "Files in ${modelDir}:"
        Get-ChildItem $modelDir | Format-Table Name, Length, LastWriteTime -AutoSize
        Write-Host "The backend picks these up automatically (BREED_MODEL_DIR, default backend/models/breed)."
    }
}
