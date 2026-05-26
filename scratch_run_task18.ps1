# Task 18 — noise floor (20 seeds) on 2000-person subsample.
#
# Each seed writes one record to
#   data/ml_runs/fork_a_stage_d_subsample/noise_floor_run.jsonl
# and one model file to
#   data/ml_runs/fork_a_stage_d_subsample/models/seed_NNN_deephit.pt
#
# Expected wall-clock at subsample scale: 10-20 min/seed * 20 = 3-7 h.
# If a seed fails (non-zero exit), the loop breaks and writes the failed
# seed to noise_floor_FAILED.txt so we can resume from that seed.

$ErrorActionPreference = "Stop"
$OutDir = "data/ml_runs/fork_a_stage_d_subsample"
New-Item -ItemType Directory -Force $OutDir | Out-Null

$Failed = @()
for ($s = 101; $s -le 120; $s++) {
    Write-Host ("[task18] seed={0} starting at {1}" -f $s, (Get-Date -Format "HH:mm:ss"))
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split noise_floor --subsample --out-dir $OutDir
    if (-not $?) {
        Write-Warning ("seed {0} FAILED -- saved to FAILED list" -f $s)
        $Failed += $s
    }
    Write-Host ("[task18] seed={0} done at {1}" -f $s, (Get-Date -Format "HH:mm:ss"))
}

if ($Failed.Count -gt 0) {
    $Failed -join "`n" | Out-File -Encoding utf8 "$OutDir/noise_floor_FAILED.txt"
    Write-Error ("{0} seed(s) failed; see {1}/noise_floor_FAILED.txt" -f $Failed.Count, $OutDir)
    exit 1
}
Write-Host "[task18] all 20 seeds complete"
