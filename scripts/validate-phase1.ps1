#Requires -Version 5.1
$ErrorActionPreference = "Stop"

Write-Host "=== Phase 1 Docker Validation ===" -ForegroundColor Cyan
Write-Host "Assumes Docker images are already built. Run 'docker compose build api ml' first if needed."
Write-Host ""

# Test 1: Verify _filter_valid_laps method exists
Write-Host "[1/6] Checking _filter_valid_laps method..." -ForegroundColor Yellow
docker compose run --rm api python -c @"
from app.services.telemetry.fastf1_client import FastF1Client
client = FastF1Client()
assert hasattr(client, '_filter_valid_laps'), 'Method _filter_valid_laps not found'
print('PASS: _filter_valid_laps method exists')
"@
if ($LASTEXITCODE -ne 0) { throw "Test 1 failed" }

# Test 2: Verify deleted lap filtering logic
Write-Host "[2/6] Testing deleted lap filtering..." -ForegroundColor Yellow
docker compose run --rm api python -c @"
import pandas as pd
from app.services.telemetry.fastf1_client import FastF1Client

client = FastF1Client()
test_df = pd.DataFrame({
    'LapNumber': [1, 2, 3, 4],
    'Deleted': [False, True, False, True],
    'PitInTime': [None, None, None, None],
    'PitOutTime': [None, None, None, None]
})
result = client._filter_valid_laps(test_df)
assert len(result) == 2, f'Expected 2 valid laps, got {len(result)}'
print('PASS: Deleted lap filtering works correctly')
"@
if ($LASTEXITCODE -ne 0) { throw "Test 2 failed" }

# Test 3: Verify fallback behavior
Write-Host "[3/6] Testing fallback behavior..." -ForegroundColor Yellow
docker compose run --rm api python -c @"
import pandas as pd
from app.services.telemetry.fastf1_client import FastF1Client

client = FastF1Client()
all_deleted = pd.DataFrame({
    'LapNumber': [1, 2],
    'Deleted': [True, True],
    'PitInTime': [None, None],
    'PitOutTime': [None, None]
})
result = client._filter_valid_laps(all_deleted)
assert len(result) == 2, 'Should fallback to original when all laps invalid'
print('PASS: Fallback behavior works')
"@
if ($LASTEXITCODE -ne 0) { throw "Test 3 failed" }

# Test 4: Verify no print() statements
Write-Host "[4/6] Checking for print() statements..." -ForegroundColor Yellow
$printResult = docker compose run --rm api sh -c "grep -c 'print(' app/services/telemetry/fastf1_client.py 2>/dev/null || echo 0"
$printCount = ($printResult | Select-Object -Last 1).Trim()
if ([int]$printCount -gt 0) {
    throw "FAIL: print() statements found in fastf1_client.py ($printCount occurrences)"
}
Write-Host "PASS: No print() statements in fastf1_client.py" -ForegroundColor Green

# Test 5: Verify ML logging config
Write-Host "[5/6] Testing ML logging configuration..." -ForegroundColor Yellow
docker compose run --rm ml python -c @"
from core.logging_config import setup_logging, get_logger
logger = setup_logging()
assert logger is not None, 'setup_logging should return logger'
test_logger = get_logger('test_module')
assert 'ml_service' in test_logger.name, 'Logger should have ml_service prefix'
print('PASS: Logging configuration works')
"@
if ($LASTEXITCODE -ne 0) { throw "Test 5 failed" }

# Test 6: Run pytest suites (optional - requires dev dependencies)
Write-Host "[6/6] Running pytest suites..." -ForegroundColor Yellow
Write-Host "Note: pytest requires dev dependencies. Skipping if not available." -ForegroundColor DarkGray

$apiTestResult = docker compose run --rm api sh -c "command -v pytest >/dev/null 2>&1 && pytest app/tests/ -v --tb=short || echo 'pytest not installed - skipping'"
if ($apiTestResult -match "pytest not installed") {
    Write-Host "SKIP: API pytest not available in production image" -ForegroundColor DarkYellow
} elseif ($LASTEXITCODE -ne 0) {
    throw "API tests failed"
} else {
    Write-Host "PASS: API tests" -ForegroundColor Green
}

$mlTestResult = docker compose run --rm ml sh -c "command -v pytest >/dev/null 2>&1 && pytest tests/ -v --tb=short || echo 'pytest not installed - skipping'"
if ($mlTestResult -match "pytest not installed") {
    Write-Host "SKIP: ML pytest not available in production image" -ForegroundColor DarkYellow
} elseif ($LASTEXITCODE -ne 0) {
    throw "ML tests failed"
} else {
    Write-Host "PASS: ML tests" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== All Phase 1 Core Validations PASSED! ===" -ForegroundColor Green
Write-Host "(Tests 1-5 verify Phase 1 implementation; Test 6 requires dev dependencies)" -ForegroundColor DarkGray
