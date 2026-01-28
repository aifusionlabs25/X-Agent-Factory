Write-Host "Starting Smoke Test G1.9..."

# 1. Run Growth Runner with Smoke Config
Write-Host "Running Growth Runner..."
python tools/growth_runner.py --config growth/runs/run_configs/smoke_test_g19.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "Runner failed!"
    exit 1
}

# 2. Verify Output
Write-Host "Verifying Output..."
python tools/verify_smoke_test.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Verification failed!"
    exit 1
}

Write-Host "Done."
