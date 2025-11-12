"""Pydantic schemas for ML service requests and responses."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TelemetryData(BaseModel):
    """Telemetry data for a single lap."""
    distance: List[float] = Field(..., description="Distance array (meters)")
    speed: List[float] = Field(..., description="Speed array (km/h)")
    throttle: List[float] = Field(..., description="Throttle percentage (0-100)")
    brake: List[float] = Field(..., description="Brake percentage (0-100)")
    gear: Optional[List[int]] = Field(None, description="Gear array")
    rpm: Optional[List[int]] = Field(None, description="RPM array")
    drs: Optional[List[int]] = Field(None, description="DRS status array")


class LapSimilarityRequest(BaseModel):
    """Request for lap similarity calculation."""
    lap1: TelemetryData = Field(..., description="First lap telemetry")
    lap2: TelemetryData = Field(..., description="Second lap telemetry")
    features: List[str] = Field(
        default=["speed", "throttle", "brake"],
        description="Features to use for similarity calculation"
    )


class LapSimilarityResponse(BaseModel):
    """Response for lap similarity calculation."""
    similarity: float = Field(..., description="Cosine similarity score (0-1)")
    feature_scores: Dict[str, float] = Field(
        ..., 
        description="Individual similarity scores per feature"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the calculation"
    )


class DriverTelemetryInput(BaseModel):
    """Telemetry data for a single driver."""
    driver: str = Field(..., description="Driver abbreviation (e.g., VER, HAM)")
    telemetry: TelemetryData = Field(..., description="Driver's telemetry data")


class ClusteringRequest(BaseModel):
    """Request for driver style clustering."""
    telemetry_data: List[DriverTelemetryInput] = Field(
        ..., 
        description="List of driver telemetry data"
    )
    n_clusters: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Number of clusters (2-10)"
    )
    features: List[str] = Field(
        default=["speed", "throttle", "brake"],
        description="Features to use for clustering"
    )


class DriverCluster(BaseModel):
    """Driver cluster assignment."""
    driver: str = Field(..., description="Driver abbreviation")
    cluster: int = Field(..., description="Assigned cluster ID")
    pca_x: float = Field(..., description="PCA component 1 projection")
    pca_y: float = Field(..., description="PCA component 2 projection")


class ClusteringResponse(BaseModel):
    """Response for driver clustering."""
    clusters: List[DriverCluster] = Field(
        ..., 
        description="Driver cluster assignments with PCA projections"
    )
    cluster_descriptions: Dict[int, str] = Field(
        ..., 
        description="Human-readable cluster descriptions"
    )
    explained_variance: List[float] = Field(
        ..., 
        description="Explained variance ratio for PCA components"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    service: str = Field(..., description="Service name")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

