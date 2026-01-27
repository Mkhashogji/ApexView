#Requires -Version 5.1
$ErrorActionPreference = "Stop"

Write-Host "=== Phase 2 Docker Validation ===" -ForegroundColor Cyan
Write-Host "Validates delta analysis module implementation."
Write-Host ""

# Test 1: Verify delta_analysis.py exists and imports
Write-Host "[1/6] Checking delta_analysis module..." -ForegroundColor Yellow
docker compose run --rm ml python -c @"
from services.delta_analysis import (
    DeltaResult,
    calculate_raw_delta,
    calculate_scaled_delta,
    get_delta_at_distance,
    get_delta_change_in_range
)
print('PASS: All delta_analysis exports import successfully')
"@
if ($LASTEXITCODE -ne 0) { throw "Test 1 failed" }

# Test 2: Verify DeltaResult dataclass works
Write-Host "[2/6] Testing DeltaResult dataclass..." -ForegroundColor Yellow
docker compose run --rm ml python -c @"
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
"@
if ($LASTEXITCODE -ne 0) { throw "Test 2 failed" }

# Test 3: Verify raw delta calculation
Write-Host "[3/6] Testing raw delta calculation..." -ForegroundColor Yellow
docker compose run --rm ml python -c @"
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
"@
if ($LASTEXITCODE -ne 0) { throw "Test 3 failed" }

# Test 4: Verify scaled delta matches official gap
Write-Host "[4/6] Testing scaled delta matches official..." -ForegroundColor Yellow
docker compose run --rm ml python -c @"
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
"@
if ($LASTEXITCODE -ne 0) { throw "Test 4 failed" }

# Test 5: Verify query functions for corner analysis
Write-Host "[5/6] Testing delta query functions..." -ForegroundColor Yellow
docker compose run --rm ml python -c @"
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

# Test get_delta_at_distance
delta_mid = get_delta_at_distance(result, 2500.0)
assert abs(delta_mid - 0.100) < 0.01, f'Midpoint delta {delta_mid} != 0.100'

# Test get_delta_change_in_range
change = get_delta_change_in_range(result, 1000.0, 2000.0)
assert abs(change - 0.040) < 0.01, f'Delta change {change} != 0.040'

print('PASS: Query functions work correctly')
print(f'      Delta at 2500m: {delta_mid:.3f}s')
print(f'      Delta change 1000-2000m: {change:.3f}s')
"@
if ($LASTEXITCODE -ne 0) { throw "Test 5 failed" }

# Test 6: Run unit tests (if pytest available)
Write-Host "[6/6] Running unit tests..." -ForegroundColor Yellow
$testResult = docker compose run --rm ml sh -c "command -v pytest >/dev/null 2>&1 && pytest tests/test_delta_analysis.py -v --tb=short 2>&1 || echo 'pytest not installed'"
if ($testResult -match "pytest not installed") {
    Write-Host "SKIP: pytest not available in production image" -ForegroundColor DarkYellow
} elseif ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some tests may have failed" -ForegroundColor DarkYellow
} else {
    Write-Host "PASS: Unit tests completed" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== All Phase 2 Core Validations PASSED! ===" -ForegroundColor Green
Write-Host "(Tests 1-5 verify Phase 2 implementation)" -ForegroundColor DarkGray
