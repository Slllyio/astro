# Stage D — 5-seed confirmation run on 2000p subsample, DML.
# If 5/5 seeds show mean(delta) <= -0.05, the NULL VERDICT is locked in
# and we can write DECISION.md without committing to the full 30.
# If results vary widely, one seed was unlucky and we proceed cautiously.

$ErrorActionPreference = "Continue"
$OutDir = "data/ml_runs/fork_a_stage_d_subsample"
New-Item -ItemType Directory -Force $OutDir | Out-Null

$Failed = @()
for ($s = 1; $s -le 5; $s++) {
    $started = Get-Date
    Write-Host ("[5seeds] seed={0} starting at {1}" -f $s, $started.ToString("HH:mm:ss"))
    py -3.12 -m app.medini.ml.stage_d_train --seed $s --split main --subsample --device dml --out-dir $OutDir
    $rc = $LASTEXITCODE
    $ended = Get-Date
    $mins = [math]::Round(($ended - $started).TotalMinutes, 1)
    if ($rc -ne 0) {
        Write-Warning ("[5seeds] seed {0} FAILED rc={1} after {2}min" -f $s, $rc, $mins)
        $Failed += $s
    } else {
        Write-Host ("[5seeds] seed={0} done in {1}min at {2}" -f $s, $mins, $ended.ToString("HH:mm:ss"))
    }
}

if ($Failed.Count -gt 0) {
    $Failed -join "`n" | Out-File -Encoding utf8 "$OutDir/main_FAILED.txt"
    Write-Host ("[5seeds] complete with {0} failures; see {1}/main_FAILED.txt" -f $Failed.Count, $OutDir)
} else {
    Write-Host "[5seeds] all 5 seeds complete"
}
