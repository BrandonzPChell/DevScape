# Invoke-Guardians.ps1
# This script mirrors the Makefile targets for running guardians using tox.

param(
    [string]$Target = "all_tox_guardians"
)

$overallSuccess = $true

function Run-ToxGuardian {
    param(
        [string]$EnvList,
        [string]$ParallelFlag = "auto"
    )
    Write-Host "Invoking tox environments: $($EnvList) with parallel flag: $($ParallelFlag)"
    try {
        if ($ParallelFlag -eq "") {
            tox -e $EnvList
        } else {
            tox -p $ParallelFlag -e $EnvList
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Tox command failed for environments: $($EnvList)"
            $script:overallSuccess = $false
        }
    }
    catch {
        Write-Error "An error occurred while running tox: $($_.Exception.Message)"
        $script:overallSuccess = $false
    }
}

switch ($Target) {
    "all_tox_guardians" {
        Write-Host "Running all configured tox environments in parallel..."
        Run-ToxGuardian -EnvList "coverage,bandit,mypy,black,isort,safety" -ParallelFlag "auto"
    }
    "lint_guardian" {
        Write-Host "Running only the lint guardian (pre-commit)..."
        try {
            pre-commit run --all-files
            if ($LASTEXITCODE -ne 0) {
                Write-Error "pre-commit command failed."
                $script:overallSuccess = $false
            }
        }
        catch {
            Write-Error "An error occurred while running pre-commit: $($_.Exception.Message)"
            $script:overallSuccess = $false
        }
    }
    "safety_guardian" {
        Write-Host "Running only the safety dependency vulnerability scan..."
        Run-ToxGuardian -EnvList "safety" -ParallelFlag ""
    }
    "coverage_guardian" {
        Write-Host "Running only the test coverage beacon..."
        Run-ToxGuardian -EnvList "coverage" -ParallelFlag ""
    }
    "mypy_guardian" {
        Write-Host "Running only the mypy type checker..."
        Run-ToxGuardian -EnvList "mypy" -ParallelFlag ""
    }
    "bandit_guardian" {
        Write-Host "Running only the bandit security scanner..."
        Run-ToxGuardian -EnvList "bandit" -ParallelFlag ""
    }
    default {
        Write-Error "Invalid target specified. Available targets: all_tox_guardians, lint_guardian, safety_guardian, coverage_guardian, mypy_guardian, bandit_guardian"
        exit 1
    }
}

if ($overallSuccess) {
    Write-Host "`nAll guardians passed ✅`" -ForegroundColor Green
} else {
    Write-Host "`nSome guardians failed ❌`" -ForegroundColor Red
    exit 1
}
