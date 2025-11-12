"""Lap similarity calculation using cosine similarity."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple


def align_telemetry_arrays(
    distance1: List[float],
    values1: List[float],
    distance2: List[float],
    values2: List[float],
    num_points: int = 1000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align two telemetry arrays to common distance points using interpolation.
    
    Args:
        distance1: Distance array for first lap
        values1: Value array for first lap
        distance2: Distance array for second lap
        values2: Value array for second lap
        num_points: Number of interpolation points
        
    Returns:
        Tuple of aligned value arrays
    """
    # Find common distance range
    min_dist = max(min(distance1), min(distance2))
    max_dist = min(max(distance1), max(distance2))
    
    # Create common distance points
    common_distance = np.linspace(min_dist, max_dist, num_points)
    
    # Interpolate values to common distance
    values1_aligned = np.interp(common_distance, distance1, values1)
    values2_aligned = np.interp(common_distance, distance2, values2)
    
    return values1_aligned, values2_aligned


def compute_lap_similarity(
    lap1_data: Dict[str, List[float]],
    lap2_data: Dict[str, List[float]],
    features: List[str] = ["speed", "throttle", "brake"]
) -> Tuple[float, Dict[str, float]]:
    """
    Compute cosine similarity between two laps over distance-aligned telemetry.
    
    Args:
        lap1_data: First lap telemetry data
        lap2_data: Second lap telemetry data
        features: List of features to include in similarity
        
    Returns:
        Tuple of (overall_similarity, feature_similarities)
    """
    feature_similarities = {}
    feature_vectors_1 = []
    feature_vectors_2 = []
    
    # Extract distance arrays
    distance1 = lap1_data["distance"]
    distance2 = lap2_data["distance"]
    
    # Compute similarity for each feature
    for feature in features:
        if feature in lap1_data and feature in lap2_data:
            # Align the feature arrays
            aligned_1, aligned_2 = align_telemetry_arrays(
                distance1, lap1_data[feature],
                distance2, lap2_data[feature]
            )
            
            # Calculate feature-specific similarity
            feature_sim = cosine_similarity([aligned_1], [aligned_2])[0][0]
            feature_similarities[feature] = float(feature_sim)
            
            # Add to combined feature vectors
            feature_vectors_1.append(aligned_1)
            feature_vectors_2.append(aligned_2)
    
    # Compute overall similarity across all features
    if feature_vectors_1 and feature_vectors_2:
        # Concatenate all feature vectors
        combined_vector_1 = np.concatenate(feature_vectors_1)
        combined_vector_2 = np.concatenate(feature_vectors_2)
        
        # Compute cosine similarity
        overall_similarity = cosine_similarity(
            [combined_vector_1], 
            [combined_vector_2]
        )[0][0]
    else:
        overall_similarity = 0.0
    
    return float(overall_similarity), feature_similarities


def extract_telemetry_features(
    telemetry_data: Dict[str, List[float]],
    features: List[str] = ["speed", "throttle", "brake"]
) -> np.ndarray:
    """
    Extract and concatenate feature vectors from telemetry data.
    
    Args:
        telemetry_data: Telemetry data dictionary
        features: Features to extract
        
    Returns:
        Feature vector as numpy array
    """
    feature_vectors = []
    
    for feature in features:
        if feature in telemetry_data:
            # Normalize features to similar scales
            values = np.array(telemetry_data[feature])
            
            # Feature-specific normalization
            if feature == "speed":
                # Speed typically 0-350 km/h
                normalized = values / 350.0
            elif feature in ["throttle", "brake"]:
                # Already 0-100, normalize to 0-1
                normalized = values / 100.0
            elif feature == "gear":
                # Gears 1-8, normalize
                normalized = values / 8.0
            elif feature == "rpm":
                # RPM typically 0-15000
                normalized = values / 15000.0
            else:
                # Generic normalization
                if values.max() > 0:
                    normalized = values / values.max()
                else:
                    normalized = values
            
            feature_vectors.append(normalized)
    
    if feature_vectors:
        return np.concatenate(feature_vectors)
    else:
        return np.array([])

