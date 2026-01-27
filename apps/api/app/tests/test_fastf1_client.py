"""
Unit tests for FastF1Client, focusing on _filter_valid_laps() method.

These tests verify the Phase 1.1 implementation of deleted lap filtering.
"""
import pytest
import pandas as pd
import numpy as np
from app.services.telemetry.fastf1_client import FastF1Client


class TestFilterValidLaps:
    """Tests for the _filter_valid_laps() method."""

    @pytest.fixture
    def client(self):
        """Create a FastF1Client instance for testing."""
        return FastF1Client()

    def test_filters_deleted_laps(self, client):
        """Should filter out laps marked as Deleted=True."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3, 4],
            'Deleted': [False, True, False, True],
            'PitInTime': [None, None, None, None],
            'PitOutTime': [None, None, None, None]
        })
        result = client._filter_valid_laps(df)
        assert len(result) == 2
        assert list(result['LapNumber']) == [1, 3]

    def test_filters_pit_in_laps(self, client):
        """Should filter out laps with pit entry (PitInTime is not NaN)."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'Deleted': [False, False, False],
            'PitInTime': [None, pd.Timestamp('2024-01-01 12:00:00'), None],
            'PitOutTime': [None, None, None]
        })
        result = client._filter_valid_laps(df)
        assert len(result) == 2
        assert list(result['LapNumber']) == [1, 3]

    def test_filters_pit_out_laps(self, client):
        """Should filter out laps with pit exit (PitOutTime is not NaN)."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'Deleted': [False, False, False],
            'PitInTime': [None, None, None],
            'PitOutTime': [pd.Timestamp('2024-01-01 12:00:00'), None, None]
        })
        result = client._filter_valid_laps(df)
        assert len(result) == 2
        assert list(result['LapNumber']) == [2, 3]

    def test_filters_combined_invalid_laps(self, client):
        """Should filter deleted laps, pit-in laps, and pit-out laps together."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3, 4, 5],
            'Deleted': [False, True, False, False, False],
            'PitInTime': [None, None, pd.Timestamp('2024-01-01'), None, None],
            'PitOutTime': [pd.Timestamp('2024-01-01'), None, None, None, None]
        })
        result = client._filter_valid_laps(df)
        # Lap 1: pit out, Lap 2: deleted, Lap 3: pit in, Lap 4 & 5: valid
        assert len(result) == 2
        assert list(result['LapNumber']) == [4, 5]

    def test_fallback_when_all_laps_invalid(self, client):
        """Should return original laps when all would be filtered out."""
        df = pd.DataFrame({
            'LapNumber': [1, 2],
            'Deleted': [True, True],
            'PitInTime': [None, None],
            'PitOutTime': [None, None]
        })
        result = client._filter_valid_laps(df)
        # Should fallback to original since all are invalid
        assert len(result) == 2

    def test_handles_none_input(self, client):
        """Should handle None input gracefully."""
        result = client._filter_valid_laps(None)
        assert result is None

    def test_handles_empty_dataframe(self, client):
        """Should handle empty DataFrame gracefully."""
        df = pd.DataFrame()
        result = client._filter_valid_laps(df)
        assert len(result) == 0

    def test_handles_missing_deleted_column(self, client):
        """Should work when Deleted column is missing (older data)."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'PitInTime': [None, None, None],
            'PitOutTime': [None, None, None]
        })
        result = client._filter_valid_laps(df)
        assert len(result) == 3

    def test_handles_missing_pit_columns(self, client):
        """Should work when PitInTime/PitOutTime columns are missing."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'Deleted': [False, True, False]
        })
        result = client._filter_valid_laps(df)
        assert len(result) == 2

    def test_handles_nan_deleted_values(self, client):
        """Should treat NaN Deleted values as valid (older data compatibility)."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'Deleted': [False, np.nan, True],
            'PitInTime': [None, None, None],
            'PitOutTime': [None, None, None]
        })
        result = client._filter_valid_laps(df)
        # Lap 1: valid, Lap 2: NaN treated as valid, Lap 3: deleted
        assert len(result) == 2
        assert list(result['LapNumber']) == [1, 2]

    def test_preserves_dataframe_structure(self, client):
        """Should preserve all columns in the filtered DataFrame."""
        df = pd.DataFrame({
            'LapNumber': [1, 2],
            'Deleted': [False, True],
            'PitInTime': [None, None],
            'PitOutTime': [None, None],
            'LapTime': [90.5, 91.0],
            'Driver': ['VER', 'VER']
        })
        result = client._filter_valid_laps(df)
        assert list(result.columns) == list(df.columns)
        assert result['Driver'].iloc[0] == 'VER'
        assert result['LapTime'].iloc[0] == 90.5

    def test_single_valid_lap_remains(self, client):
        """Should return single valid lap when only one exists."""
        df = pd.DataFrame({
            'LapNumber': [1, 2, 3],
            'Deleted': [True, False, True],
            'PitInTime': [None, None, None],
            'PitOutTime': [None, None, None]
        })
        result = client._filter_valid_laps(df)
        assert len(result) == 1
        assert result['LapNumber'].iloc[0] == 2


class TestFastF1ClientInit:
    """Tests for FastF1Client initialization."""

    def test_client_has_filter_valid_laps_method(self):
        """Verify the _filter_valid_laps method exists."""
        client = FastF1Client()
        assert hasattr(client, '_filter_valid_laps')
        assert callable(client._filter_valid_laps)

    def test_client_has_filter_laps_by_session_part_method(self):
        """Verify the _filter_laps_by_session_part method exists."""
        client = FastF1Client()
        assert hasattr(client, '_filter_laps_by_session_part')
        assert callable(client._filter_laps_by_session_part)
