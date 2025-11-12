"""Driver style clustering using PCA and KMeans."""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple, Any


def cluster_driving_styles(
    driver_telemetry: List[Dict[str, Any]],
    n_clusters: int = 3,
    features: List[str] = ["speed", "throttle", "brake"]
) -> Tuple[np.ndarray, np.ndarray, List[float], Dict[int, str]]:
    """
    Cluster drivers by driving style using PCA + KMeans.
    
    Args:
        driver_telemetry: List of driver telemetry dictionaries
        n_clusters: Number of clusters to create
        features: Features to use for clustering
        
    Returns:
        Tuple of (cluster_labels, pca_projections, explained_variance, cluster_descriptions)
    """
    # Extract feature matrices for each driver
    feature_matrices = []
    driver_names = []
    
    for driver_data in driver_telemetry:
        driver_names.append(driver_data["driver"])
        
        # Extract features from telemetry
        feature_vector = extract_driver_features(
            driver_data["telemetry"],
            features
        )
        feature_matrices.append(feature_vector)
    
    # Convert to numpy array
    X = np.array(feature_matrices)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply PCA for dimensionality reduction and visualization
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # Generate cluster descriptions based on cluster centers
    cluster_descriptions = generate_cluster_descriptions(
        kmeans.cluster_centers_,
        scaler,
        features
    )
    
    return labels, X_pca, pca.explained_variance_ratio_.tolist(), cluster_descriptions


def extract_driver_features(
    telemetry: Dict[str, List[float]],
    features: List[str]
) -> np.ndarray:
    """
    Extract statistical features from driver telemetry.
    
    Args:
        telemetry: Driver telemetry data
        features: Features to extract statistics from
        
    Returns:
        Feature vector with statistical summaries
    """
    feature_stats = []
    
    for feature_name in features:
        if feature_name in telemetry:
            values = np.array(telemetry[feature_name])
            
            # Extract statistical features
            feature_stats.extend([
                np.mean(values),         # Average
                np.std(values),          # Variability
                np.percentile(values, 95),  # Peak (95th percentile)
                np.percentile(values, 5),   # Minimum (5th percentile)
                np.median(values),       # Median
            ])
    
    return np.array(feature_stats)


def generate_cluster_descriptions(
    cluster_centers: np.ndarray,
    scaler: StandardScaler,
    features: List[str]
) -> Dict[int, str]:
    """
    Generate human-readable descriptions for clusters.
    
    Args:
        cluster_centers: KMeans cluster centers
        scaler: StandardScaler used for normalization
        features: Feature names
        
    Returns:
        Dictionary mapping cluster IDs to descriptions
    """
    descriptions = {}
    
    # Inverse transform cluster centers to original scale
    centers_original = scaler.inverse_transform(cluster_centers)
    
    n_stats_per_feature = 5  # mean, std, p95, p5, median
    n_features = len(features)
    
    for cluster_id, center in enumerate(centers_original):
        feature_characteristics = []
        
        for i, feature_name in enumerate(features):
            start_idx = i * n_stats_per_feature
            mean_val = center[start_idx]
            std_val = center[start_idx + 1]
            peak_val = center[start_idx + 2]
            
            # Characterize based on feature values
            if feature_name == "speed":
                if mean_val > 200:
                    feature_characteristics.append("High-speed")
                elif mean_val < 150:
                    feature_characteristics.append("Low-speed")
                else:
                    feature_characteristics.append("Medium-speed")
            
            elif feature_name == "throttle":
                if mean_val > 70:
                    feature_characteristics.append("Aggressive throttle")
                elif mean_val < 50:
                    feature_characteristics.append("Conservative throttle")
            
            elif feature_name == "brake":
                if peak_val > 80:
                    feature_characteristics.append("Hard braking")
                elif mean_val > 20:
                    feature_characteristics.append("Frequent braking")
        
        # Combine characteristics into description
        if feature_characteristics:
            descriptions[cluster_id] = " + ".join(feature_characteristics)
        else:
            descriptions[cluster_id] = f"Cluster {cluster_id}"
    
    return descriptions


def calculate_driver_style_metrics(
    telemetry: Dict[str, List[float]]
) -> Dict[str, float]:
    """
    Calculate driving style metrics from telemetry.
    
    Args:
        telemetry: Driver telemetry data
        
    Returns:
        Dictionary of style metrics
    """
    metrics = {}
    
    if "speed" in telemetry:
        speed = np.array(telemetry["speed"])
        metrics["avg_speed"] = float(np.mean(speed))
        metrics["max_speed"] = float(np.max(speed))
        metrics["speed_variability"] = float(np.std(speed))
    
    if "throttle" in telemetry:
        throttle = np.array(telemetry["throttle"])
        metrics["avg_throttle"] = float(np.mean(throttle))
        metrics["throttle_application"] = float(np.percentile(throttle, 95))
    
    if "brake" in telemetry:
        brake = np.array(telemetry["brake"])
        metrics["avg_brake"] = float(np.mean(brake))
        metrics["max_brake"] = float(np.max(brake))
        # Count braking events
        metrics["braking_frequency"] = float(np.sum(brake > 10) / len(brake))
    
    return metrics

