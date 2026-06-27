import json, subprocess, sys

def test_cli_prints_json_chart():
    out = subprocess.run(
        [sys.executable, "-m", "app.raman_saab", "--name", "T", "--date", "1990-07-15",
         "--time", "12:00", "--tz", "5.5", "--lat", "12.97", "--lon", "77.59", "--format", "json"],
        capture_output=True, text=True, check=True)
    data = json.loads(out.stdout)
    assert data["ayanamsa"] == "lahiri"  # user-facing default is Lahiri (project-locked standard)
    assert len(data["planets"]) == 9
