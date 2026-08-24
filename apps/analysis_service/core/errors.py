"""
Exception types for the analysis service.

The service historically raised nothing — failures were returned as
``(None, error_string)`` tuples or swallowed by broad handlers. WU-2
introduces the first exception type: a structured rejection for telemetry
arrays carrying non-finite values (NaN or ±inf), so a caller can distinguish
"the data was dishonest" from any other failure. Mirrors the API service's
``NativeAcquisitionError`` precedent (structured attributes plus a
deterministic message).
"""
from typing import List, Optional


class NonFiniteTelemetryError(ValueError):
    """
    A telemetry channel contained NaN or ±inf at first touch.

    Raised instead of fabricating values (interpolation or default fill):
    the governing standard is "accurate or absent, never misleading", and a
    non-finite input has no honest repaired form. Subclasses ``ValueError``
    so defensive generic handlers keep working, while remaining
    distinguishable by type.

    Attributes:
        channel: name of the offending channel/array (e.g. "ref_speed").
        n_nonfinite: how many values were NaN/inf.
        n_total: array length.
        positions: indices of the first few non-finite values.
    """

    def __init__(self, channel: str, n_nonfinite: int, n_total: int,
                 positions: Optional[List[int]] = None):
        self.channel = channel
        self.n_nonfinite = n_nonfinite
        self.n_total = n_total
        self.positions = positions or []
        shown = ", ".join(str(p) for p in self.positions)
        super().__init__(
            f"non-finite telemetry: {n_nonfinite} of {n_total} values in "
            f"'{channel}' are NaN/inf (first at indices [{shown}])"
        )
