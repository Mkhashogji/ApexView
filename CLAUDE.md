# ApexView F1 Engineering App - Project Rules

## Code Standards
- **Python**: 3.12+ with full type hints on all functions
- **Formatting**: Black (line-length=100), isort for imports
- **Logging**: Use `logging` module exclusively, never `print()` for diagnostics
- **Schemas**: Pydantic BaseModel for all API request/response types
- **Testing**: pytest with descriptive test names (`test_should_filter_deleted_laps`)

## Error Handling Patterns
- Always handle None/NaN/empty arrays gracefully
- Provide fallback values with WARNING-level log messages
- Never let exceptions propagate silently in production code
- Use try/except with specific exception types, not bare except

## Git Workflow
- Feature branch: `feature/ai-insights-v2`
- Commit format: `feat(ai-insights): Phase N.X - Brief description`
- Commit after each successful validation gate
- Do not proceed to next phase until current phase passes validation

## Module Standards
Every new Python module must include:
1. Module docstring explaining purpose
2. `_safe_array()` utility for array handling (see below)
3. Logger initialization: `logger = logging.getLogger(__name__)`
4. Type hints on all public functions

## Standard Utility (Include in all new modules)
```python
import numpy as np
import logging

logger = logging.getLogger(__name__)

def _safe_array(arr, default_value: float = 0.0) -> np.ndarray:
    """
    Safely convert input to numpy array, handling None/empty/NaN cases.

    Args:
        arr: Input (list, np.ndarray, None, or empty)
        default_value: Fallback for empty/invalid arrays

    Returns:
        np.ndarray with at least one valid element
    """
    if arr is None or (hasattr(arr, '__len__') and len(arr) == 0):
        logger.warning(f"Empty/None array received, using default [{default_value}]")
        return np.array([default_value])

    result = np.array(arr, dtype=float)

    if np.any(np.isnan(result)):
        nan_count = np.sum(np.isnan(result))
        logger.warning(f"Array contains {nan_count} NaN values, interpolating")
        mask = np.isnan(result)
        if np.any(~mask):
            result[mask] = np.interp(
                np.flatnonzero(mask),
                np.flatnonzero(~mask),
                result[~mask]
            )
        else:
            result = np.full_like(result, default_value)

    return result
```

## Performance Guidelines
- Use numpy vectorized operations, avoid Python loops for arrays
- Cache expensive calculations where appropriate
- Target <2 second response time for API endpoints
