import numpy as np
import pandas as pd
from typing import List, Tuple, Optional


def calculate_delta(
    reference_telemetry: pd.DataFrame,
    compare_telemetry: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate time delta between two telemetry traces.
    
    Args:
        reference_telemetry: Reference driver telemetry with 'Distance' and 'Speed'
        compare_telemetry: Comparison driver telemetry with 'Distance' and 'Speed'
    
    Returns:
        Tuple of (distance array, delta array) in seconds
    """
    # Get common distance range
    min_dist = max(reference_telemetry['Distance'].min(), compare_telemetry['Distance'].min())
    max_dist = min(reference_telemetry['Distance'].max(), compare_telemetry['Distance'].max())
    
    # Create common distance points
    common_distance = np.linspace(min_dist, max_dist, 1000)
    
    # Interpolate speeds to common distance points
    ref_speed = np.interp(
        common_distance, 
        reference_telemetry['Distance'].values, 
        reference_telemetry['Speed'].values
    )
    comp_speed = np.interp(
        common_distance,
        compare_telemetry['Distance'].values,
        compare_telemetry['Speed'].values
    )
    
    # Calculate time at each point (distance / speed, converting km/h to m/s)
    distance_deltas = np.diff(common_distance, prepend=common_distance[0])
    ref_times = np.cumsum(distance_deltas / (ref_speed / 3.6))
    comp_times = np.cumsum(distance_deltas / (comp_speed / 3.6))
    
    # Delta is comparison time minus reference time
    delta = comp_times - ref_times
    
    return common_distance, delta


def aggregate_sector_times(laps: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate sector times from lap data.
    
    Args:
        laps: DataFrame with lap and sector information
    
    Returns:
        Aggregated sector statistics
    """
    # TODO: Group by sector, calculate min/max/mean
    pass


def calculate_tyre_degradation(
    laps: pd.DataFrame, compound: str
) -> pd.DataFrame:
    """
    Calculate tyre degradation rate for a compound.
    
    Args:
        laps: Lap data with tyre information
        compound: Tyre compound name
    
    Returns:
        Degradation statistics per stint
    """
    # TODO: Filter by compound, calculate pace loss over stint age
    pass


def detect_outliers(lap_times: List[float], threshold: float = 3.0) -> List[bool]:
    """
    Detect outlier laps using standard deviation.
    
    Args:
        lap_times: List of lap times
        threshold: Number of standard deviations for outlier
    
    Returns:
        Boolean list indicating outliers
    """
    times = np.array(lap_times)
    mean = np.mean(times)
    std = np.std(times)
    return np.abs(times - mean) > (threshold * std)


def downsample_telemetry(
    distance: np.ndarray,
    *channels: np.ndarray,
    max_points: int = 1000
) -> Tuple[np.ndarray, ...]:
    """
    Downsample telemetry data to reduce size while preserving shape.
    
    Args:
        distance: Distance array
        *channels: Variable number of telemetry channels (speed, throttle, etc.)
        max_points: Maximum number of points to keep
    
    Returns:
        Tuple of downsampled arrays (distance, *channels)
    """
    if len(distance) <= max_points:
        return (distance, *channels)
    
    # Use linear interpolation to downsample
    indices = np.linspace(0, len(distance) - 1, max_points, dtype=int)
    
    downsampled = [distance[indices]]
    for channel in channels:
        downsampled.append(channel[indices])
    
    return tuple(downsampled)


def resample_telemetry(
    telemetry: pd.DataFrame,
    target_distance: Optional[np.ndarray] = None,
    num_points: int = 1000
) -> pd.DataFrame:
    """
    Resample telemetry to a uniform distance grid.
    
    Args:
        telemetry: Telemetry DataFrame with Distance column
        target_distance: Target distance points (if None, creates uniform grid)
        num_points: Number of points if creating uniform grid
    
    Returns:
        Resampled telemetry DataFrame
    """
    if target_distance is None:
        target_distance = np.linspace(
            telemetry['Distance'].min(),
            telemetry['Distance'].max(),
            num_points
        )
    
    resampled = pd.DataFrame({'Distance': target_distance})
    
    # Interpolate each column
    for col in telemetry.columns:
        if col != 'Distance':
            resampled[col] = np.interp(
                target_distance,
                telemetry['Distance'].values,
                telemetry[col].values
            )
    
    return resampled

