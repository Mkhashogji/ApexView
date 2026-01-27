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


# =============================================================================
# Phase 2: Scaled Delta Schemas
# =============================================================================

class ScaledDeltaRequest(BaseModel):
    """Request for scaled delta calculation."""
    session_id: str = Field(
        ...,
        description="Session identifier (e.g., '2025_24_Qualifying')"
    )
    reference_driver: str = Field(
        ...,
        description="Reference driver code (3 letters, e.g., 'NOR')"
    )
    compare_drivers: List[str] = Field(
        ...,
        description="List of driver codes to compare against reference"
    )
    session_part: Optional[str] = Field(
        None,
        description="Qualifying session part filter (Q1, Q2, or Q3)"
    )


class ScaledDeltaDriverResult(BaseModel):
    """Result for a single driver comparison with scaling metadata."""
    reference_driver: str = Field(..., description="Reference driver code")
    compare_driver: str = Field(..., description="Comparison driver code")

    # Delta arrays (distance-indexed)
    distance: List[float] = Field(..., description="Distance array in meters")
    delta: List[float] = Field(
        ...,
        description="Scaled delta in seconds (positive = compare driver slower)"
    )
    raw_delta: List[float] = Field(
        ...,
        description="Original telemetry-derived delta before scaling"
    )

    # Scaling metadata
    official_gap: float = Field(
        ...,
        description="Official timing gap in seconds (ground truth from FIA)"
    )
    telemetry_gap: float = Field(
        ...,
        description="Raw telemetry-calculated gap in seconds"
    )
    scaling_factor: float = Field(
        ...,
        description="Multiplier applied: official_gap / telemetry_gap"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) based on scaling factor deviation"
    )


class ScaledDeltaResponse(BaseModel):
    """Complete response for scaled delta endpoint."""
    session_id: str = Field(..., description="Session that was analyzed")
    reference_driver: str = Field(..., description="Reference driver used")
    results: List[ScaledDeltaDriverResult] = Field(
        ...,
        description="Scaled delta results for each comparison driver"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (session_part, errors, etc.)"
    )


# =============================================================================
# Phase 3: Corner Analysis Schemas
# =============================================================================

class CornerInput(BaseModel):
    """Input definition for a corner to analyze."""
    corner_number: int = Field(..., ge=1, description="Sequential corner number (1-indexed)")
    name: Optional[str] = Field(None, description="Corner name (e.g., 'Turn 1', 'Parabolica')")
    apex_distance: float = Field(
        ...,
        ge=0,
        description="Distance from start/finish to corner apex (meters)"
    )
    corner_type: str = Field(..., description="Corner direction: 'left' or 'right'")


class CornerResultSchema(BaseModel):
    """Result of analyzing a single corner."""
    corner_number: int = Field(..., description="Sequential corner number")
    name: Optional[str] = Field(None, description="Corner name if provided")
    apex_distance: float = Field(..., description="Distance to corner apex (meters)")
    brake_distance: float = Field(
        ...,
        description="Detected braking start distance (meters)"
    )
    zone_start: float = Field(..., description="Analysis zone start distance (meters)")
    zone_end: float = Field(..., description="Analysis zone end distance (meters)")
    delta_change: float = Field(
        ...,
        description="Time gained/lost in seconds (positive = compare driver slower)"
    )
    cause: str = Field(
        ...,
        description="Primary cause: 'braking', 'apex', 'exit', 'multiple', or 'unknown'"
    )
    confidence: str = Field(
        ...,
        description="Confidence level: 'high', 'medium', or 'low'"
    )


# =============================================================================
# Sector Validation Schemas (V2 Enhancement)
# =============================================================================

class SectorValidationSchema(BaseModel):
    """Validation result for a single sector."""
    sector_number: int = Field(..., ge=1, le=3, description="Sector number (1-3)")
    corner_delta_sum: float = Field(
        ...,
        description="Sum of corner deltas in this sector (seconds)"
    )
    official_delta: float = Field(
        ...,
        description="Official sector time delta: comp - ref (seconds)"
    )
    difference: float = Field(
        ...,
        description="Discrepancy: corner_sum - official_delta (seconds)"
    )
    is_valid: bool = Field(
        ...,
        description="Whether difference is within tolerance threshold"
    )
    corners_in_sector: int = Field(
        default=0,
        ge=0,
        description="Number of corners contributing to this sector"
    )


class ValidationReportSchema(BaseModel):
    """Complete sector validation report for corner analysis."""
    sector_validations: List[SectorValidationSchema] = Field(
        ...,
        description="Validation results for each of the 3 sectors"
    )
    overall_valid: bool = Field(
        ...,
        description="True if all sectors are within tolerance"
    )
    confidence_adjustment: float = Field(
        ...,
        ge=0.5,
        le=1.0,
        description="Multiplier based on validation (0.5 if 0/3 valid, 1.0 if 3/3 valid)"
    )
    total_corner_delta: float = Field(
        ...,
        description="Sum of all corner deltas (seconds)"
    )
    official_lap_delta: float = Field(
        ...,
        description="Official lap time delta: comp - ref (seconds)"
    )


class CornerAnalysisRequest(BaseModel):
    """Request for corner analysis."""
    session_id: str = Field(
        ...,
        description="Session identifier (e.g., '2025_24_Qualifying')"
    )
    reference_driver: str = Field(
        ...,
        description="Reference driver code (3 letters, e.g., 'NOR')"
    )
    compare_drivers: List[str] = Field(
        ...,
        description="List of driver codes to compare against reference"
    )
    corners: List[CornerInput] = Field(
        ...,
        description="List of corners to analyze"
    )
    session_part: Optional[str] = Field(
        None,
        description="Qualifying session part filter (Q1, Q2, or Q3)"
    )
    circuit_id: Optional[str] = Field(
        None,
        description="Circuit identifier for v2 config lookup (e.g., 'monza', 'monaco')"
    )
    sector_boundaries: Optional[List[float]] = Field(
        None,
        description="Sector boundary distances [s1_end, s2_end] in meters for validation"
    )


class CornerAnalysisDriverResult(BaseModel):
    """Corner analysis result for a single driver comparison."""
    compare_driver: str = Field(..., description="Comparison driver code")
    corner_results: List[CornerResultSchema] = Field(
        ...,
        description="Analysis results for each corner"
    )
    total_delta_change: float = Field(
        ...,
        description="Sum of all corner delta changes (seconds)"
    )
    corners_gaining: int = Field(
        ...,
        ge=0,
        description="Count of corners where compare driver gained time"
    )
    corners_losing: int = Field(
        ...,
        ge=0,
        description="Count of corners where compare driver lost time"
    )
    # V2 additions
    validation: Optional[ValidationReportSchema] = Field(
        None,
        description="Sector validation report (if sector times and boundaries provided)"
    )
    analysis_version: str = Field(
        default="v1",
        description="Analysis version used: 'v1' or 'v2'"
    )


class CornerAnalysisResponse(BaseModel):
    """Complete response for corner analysis endpoint."""
    session_id: str = Field(..., description="Session that was analyzed")
    reference_driver: str = Field(..., description="Reference driver used")
    results: List[CornerAnalysisDriverResult] = Field(
        ...,
        description="Corner analysis results for each comparison driver"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (drivers_analyzed, corners_analyzed, errors)"
    )


# =============================================================================
# Phase 4: Technique Profiling Schemas
# =============================================================================

class TechniqueDimensionSchema(BaseModel):
    """Single dimension of driving technique (braking, apex, exit, or consistency)."""
    level: str = Field(
        ...,
        description="Classification level: 'strong', 'neutral', or 'weak'"
    )
    descriptor: str = Field(
        ...,
        description="Human-readable description (e.g., 'Strong under braking')"
    )
    percentile: float = Field(
        ...,
        ge=0,
        le=100,
        description="Session percentile (0-100, lower = better for performance)"
    )
    raw_value: float = Field(
        ...,
        description="Actual delta sum in seconds for this dimension"
    )
    corner_count: int = Field(
        ...,
        ge=0,
        description="Number of corners contributing to this dimension"
    )
    avg_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Average confidence of contributing corners (0-1)"
    )


class TechniqueProfileSchema(BaseModel):
    """Complete technique profile for a driver."""
    driver: str = Field(..., description="Driver code (e.g., 'PIA')")
    reference_driver: str = Field(
        ...,
        description="Reference driver this profile is compared against"
    )
    braking: TechniqueDimensionSchema = Field(
        ...,
        description="Braking technique dimension"
    )
    apex: TechniqueDimensionSchema = Field(
        ...,
        description="Apex/mid-corner technique dimension"
    )
    exit: TechniqueDimensionSchema = Field(
        ...,
        description="Exit/traction technique dimension"
    )
    consistency: TechniqueDimensionSchema = Field(
        ...,
        description="Consistency across all corners"
    )
    top_gaining_corners: List[str] = Field(
        default_factory=list,
        description="Top 3 corners where driver gained time (names/numbers)"
    )
    top_losing_corners: List[str] = Field(
        default_factory=list,
        description="Top 3 corners where driver lost time (names/numbers)"
    )
    style_summary: str = Field(
        ...,
        description="One-line style characterization (e.g., 'Conservative entry, aggressive exit')"
    )
    overall_confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Overall profile confidence (0-1)"
    )
    total_corners_analyzed: int = Field(
        ...,
        ge=0,
        description="Total number of corners in the analysis"
    )


class SessionPercentilesSchema(BaseModel):
    """Session percentile boundaries for technique classification."""
    braking_p30: float = Field(
        ...,
        description="Braking 30th percentile threshold (STRONG boundary)"
    )
    braking_p70: float = Field(
        ...,
        description="Braking 70th percentile threshold (WEAK boundary)"
    )
    apex_p30: float = Field(..., description="Apex 30th percentile threshold")
    apex_p70: float = Field(..., description="Apex 70th percentile threshold")
    exit_p30: float = Field(..., description="Exit 30th percentile threshold")
    exit_p70: float = Field(..., description="Exit 70th percentile threshold")
    consistency_p30: float = Field(
        ...,
        description="Consistency 30th percentile threshold"
    )
    consistency_p70: float = Field(
        ...,
        description="Consistency 70th percentile threshold"
    )
    driver_count: int = Field(
        ...,
        ge=1,
        description="Number of drivers used to calculate percentiles"
    )


class TechniqueProfilingRequest(BaseModel):
    """Request for technique profiling analysis."""
    session_id: str = Field(
        ...,
        description="Session identifier (e.g., '2025_8_Qualifying')"
    )
    reference_driver: str = Field(
        ...,
        description="Reference driver code (3 letters, e.g., 'NOR')"
    )
    compare_drivers: List[str] = Field(
        ...,
        description="List of driver codes to profile against reference"
    )
    corners: List[CornerInput] = Field(
        ...,
        description="List of corners to analyze (from track intelligence)"
    )
    session_part: Optional[str] = Field(
        None,
        description="Qualifying session part filter (Q1, Q2, or Q3)"
    )
    weight_by_confidence: bool = Field(
        True,
        description="Whether to weight aggregations by corner confidence"
    )
    circuit_id: Optional[str] = Field(
        None,
        description="Circuit identifier for v2 config lookup (e.g., 'monza', 'monaco')"
    )


class TechniqueProfilingResponse(BaseModel):
    """Complete response for technique profiling endpoint."""
    session_id: str = Field(..., description="Session that was analyzed")
    reference_driver: str = Field(..., description="Reference driver used")
    profiles: List[TechniqueProfileSchema] = Field(
        ...,
        description="Technique profiles for each comparison driver"
    )
    session_percentiles: SessionPercentilesSchema = Field(
        ...,
        description="Session-wide percentile boundaries used for classification"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (drivers_analyzed, drivers_failed, errors)"
    )


# =============================================================================
# Phase 5: Natural Language Insight Schemas
# =============================================================================

class CornerInsightSchema(BaseModel):
    """Insight for a single corner."""
    corner_name: str = Field(..., description="Corner name or number (e.g., 'Turn 3')")
    delta_ms: int = Field(..., description="Delta change in milliseconds")
    direction: str = Field(..., description="'gaining' or 'losing'")
    cause: str = Field(
        ...,
        description="Primary cause (braking/apex/exit/multiple/unknown)"
    )
    text: str = Field(..., description="Human-readable insight text")
    confidence: str = Field(..., description="Confidence level (high/medium/low)")


class DimensionInsightSchema(BaseModel):
    """Insight for a technique dimension."""
    dimension: str = Field(
        ...,
        description="Dimension name (braking/apex/exit/consistency)"
    )
    level: str = Field(..., description="Classification level (strong/neutral/weak)")
    percentile: float = Field(
        ...,
        ge=0,
        le=100,
        description="Session percentile (0-100)"
    )
    text: str = Field(..., description="Human-readable insight text")
    raw_value_ms: int = Field(..., description="Raw delta value in milliseconds")
    corner_count: int = Field(
        default=0,
        ge=0,
        description="Number of corners in this dimension"
    )


class NaturalLanguageInsightSchema(BaseModel):
    """Complete natural language insight for a driver."""
    driver: str = Field(..., description="Driver code being analyzed")
    reference_driver: str = Field(..., description="Reference driver for comparison")
    mode: str = Field(..., description="Insight mode: 'engineer' or 'driver'")
    confidence_level: str = Field(
        ...,
        description="Overall confidence: 'high', 'medium', 'low', or 'insufficient'"
    )
    summary: str = Field(..., description="Main summary paragraph")
    dimension_insights: List[DimensionInsightSchema] = Field(
        default_factory=list,
        description="Insights for each technique dimension"
    )
    corner_insights: List[CornerInsightSchema] = Field(
        default_factory=list,
        description="Top corner-specific insights"
    )
    opportunity_text: str = Field(
        default="",
        description="Suggested areas for improvement"
    )
    hedging_prefix: str = Field(
        default="",
        description="Confidence qualifier prefix (e.g., 'Analysis suggests: ')"
    )
    total_corners: int = Field(..., ge=0, description="Number of corners analyzed")
    session_context: Dict[str, str] = Field(
        default_factory=dict,
        description="Optional circuit/session context"
    )
    style_summary: str = Field(
        default="",
        description="Style summary from Phase 4"
    )


class InsightGenerationRequest(BaseModel):
    """Request for insight generation endpoint."""
    session_id: str = Field(
        ...,
        description="Session identifier (e.g., '2025_8_Qualifying')"
    )
    reference_driver: str = Field(
        ...,
        description="Reference driver code (3 letters, e.g., 'NOR')"
    )
    compare_drivers: List[str] = Field(
        ...,
        description="List of driver codes to generate insights for"
    )
    corners: List[CornerInput] = Field(
        ...,
        description="List of corners to analyze"
    )
    mode: str = Field(
        default="engineer",
        description="Insight mode: 'engineer' (metrics-heavy) or 'driver' (actionable)"
    )
    session_part: Optional[str] = Field(
        None,
        description="Qualifying session part filter (Q1, Q2, or Q3)"
    )
    circuit_name: Optional[str] = Field(
        None,
        description="Circuit name for context (e.g., 'Monaco')"
    )


class InsightGenerationResponse(BaseModel):
    """Response for insight generation endpoint."""
    session_id: str = Field(..., description="Session that was analyzed")
    reference_driver: str = Field(..., description="Reference driver used")
    insights: List[NaturalLanguageInsightSchema] = Field(
        ...,
        description="Generated insights for each driver"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (mode, drivers_processed, errors)"
    )


# =============================================================================
# Phase 6: Performance Insights Orchestrator Schemas
# =============================================================================

class PerformanceInsightsRequest(BaseModel):
    """
    Request for unified performance insights (orchestrates Phases 2-5).

    This is the primary endpoint for frontend consumption, providing
    complete analysis in a single API call.
    """
    session_id: str = Field(
        ...,
        description="Session identifier (e.g., '2025_24_Qualifying')"
    )
    reference_driver: str = Field(
        ...,
        description="Reference driver code (3 letters, e.g., 'NOR')"
    )
    compare_drivers: List[str] = Field(
        ...,
        description="List of driver codes to compare against reference"
    )
    corners: List[CornerInput] = Field(
        ...,
        description="List of corners to analyze (from track intelligence)"
    )
    mode: str = Field(
        default="engineer",
        description="Insight mode: 'engineer' (metrics-heavy) or 'driver' (actionable)"
    )
    session_part: Optional[str] = Field(
        None,
        description="Qualifying session part filter (Q1, Q2, or Q3)"
    )
    circuit_name: Optional[str] = Field(
        None,
        description="Circuit name for context (e.g., 'Bahrain International Circuit')"
    )
    include_telemetry: bool = Field(
        default=True,
        description="Whether to include full delta arrays in response"
    )


class DriverPerformanceResult(BaseModel):
    """
    Complete performance analysis for a single driver comparison.

    Aggregates results from all phases into a single driver object.
    """
    driver: str = Field(..., description="Driver code being analyzed")

    # Phase 2: Scaled Delta
    official_gap: float = Field(
        ...,
        description="Official timing gap in seconds (from FIA)"
    )
    scaling_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Delta scaling confidence (0-1)"
    )
    delta: Optional[List[float]] = Field(
        None,
        description="Scaled delta array (if include_telemetry=True)"
    )
    distance: Optional[List[float]] = Field(
        None,
        description="Distance array (if include_telemetry=True)"
    )

    # Phase 3: Corner Analysis Summary
    corners_gaining: int = Field(
        ...,
        ge=0,
        description="Count of corners where driver gained time"
    )
    corners_losing: int = Field(
        ...,
        ge=0,
        description="Count of corners where driver lost time"
    )
    total_corner_delta: float = Field(
        ...,
        description="Sum of all corner deltas in seconds"
    )
    corner_results: List[CornerResultSchema] = Field(
        default_factory=list,
        description="Detailed results for each corner"
    )

    # Phase 4: Technique Profile
    technique_profile: Optional[TechniqueProfileSchema] = Field(
        None,
        description="Complete technique profile for the driver"
    )

    # Phase 5: Natural Language Insight
    insight: Optional[NaturalLanguageInsightSchema] = Field(
        None,
        description="Generated natural language insight"
    )


class PhaseTimingInfo(BaseModel):
    """Timing information for a single phase execution."""
    phase: str = Field(..., description="Phase name (e.g., 'delta', 'corner')")
    duration_ms: int = Field(..., ge=0, description="Execution time in milliseconds")
    success: bool = Field(..., description="Whether phase completed successfully")
    error: Optional[str] = Field(None, description="Error message if failed")


class PerformanceInsightsResponse(BaseModel):
    """
    Complete response from performance insights orchestrator.

    Contains all analysis results for all requested drivers,
    plus session-wide metadata and timing information.
    """
    session_id: str = Field(..., description="Session that was analyzed")
    reference_driver: str = Field(..., description="Reference driver used")
    circuit_name: Optional[str] = Field(
        None,
        description="Circuit name if provided"
    )
    mode: str = Field(..., description="Insight mode used")

    # Results for each driver
    results: List[DriverPerformanceResult] = Field(
        ...,
        description="Complete performance results for each comparison driver"
    )

    # Session-wide context from Phase 4
    session_percentiles: Optional[SessionPercentilesSchema] = Field(
        None,
        description="Session percentile boundaries for technique classification"
    )

    # Orchestration metadata
    total_drivers_requested: int = Field(
        ...,
        ge=0,
        description="Number of drivers requested"
    )
    total_drivers_processed: int = Field(
        ...,
        ge=0,
        description="Number of drivers successfully processed"
    )
    total_corners: int = Field(
        ...,
        ge=0,
        description="Number of corners in the analysis"
    )

    # Timing breakdown
    phase_timing: List[PhaseTimingInfo] = Field(
        default_factory=list,
        description="Execution timing for each phase"
    )
    total_duration_ms: int = Field(
        ...,
        ge=0,
        description="Total orchestration time in milliseconds"
    )

    # Error tracking
    errors: List[str] = Field(
        default_factory=list,
        description="Any errors encountered during processing"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings generated during processing"
    )
