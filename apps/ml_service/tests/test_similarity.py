"""Tests for lap similarity calculations."""
import pytest
import numpy as np
from services.similarity import (
    compute_lap_similarity,
    align_telemetry_arrays,
    extract_telemetry_features
)


def test_align_telemetry_arrays():
    """Test telemetry array alignment."""
    distance1 = [0, 100, 200, 300]
    values1 = [50, 100, 150, 200]
    distance2 = [0, 150, 300]
    values2 = [50, 125, 200]
    
    aligned1, aligned2 = align_telemetry_arrays(
        distance1, values1, distance2, values2, num_points=10
    )
    
    assert len(aligned1) == 10
    assert len(aligned2) == 10
    assert aligned1[0] == pytest.approx(50, abs=1)
    assert aligned2[0] == pytest.approx(50, abs=1)


def test_compute_lap_similarity_identical():
    """Test similarity between identical laps."""
    lap_data = {
        "distance": [0, 100, 200, 300],
        "speed": [50, 100, 150, 200],
        "throttle": [20, 40, 60, 80],
        "brake": [0, 10, 20, 10],
    }
    
    similarity, feature_scores = compute_lap_similarity(
        lap_data, lap_data, features=["speed", "throttle", "brake"]
    )
    
    assert similarity == pytest.approx(1.0, abs=0.01)
    assert all(score > 0.99 for score in feature_scores.values())


def test_compute_lap_similarity_different():
    """Test similarity between different laps."""
    lap1 = {
        "distance": [0, 100, 200, 300],
        "speed": [50, 100, 150, 200],
        "throttle": [20, 40, 60, 80],
        "brake": [0, 10, 20, 10],
    }
    lap2 = {
        "distance": [0, 100, 200, 300],
        "speed": [60, 110, 160, 210],
        "throttle": [30, 50, 70, 90],
        "brake": [5, 15, 25, 15],
    }
    
    similarity, feature_scores = compute_lap_similarity(
        lap1, lap2, features=["speed", "throttle", "brake"]
    )
    
    assert 0.8 < similarity < 1.0  # Similar but not identical
    assert all(0.8 < score < 1.0 for score in feature_scores.values())


def test_extract_telemetry_features():
    """Test feature extraction."""
    telemetry = {
        "distance": [0, 100, 200],
        "speed": [100, 200, 300],
        "throttle": [50, 75, 100],
    }
    
    features = extract_telemetry_features(telemetry, ["speed", "throttle"])
    
    assert len(features) > 0
    assert np.all((features >= 0) & (features <= 1))  # Normalized

