# Task 19 — main 10-seed run on 2000-person subsample.
# Run AFTER Task 18 + noise_floor.json have been computed (sub-gate D.4
# threshold needs sigma_noise to evaluate G2 over the main records).

$ErrorActionPreference = "Stop"
$OutDir = "data/ml_runs/fork_a_stage_d_subsample"

$Failed = @()
for ($s = 1; $s -le 10; $s++) {
    Write-Host ("[task19] seed={0} starting at {1}" -f $s, (Get-Date -Format "HH:mm:ss"))
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split main --subsample --out-dir $OutDir
    if (-not $?) {
        Write-Warning ("seed {0} FAILED" -f $s)
        $Failed += $s
    }
    Write-Host ("[task19] seed={0} done at {1}" -f $s, (Get-Date -Format "HH:mm:ss"))
}

if ($Failed.Count -gt 0) {
    $Failed -join "`n" | Out-File -Encoding utf8 "$OutDir/main_FAILED.txt"
    Write-Error ("{0} seed(s) failed; see {1}/main_FAILED.txt" -f $Failed.Count, $OutDir)
    exit 1
}
Write-Host "[task19] all 10 seeds complete"
