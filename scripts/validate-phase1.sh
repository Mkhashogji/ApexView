#!/bin/bash
set -e

echo "=== Phase 1 Docker Validation ==="
echo "Assumes Docker images are already built. Run 'docker compose build api ml' first if needed."
echo ""

# Test 1: Verify _filter_valid_laps method exists
echo "[1/6] Checking _filter_valid_laps method..."
docker compose run --rm api python -c "
from app.services.telemetry.fastf1_client import FastF1Client
client = FastF1Client()
assert hasattr(client, '_filter_valid_laps'), 'Method _filter_valid_laps not found'
print('PASS: _filter_valid_laps method exists')
"

# Test 2: Verify deleted lap filtering logic
echo "[2/6] Testing deleted lap filtering..."
docker compose run --rm api python -c "
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
"

# Test 3: Verify fallback behavior when all laps invalid
echo "[3/6] Testing fallback behavior..."
docker compose run --rm api python -c "
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
"

# Test 4: Verify no print() statements remain
echo "[4/6] Checking for print() statements..."
docker compose run --rm api sh -c "
if grep -q 'print(' app/services/telemetry/fastf1_client.py; then
    echo 'FAIL: print() statements found in fastf1_client.py'
    exit 1
else
    echo 'PASS: No print() statements in fastf1_client.py'
fi
"

# Test 5: Verify ML logging config
echo "[5/6] Testing ML logging configuration..."
docker compose run --rm ml python -c "
from core.logging_config import setup_logging, get_logger
logger = setup_logging()
assert logger is not None, 'setup_logging should return logger'
test_logger = get_logger('test_module')
assert 'ml_service' in test_logger.name, 'Logger should have ml_service prefix'
print('PASS: Logging configuration works')
"

# Test 6: Run pytest suites (optional - requires dev dependencies)
echo "[6/6] Running pytest suites..."
echo "Note: pytest requires dev dependencies. Skipping if not available."

if docker compose run --rm api sh -c "command -v pytest >/dev/null 2>&1"; then
    echo "--- API Tests ---"
    docker compose run --rm api pytest app/tests/ -v --tb=short
else
    echo "SKIP: API pytest not available in production image"
fi

if docker compose run --rm ml sh -c "command -v pytest >/dev/null 2>&1"; then
    echo "--- ML Tests ---"
    docker compose run --rm ml pytest tests/ -v --tb=short
else
    echo "SKIP: ML pytest not available in production image"
fi

echo ""
echo "=== All Phase 1 Core Validations PASSED! ==="
echo "(Tests 1-5 verify Phase 1 implementation; Test 6 requires dev dependencies)"
