#!/bin/bash
set -e

echo "=== Phase 2 Docker Validation ==="
echo "Validates delta analysis module implementation."
echo ""

# Test 1: Verify delta_analysis.py exists and imports
echo "[1/6] Checking delta_analysis module..."
docker compose run --rm ml python -c "
from services.delta_analysis import (
    DeltaResult,
    calculate_raw_delta,
    calculate_scaled_delta,
    get_delta_at_distance,
    get_delta_change_in_range
)
print('PASS: All delta_analysis exports import successfully')
"

# Test 2: Verify DeltaResult dataclass works
echo "[2/6] Testing DeltaResult dataclass..."
docker compose run --rm ml python -c "
from services.delta_analysis import DeltaResult

result = DeltaResult(
    reference_driver='VER',
    compare_driver='NOR',
    distance=[0, 1000, 2000],
    delta=[0.0, 0.1, 0.2],
    raw_delta=[0.0, 0.09, 0.18],
    official_gap=0.2,
    scaling_factor=1.111,
    telemetry_gap=0.18,
    confidence=0.85
)
assert result.reference_driver == 'VER'
assert result.official_gap == 0.2
print('PASS: DeltaResult dataclass works correctly')
"

# Test 3: Verify raw delta calculation
echo "[3/6] Testing raw delta calculation..."
docker compose run --rm ml python -c "
import numpy as np
from services.delta_analysis import calculate_raw_delta

ref_distance = np.linspace(0, 5000, 100)
ref_speed = np.full(100, 250.0)
comp_distance = np.linspace(0, 5000, 100)
comp_speed = np.full(100, 240.0)

common_dist, delta = calculate_raw_delta(ref_distance, ref_speed, comp_distance, comp_speed)

assert len(common_dist) == 1000
assert delta[-1] > 0, 'Slower driver should have positive delta'
print(f'PASS: Raw delta = {delta[-1]:.3f}s (slower driver is behind)')
"

# Test 4: Verify scaled delta matches official gap
echo "[4/6] Testing scaled delta matches official..."
docker compose run --rm ml python -c "
from services.delta_analysis import calculate_scaled_delta

ref_telemetry = {'distance': list(range(0, 5001, 50)), 'speed': [250.0] * 101}
comp_telemetry = {'distance': list(range(0, 5001, 50)), 'speed': [245.0] * 101}

result = calculate_scaled_delta(
    ref_telemetry, comp_telemetry,
    ref_official_time=90.591,
    comp_official_time=90.791,
    ref_driver='VER',
    comp_driver='NOR'
)

assert abs(result.delta[-1] - 0.200) < 0.001, f'Delta {result.delta[-1]} != 0.200'
print(f'PASS: Scaled delta {result.delta[-1]:.3f}s == official gap 0.200s')
print(f'      Scaling factor: {result.scaling_factor:.3f}')
print(f'      Confidence: {result.confidence:.2f}')
"

# Test 5: Verify query functions for corner analysis
echo "[5/6] Testing delta query functions..."
docker compose run --rm ml python -c "
import numpy as np
from services.delta_analysis import DeltaResult, get_delta_at_distance, get_delta_change_in_range

result = DeltaResult(
    reference_driver='VER',
    compare_driver='NOR',
    distance=list(np.linspace(0, 5000, 100)),
    delta=list(np.linspace(0, 0.200, 100)),
    raw_delta=list(np.linspace(0, 0.180, 100)),
    official_gap=0.200,
    scaling_factor=1.111,
    telemetry_gap=0.180,
    confidence=0.85
)

delta_mid = get_delta_at_distance(result, 2500.0)
assert abs(delta_mid - 0.100) < 0.01

change = get_delta_change_in_range(result, 1000.0, 2000.0)
assert abs(change - 0.040) < 0.01

print('PASS: Query functions work correctly')
"

# Test 6: Run unit tests (if pytest available)
echo "[6/6] Running unit tests..."
if docker compose run --rm ml sh -c "command -v pytest >/dev/null 2>&1"; then
    docker compose run --rm ml pytest tests/test_delta_analysis.py -v --tb=short
else
    echo "SKIP: pytest not available in production image"
fi

echo ""
echo "=== All Phase 2 Core Validations PASSED! ==="
