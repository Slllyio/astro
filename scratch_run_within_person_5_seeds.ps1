# Within-person concordance — scale up to 5 seeds × top-5 classes × 1000 perms.
# Only run this AFTER the seed=1 probe (within_person_seed1.md) shows signal.
# Each seed = ~25 min, total ~2 h wall.

$ErrorActionPreference = "Continue"
$OutDir = "data/ml_runs/fork_a_stage_d_subsample"

$Failed = @()
for ($s = 1; $s -le 5; $s++) {
    $started = Get-Date
    Write-Host ("[within5] seed={0} starting at {1}" -f $s, $started.ToString("HH:mm:ss"))
    py -3.12 -m app.medini.ml.stage_d_within_person `
        --seed $s `
        --n-perm 1000 `
        --out "$OutDir/within_person_seed$s.md"
    $rc = $LASTEXITCODE
    $ended = Get-Date
    $mins = [math]::Round(($ended - $started).TotalMinutes, 1)
    if ($rc -ne 0) {
        Write-Warning ("[within5] seed {0} FAILED rc={1} after {2}min" -f $s, $rc, $mins)
        $Failed += $s
    } else {
        Write-Host ("[within5] seed={0} done in {1}min at {2}" -f $s, $mins, $ended.ToString("HH:mm:ss"))
    }
}

if ($Failed.Count -gt 0) {
    $Failed -join "`n" | Out-File -Encoding utf8 "$OutDir/within_person_FAILED.txt"
    Write-Host ("[within5] complete with {0} failures; see {1}/within_person_FAILED.txt" -f $Failed.Count, $OutDir)
} else {
    Write-Host "[within5] all 5 seeds complete"
}
