#!/bin/bash
# Smoke Test Runner for Phase G1.9
# Usage: ./run_smoke_test_g19.sh

echo "Starting Smoke Test G1.9..."

# 1. Run Growth Runner with Smoke Config
echo "Running Growth Runner..."
# Note: Assuming running from repo root
python tools/growth_runner.py --config growth/runs/run_configs/smoke_test_g19.yaml

if [ $? -ne 0 ]; then
    echo "Runner failed!"
    exit 1
fi

# 2. Verify Output
echo "Verifying Output..."
python tools/verify_smoke_test.py

if [ $? -ne 0 ]; then
    echo "Verification failed!"
    exit 1
fi

echo "Done."
