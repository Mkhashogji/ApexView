#!/usr/bin/env python3
"""
Quick verification that the brake detection fix works.
Tests the exact scenario that was failing: abrupt brake application.
"""

import numpy as np
from services.corner_analysis import detect_braking_zone, BRAKE_THRESHOLD_PERCENT, BRAKE_GRADIENT_THRESHOLD

def test_abrupt_braking():
    """
    Test detection when brake goes from 0% to 100% instantly.
    This is the exact scenario that was broken before the fix.
    
    Before fix: Would return MEDIUM (gradient checked at wrong index)
    After fix: Should return HIGH (gradient checked leading into brake point)
    """
    # Create telemetry with abrupt braking at 100m
    distance = np.linspace(0, 500, 100)  # 5m resolution
    brake = np.zeros(100)
    
    # Abrupt brake: 0% -> 100% at index 20 (distance ~100m)
    brake[20:50] = 100.0  # Full brake from 100m to 250m
    
    # Test detection with apex at 300m
    # Search zone: 300-250=50m to 300-50=250m
    # This covers the braking event at 100m
    brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=300)
    
    print("=" * 60)
    print("BRAKE DETECTION FIX VERIFICATION")
    print("=" * 60)
    print(f"\nTest: Abrupt braking (0% -> 100% at ~100m)")
    print(f"  Apex distance: 300m")
    print(f"  Search zone: 50m to 250m")
    print(f"  Detected brake point: {brake_dist:.0f}m")
    print(f"  Confidence: {confidence}")
    
    # Calculate what the gradient would be
    dist_diff = distance[20] - distance[19]  # ~5m
    brake_diff = brake[20] - brake[19]  # 100-0 = 100
    expected_gradient = (brake_diff / dist_diff) * 10  # ~200 %/10m
    print(f"\n  Expected gradient at brake onset: {expected_gradient:.1f} %/10m")
    print(f"  Gradient threshold: {BRAKE_GRADIENT_THRESHOLD} %/10m")
    
    assert confidence == "high", f"Expected HIGH confidence, got {confidence}"
    assert 95 <= brake_dist <= 105, f"Expected brake at ~100m, got {brake_dist}m"
    
    print("\n✅ TEST PASSED: Abrupt braking detected with HIGH confidence")
    return True


def test_gradual_braking():
    """
    Test that gradual braking (low gradient) still returns MEDIUM.
    """
    distance = np.linspace(0, 500, 100)
    # Very gradual brake increase over 200m
    brake = np.zeros(100)
    brake[10:60] = np.linspace(0, 30, 50)  # Slow ramp from 50m to 300m
    
    brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=350)
    
    print("\nTest: Gradual braking (slow ramp)")
    print(f"  Detected confidence: {confidence}")
    
    # Gradual braking should be LOW or MEDIUM
    assert confidence in ["low", "medium"], f"Expected LOW/MEDIUM, got {confidence}"
    print("✅ TEST PASSED: Gradual braking detected with appropriate confidence")
    return True


if __name__ == "__main__":
    test_abrupt_braking()
    test_gradual_braking()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - Brake detection fix verified!")
    print("=" * 60)
