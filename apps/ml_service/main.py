"""
F1 ML Service - FastAPI microservice for machine learning features.

Provides endpoints for:
- Lap similarity calculation (cosine similarity)
- Driver style clustering (PCA + KMeans)
- Scaled delta analysis (Phase 2)
"""
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import __init__ as ml_service
from core.logging_config import setup_logging, get_logger

# Initialize structured logging
setup_logging(level=logging.INFO)
logger = get_logger("main")
from models.schemas import (
    LapSimilarityRequest,
    LapSimilarityResponse,
    ClusteringRequest,
    ClusteringResponse,
    HealthResponse,
    ErrorResponse,
    DriverCluster,
    ScaledDeltaRequest,
    ScaledDeltaResponse,
    ScaledDeltaDriverResult,
    CornerAnalysisRequest,
    CornerAnalysisResponse,
    CornerAnalysisDriverResult,
    CornerResultSchema,
    # V2 Sector Validation
    SectorValidationSchema,
    ValidationReportSchema,
    # Phase 4: Technique Profiling
    TechniqueProfilingRequest,
    TechniqueProfilingResponse,
    TechniqueProfileSchema,
    TechniqueDimensionSchema,
    SessionPercentilesSchema,
    # Phase 5: Natural Language Insights
    InsightGenerationRequest,
    InsightGenerationResponse,
    NaturalLanguageInsightSchema,
    DimensionInsightSchema,
    CornerInsightSchema,
    # Phase 6: Performance Insights Orchestrator
    PerformanceInsightsRequest,
    PerformanceInsightsResponse,
    DriverPerformanceResult,
    PhaseTimingInfo,
    # 5th Dimension: Lap Breakdown
    LapBreakdownSchema,
    StraightSegmentSchema,
)
from services.similarity import compute_lap_similarity
from services.clustering import cluster_driving_styles
from services.delta_analysis import calculate_scaled_delta, DeltaResult
from services.corner_analysis import (
    analyze_corners,
    analyze_corners_v2,
    validate_against_sectors,
    CornerInput as CACornerInput,
    CornerResult,
    CornerAnalysisResult,
)
from services.technique_profiling import (
    profile_drivers,
    TechniqueProfile,
    TechniqueDimension,
    SessionPercentiles,
)
from services.insight_generation import (
    generate_insights,
    generate_insights_batch,
    InsightMode,
    NaturalLanguageInsight,
    InsightGenerationResult,
)
from services.performance_orchestrator import (
    orchestrate_performance_insights,
    PerformanceInsightsConfig,
    PerformanceInsightsResult,
    DriverPerformanceResult as OrchestratorDriverResult,
    PhaseTimingInfo as OrchestratorPhaseTimingInfo,
)
from services.corner_analysis import CornerInput as CACornerInputForOrchestrator

# API service URL for fetching telemetry and lap data
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")

__version__ = ml_service.__version__


# Create FastAPI app
app = FastAPI(
    title="F1 ML Service",
    description="Machine Learning microservice for F1 telemetry analysis",
    version=__version__,
)

# CORS configuration - allow API gateway to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to API gateway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Log service startup."""
    logger.info(f"F1 ML Service v{__version__} starting")
    logger.info("Endpoints: /health, /lap-similarity, /driver-style-clustering, /ml/scaled-delta, /ml/corner-analysis, /ml/technique-profile, /ml/generate-insight, /ml/performance-insights")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": "F1 ML Service",
        "version": __version__,
        "endpoints": {
            "health": "/health",
            "lap_similarity": "/lap-similarity",
            "clustering": "/driver-style-clustering",
            "scaled_delta": "/ml/scaled-delta",
            "corner_analysis": "/ml/corner-analysis",
            "technique_profile": "/ml/technique-profile",
            "generate_insight": "/ml/generate-insight",
            "performance_insights": "/ml/performance-insights",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        service="f1-ml-service",
    )


@app.post("/lap-similarity", response_model=LapSimilarityResponse)
async def calculate_lap_similarity(request: LapSimilarityRequest):
    """
    Calculate cosine similarity between two laps based on telemetry.
    
    The similarity score ranges from 0 to 1:
    - 1.0: Identical driving (same speed/throttle/brake at every distance point)
    - 0.8-0.99: Very similar driving style
    - 0.5-0.8: Moderately similar
    - < 0.5: Different approaches
    
    Args:
        request: Lap similarity request with two lap telemetry datasets
        
    Returns:
        Similarity score and per-feature breakdown
    """
    try:
        # Convert Pydantic models to dictionaries
        lap1_dict = {
            "distance": request.lap1.distance,
            "speed": request.lap1.speed,
            "throttle": request.lap1.throttle,
            "brake": request.lap1.brake,
        }
        
        lap2_dict = {
            "distance": request.lap2.distance,
            "speed": request.lap2.speed,
            "throttle": request.lap2.throttle,
            "brake": request.lap2.brake,
        }
        
        # Add optional features if present
        if request.lap1.gear:
            lap1_dict["gear"] = request.lap1.gear
        if request.lap2.gear:
            lap2_dict["gear"] = request.lap2.gear
        if request.lap1.rpm:
            lap1_dict["rpm"] = request.lap1.rpm
        if request.lap2.rpm:
            lap2_dict["rpm"] = request.lap2.rpm
        
        # Compute similarity
        similarity, feature_scores = compute_lap_similarity(
            lap1_dict,
            lap2_dict,
            features=request.features
        )
        
        return LapSimilarityResponse(
            similarity=similarity,
            feature_scores=feature_scores,
            metadata={
                "features_used": request.features,
                "lap1_points": len(request.lap1.distance),
                "lap2_points": len(request.lap2.distance),
            }
        )
    
    except Exception as e:
        logger.error(f"Error calculating lap similarity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating lap similarity: {str(e)}"
        )


@app.post("/driver-style-clustering", response_model=ClusteringResponse)
async def cluster_drivers(request: ClusteringRequest):
    """
    Cluster drivers by driving style using PCA and KMeans.
    
    This endpoint analyzes telemetry patterns to group drivers with similar
    driving characteristics. Useful for:
    - Identifying aggressive vs conservative drivers
    - Finding drivers with similar setup preferences
    - Analyzing team strategy alignment
    
    Args:
        request: Clustering request with multiple driver telemetry datasets
        
    Returns:
        Cluster assignments with PCA projections for visualization
    """
    try:
        # Prepare driver telemetry data
        driver_data = []
        for driver_input in request.telemetry_data:
            telemetry_dict = {
                "distance": driver_input.telemetry.distance,
                "speed": driver_input.telemetry.speed,
                "throttle": driver_input.telemetry.throttle,
                "brake": driver_input.telemetry.brake,
            }
            
            # Add optional features
            if driver_input.telemetry.gear:
                telemetry_dict["gear"] = driver_input.telemetry.gear
            if driver_input.telemetry.rpm:
                telemetry_dict["rpm"] = driver_input.telemetry.rpm
            
            driver_data.append({
                "driver": driver_input.driver,
                "telemetry": telemetry_dict
            })
        
        # Perform clustering
        labels, pca_projections, explained_variance, cluster_descriptions = cluster_driving_styles(
            driver_data,
            n_clusters=request.n_clusters,
            features=request.features
        )
        
        # Format results
        clusters = []
        for i, driver_input in enumerate(request.telemetry_data):
            clusters.append(
                DriverCluster(
                    driver=driver_input.driver,
                    cluster=int(labels[i]),
                    pca_x=float(pca_projections[i][0]),
                    pca_y=float(pca_projections[i][1]),
                )
            )
        
        return ClusteringResponse(
            clusters=clusters,
            cluster_descriptions=cluster_descriptions,
            explained_variance=explained_variance,
            metadata={
                "n_drivers": len(driver_data),
                "n_clusters": request.n_clusters,
                "features_used": request.features,
            }
        )
    
    except Exception as e:
        logger.error(f"Error clustering drivers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clustering drivers: {str(e)}"
        )


# =============================================================================
# Phase 2: Scaled Delta Endpoint
# =============================================================================

@app.post(
    "/ml/scaled-delta",
    response_model=ScaledDeltaResponse,
    summary="Calculate scaled time delta between drivers",
    description="""
    Calculate time delta between a reference driver and comparison drivers,
    scaled to match official F1 timing.

    This endpoint uses Phase 2's delta analysis algorithm which:
    1. Calculates raw delta from telemetry (shows WHERE time is gained/lost)
    2. Scales the delta to match official timing (ensures correct magnitude)
    3. Returns metadata including scaling factor and confidence score

    The final delta value is GUARANTEED to match the official timing gap.
    """,
    tags=["Phase 2 - Delta Analysis"]
)
async def get_scaled_delta(request: ScaledDeltaRequest):
    """
    Calculate scaled delta using Phase 2's algorithm.

    Fetches telemetry and official lap times from the API service,
    then applies the scaling algorithm to produce accurate deltas.
    """
    logger.info(
        f"Scaled delta request: session={request.session_id}, "
        f"ref={request.reference_driver}, compare={request.compare_drivers}, "
        f"session_part={request.session_part}"
    )

    results = []
    errors = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build query parameters
            all_drivers = [request.reference_driver] + request.compare_drivers
            drivers_param = "&".join([f"drivers={d}" for d in all_drivers])
            session_part_param = f"&session_part={request.session_part}" if request.session_part else ""

            # Fetch telemetry for all drivers
            telemetry_url = (
                f"{API_BASE_URL}/telemetry"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching telemetry from: {telemetry_url}")

            telemetry_response = await client.get(telemetry_url)
            if telemetry_response.status_code != 200:
                logger.error(f"Telemetry fetch failed: {telemetry_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch telemetry data: {telemetry_response.status_code}"
                )
            telemetry_data = telemetry_response.json()

            # Fetch sector times (contains official lap times)
            sectors_url = (
                f"{API_BASE_URL}/laps/sectors"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching sectors from: {sectors_url}")

            sectors_response = await client.get(sectors_url)
            if sectors_response.status_code != 200:
                logger.error(f"Sectors fetch failed: {sectors_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch sector/lap time data: {sectors_response.status_code}"
                )
            sectors_data = sectors_response.json()

        # Build lookup maps for efficient access
        telemetry_map = {t["driver"]: t for t in telemetry_data}
        sectors_map = {s["driver"]: s for s in sectors_data}

        logger.info(
            f"Data fetched: {len(telemetry_map)} telemetry records, "
            f"{len(sectors_map)} sector records"
        )

        # Get reference driver data
        ref_telemetry = telemetry_map.get(request.reference_driver)
        ref_sectors = sectors_map.get(request.reference_driver)

        if not ref_telemetry:
            raise HTTPException(
                status_code=404,
                detail=f"Telemetry not found for reference driver: {request.reference_driver}"
            )
        if not ref_sectors:
            raise HTTPException(
                status_code=404,
                detail=f"Lap times not found for reference driver: {request.reference_driver}"
            )

        ref_official_time = ref_sectors["totalTime"]
        logger.debug(f"Reference driver {request.reference_driver}: {ref_official_time:.3f}s")

        # Calculate scaled delta for each comparison driver
        for comp_driver in request.compare_drivers:
            try:
                comp_telemetry = telemetry_map.get(comp_driver)
                comp_sectors = sectors_map.get(comp_driver)

                if not comp_telemetry:
                    logger.warning(f"Telemetry not found for {comp_driver}, skipping")
                    errors.append(f"No telemetry for {comp_driver}")
                    continue
                if not comp_sectors:
                    logger.warning(f"Lap times not found for {comp_driver}, skipping")
                    errors.append(f"No lap times for {comp_driver}")
                    continue

                comp_official_time = comp_sectors["totalTime"]

                # Convert telemetry to dict format expected by delta_analysis
                # Include relative_distance and time for Tier 1 algorithm
                ref_telem_dict = {
                    "distance": ref_telemetry["distance"],
                    "speed": ref_telemetry["speed"],
                    "relative_distance": ref_telemetry.get("relativeDistance"),  # camelCase from API
                    "time": ref_telemetry.get("time"),
                }
                comp_telem_dict = {
                    "distance": comp_telemetry["distance"],
                    "speed": comp_telemetry["speed"],
                    "relative_distance": comp_telemetry.get("relativeDistance"),
                    "time": comp_telemetry.get("time"),
                }

                logger.debug(
                    f"Calculating delta: {request.reference_driver} vs {comp_driver}, "
                    f"official times: {ref_official_time:.3f}s vs {comp_official_time:.3f}s"
                )

                # Call Phase 2's calculate_scaled_delta
                delta_result: DeltaResult = calculate_scaled_delta(
                    ref_telemetry=ref_telem_dict,
                    comp_telemetry=comp_telem_dict,
                    ref_official_time=ref_official_time,
                    comp_official_time=comp_official_time,
                    ref_driver=request.reference_driver,
                    comp_driver=comp_driver
                )

                logger.info(
                    f"Delta calculated for {comp_driver}: "
                    f"official_gap={delta_result.official_gap:.3f}s, "
                    f"scaling_factor={delta_result.scaling_factor:.3f}, "
                    f"confidence={delta_result.confidence:.2f}"
                )

                # Convert DeltaResult to response schema
                results.append(ScaledDeltaDriverResult(
                    reference_driver=delta_result.reference_driver,
                    compare_driver=delta_result.compare_driver,
                    distance=delta_result.distance,
                    delta=delta_result.delta,
                    raw_delta=delta_result.raw_delta,
                    official_gap=delta_result.official_gap,
                    telemetry_gap=delta_result.telemetry_gap,
                    scaling_factor=delta_result.scaling_factor,
                    confidence=delta_result.confidence
                ))

            except Exception as e:
                logger.error(f"Error calculating delta for {comp_driver}: {e}", exc_info=True)
                errors.append(f"Calculation error for {comp_driver}: {str(e)}")
                continue

        if not results:
            raise HTTPException(
                status_code=422,
                detail=f"Could not calculate delta for any drivers. Errors: {errors}"
            )

        return ScaledDeltaResponse(
            session_id=request.session_id,
            reference_driver=request.reference_driver,
            results=results,
            metadata={
                "session_part": request.session_part,
                "drivers_analyzed": len(results),
                "drivers_failed": len(errors),
                "errors": errors if errors else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in scaled delta calculation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error calculating scaled delta: {str(e)}"
        )


# =============================================================================
# Phase 3: Corner Analysis Endpoint
# =============================================================================

@app.post(
    "/ml/corner-analysis",
    response_model=CornerAnalysisResponse,
    summary="Analyze time gained/lost at each corner",
    description="""
    Analyze WHERE and WHY time is gained or lost at each corner.

    This endpoint uses Phase 3's corner analysis algorithm which:
    1. Detects braking zones using telemetry
    2. Defines corner zones (brake start to apex + exit)
    3. Computes delta change within each zone
    4. Attributes cause (braking, apex, exit, multiple)

    Returns detailed corner-by-corner analysis with confidence levels.
    """,
    tags=["Phase 3 - Corner Analysis"]
)
async def get_corner_analysis(request: CornerAnalysisRequest):
    """
    Analyze time gained/lost at each corner.

    Fetches telemetry from the API service, calculates scaled delta,
    then performs corner-by-corner analysis.
    """
    logger.info(
        f"Corner analysis request: session={request.session_id}, "
        f"ref={request.reference_driver}, compare={request.compare_drivers}, "
        f"corners={len(request.corners)}, session_part={request.session_part}"
    )

    results = []
    errors = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build query parameters
            all_drivers = [request.reference_driver] + request.compare_drivers
            drivers_param = "&".join([f"drivers={d}" for d in all_drivers])
            session_part_param = f"&session_part={request.session_part}" if request.session_part else ""

            # Fetch telemetry for all drivers
            telemetry_url = (
                f"{API_BASE_URL}/telemetry"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching telemetry from: {telemetry_url}")

            telemetry_response = await client.get(telemetry_url)
            if telemetry_response.status_code != 200:
                logger.error(f"Telemetry fetch failed: {telemetry_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch telemetry data: {telemetry_response.status_code}"
                )
            telemetry_data = telemetry_response.json()

            # Fetch sector times (contains official lap times)
            sectors_url = (
                f"{API_BASE_URL}/laps/sectors"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching sectors from: {sectors_url}")

            sectors_response = await client.get(sectors_url)
            if sectors_response.status_code != 200:
                logger.error(f"Sectors fetch failed: {sectors_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch sector/lap time data: {sectors_response.status_code}"
                )
            sectors_data = sectors_response.json()

        # Build lookup maps
        telemetry_map = {t["driver"]: t for t in telemetry_data}
        sectors_map = {s["driver"]: s for s in sectors_data}

        logger.info(
            f"Data fetched: {len(telemetry_map)} telemetry records, "
            f"{len(sectors_map)} sector records"
        )

        # Get reference driver data
        ref_telemetry = telemetry_map.get(request.reference_driver)
        ref_sectors = sectors_map.get(request.reference_driver)

        if not ref_telemetry:
            raise HTTPException(
                status_code=404,
                detail=f"Telemetry not found for reference driver: {request.reference_driver}"
            )
        if not ref_sectors:
            raise HTTPException(
                status_code=404,
                detail=f"Lap times not found for reference driver: {request.reference_driver}"
            )

        # Use lap_time from telemetry if available (more accurate), fall back to sector totalTime
        ref_official_time = ref_telemetry.get("lapTime") or ref_sectors["totalTime"]
        if ref_telemetry.get("lapTime"):
            logger.debug(f"Using telemetry lapTime for {request.reference_driver}: {ref_official_time:.3f}s")
        else:
            logger.debug(f"Using sector totalTime for {request.reference_driver}: {ref_official_time:.3f}s")

        # Convert request corners to CornerInput dataclass
        corner_inputs = [
            CACornerInput(
                corner_number=c.corner_number,
                apex_distance=c.apex_distance,
                corner_type=c.corner_type,
                name=c.name
            )
            for c in request.corners
        ]

        # Process each comparison driver
        for comp_driver in request.compare_drivers:
            try:
                comp_telemetry = telemetry_map.get(comp_driver)
                comp_sectors = sectors_map.get(comp_driver)

                if not comp_telemetry:
                    logger.warning(f"Telemetry not found for {comp_driver}, skipping")
                    errors.append(f"No telemetry for {comp_driver}")
                    continue
                if not comp_sectors:
                    logger.warning(f"Lap times not found for {comp_driver}, skipping")
                    errors.append(f"No lap times for {comp_driver}")
                    continue

                # Use lap_time from telemetry if available (more accurate), fall back to sector totalTime
                comp_official_time = comp_telemetry.get("lapTime") or comp_sectors["totalTime"]
                if comp_telemetry.get("lapTime"):
                    logger.debug(f"Using telemetry lapTime for {comp_driver}: {comp_official_time:.3f}s")
                else:
                    logger.debug(f"Using sector totalTime for {comp_driver}: {comp_official_time:.3f}s")

                # First, calculate scaled delta (Phase 2)
                # Include relative_distance and time for Tier 1 algorithm
                ref_telem_dict = {
                    "distance": ref_telemetry["distance"],
                    "speed": ref_telemetry["speed"],
                    "relative_distance": ref_telemetry.get("relativeDistance"),
                    "time": ref_telemetry.get("time"),
                }
                comp_telem_dict = {
                    "distance": comp_telemetry["distance"],
                    "speed": comp_telemetry["speed"],
                    "relative_distance": comp_telemetry.get("relativeDistance"),
                    "time": comp_telemetry.get("time"),
                }

                delta_result = calculate_scaled_delta(
                    ref_telemetry=ref_telem_dict,
                    comp_telemetry=comp_telem_dict,
                    ref_official_time=ref_official_time,
                    comp_official_time=comp_official_time,
                    ref_driver=request.reference_driver,
                    comp_driver=comp_driver
                )

                # Now, perform corner analysis (Phase 3)
                # Use v2 if speed data is available, otherwise fall back to v1
                ref_has_speed = "speed" in ref_telemetry and len(ref_telemetry["speed"]) > 0
                comp_has_speed = "speed" in comp_telemetry and len(comp_telemetry["speed"]) > 0

                if ref_has_speed and comp_has_speed:
                    # Use v2 with deceleration-based detection
                    logger.debug(f"Using v2 corner analysis for {comp_driver}")
                    corner_result = analyze_corners_v2(
                        delta_result=delta_result,
                        ref_distance=ref_telemetry["distance"],
                        ref_brake=ref_telemetry["brake"],
                        ref_speed=ref_telemetry["speed"],
                        comp_distance=comp_telemetry["distance"],
                        comp_brake=comp_telemetry["brake"],
                        comp_speed=comp_telemetry["speed"],
                        corners=corner_inputs,
                        circuit_id=request.circuit_id if hasattr(request, "circuit_id") else ""
                    )
                else:
                    # Fall back to v1
                    logger.debug(f"Using v1 corner analysis for {comp_driver} (speed data unavailable)")
                    corner_result = analyze_corners(
                        delta_result=delta_result,
                        ref_distance=ref_telemetry["distance"],
                        ref_brake=ref_telemetry["brake"],
                        comp_distance=comp_telemetry["distance"],
                        comp_brake=comp_telemetry["brake"],
                        corners=corner_inputs
                    )

                # Convert to response schema
                corner_results_schema = [
                    CornerResultSchema(
                        corner_number=cr.corner_number,
                        name=cr.name,
                        apex_distance=cr.apex_distance,
                        brake_distance=cr.brake_distance,
                        zone_start=cr.zone_start,
                        zone_end=cr.zone_end,
                        delta_change=cr.delta_change,
                        cause=cr.cause,
                        confidence=cr.confidence
                    )
                    for cr in corner_result.corner_results
                ]

                # Sector validation (optional, if sector_boundaries provided)
                validation_report = None
                analysis_version = "v2" if ref_has_speed and comp_has_speed else "v1"

                if (
                    hasattr(request, "sector_boundaries")
                    and request.sector_boundaries
                    and len(request.sector_boundaries) >= 2
                ):
                    # Get sector times from the sectors data
                    ref_sector_times = (
                        ref_sectors.get("sector1", 0),
                        ref_sectors.get("sector2", 0),
                        ref_sectors.get("sector3", 0),
                    )
                    comp_sector_times = (
                        comp_sectors.get("sector1", 0),
                        comp_sectors.get("sector2", 0),
                        comp_sectors.get("sector3", 0),
                    )

                    # Only validate if we have actual sector times
                    if all(t > 0 for t in ref_sector_times) and all(t > 0 for t in comp_sector_times):
                        try:
                            sector_boundaries = (
                                request.sector_boundaries[0],
                                request.sector_boundaries[1]
                            )

                            validations, conf_adj = validate_against_sectors(
                                corner_results=corner_result.corner_results,
                                sector_boundaries=sector_boundaries,
                                ref_sectors=ref_sector_times,
                                comp_sectors=comp_sector_times,
                            )

                            # Count corners per sector
                            s1_end, s2_end = sector_boundaries
                            sector_corner_counts = [0, 0, 0]
                            for cr in corner_result.corner_results:
                                if cr.apex_distance < s1_end:
                                    sector_corner_counts[0] += 1
                                elif cr.apex_distance < s2_end:
                                    sector_corner_counts[1] += 1
                                else:
                                    sector_corner_counts[2] += 1

                            validation_report = ValidationReportSchema(
                                sector_validations=[
                                    SectorValidationSchema(
                                        sector_number=v.sector_number,
                                        corner_delta_sum=v.corner_delta_sum,
                                        official_delta=v.official_delta,
                                        difference=v.difference,
                                        is_valid=v.is_valid,
                                        corners_in_sector=sector_corner_counts[v.sector_number - 1]
                                    )
                                    for v in validations
                                ],
                                overall_valid=all(v.is_valid for v in validations),
                                confidence_adjustment=conf_adj,
                                total_corner_delta=corner_result.total_delta_change,
                                official_lap_delta=sum(comp_sector_times) - sum(ref_sector_times)
                            )

                            logger.info(
                                f"Sector validation for {comp_driver}: "
                                f"{sum(1 for v in validations if v.is_valid)}/3 sectors valid, "
                                f"conf_adj={conf_adj:.2f}"
                            )
                        except Exception as e:
                            logger.warning(f"Sector validation failed for {comp_driver}: {e}")

                results.append(CornerAnalysisDriverResult(
                    compare_driver=comp_driver,
                    corner_results=corner_results_schema,
                    total_delta_change=corner_result.total_delta_change,
                    corners_gaining=corner_result.corners_gaining,
                    corners_losing=corner_result.corners_losing,
                    validation=validation_report,
                    analysis_version=analysis_version
                ))

                logger.info(
                    f"Corner analysis for {comp_driver}: "
                    f"total_delta={corner_result.total_delta_change:+.3f}s, "
                    f"gaining={corner_result.corners_gaining}, "
                    f"losing={corner_result.corners_losing}"
                )

            except Exception as e:
                logger.error(f"Error analyzing corners for {comp_driver}: {e}", exc_info=True)
                errors.append(f"Analysis error for {comp_driver}: {str(e)}")
                continue

        if not results:
            raise HTTPException(
                status_code=422,
                detail=f"Could not analyze corners for any drivers. Errors: {errors}"
            )

        return CornerAnalysisResponse(
            session_id=request.session_id,
            reference_driver=request.reference_driver,
            results=results,
            metadata={
                "session_part": request.session_part,
                "drivers_analyzed": len(results),
                "corners_analyzed": len(request.corners),
                "drivers_failed": len(errors),
                "errors": errors if errors else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in corner analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error analyzing corners: {str(e)}"
        )


# =============================================================================
# Phase 4: Technique Profiling Endpoint
# =============================================================================

@app.post(
    "/ml/technique-profile",
    response_model=TechniqueProfilingResponse,
    summary="Generate technique profiles for drivers",
    description="""
    Profile drivers' techniques using session-relative classification.

    This endpoint builds on Phase 3's corner analysis to:
    1. Aggregate corner results by cause type (braking/apex/exit)
    2. Calculate session percentiles across all comparison drivers
    3. Classify each driver's technique dimensions (STRONG/NEUTRAL/WEAK)
    4. Generate style summaries for natural language output (Phase 5)

    The classification is SESSION-RELATIVE, meaning a "STRONG braker" at Monaco
    is compared to other Monaco Q3 drivers, not to an absolute threshold.
    """,
    tags=["Phase 4 - Technique Profiling"]
)
async def get_technique_profile(request: TechniqueProfilingRequest):
    """
    Generate technique profiles for drivers.

    Fetches telemetry from the API service, performs corner analysis,
    then profiles each driver's technique using session-relative classification.
    """
    logger.info(
        f"Technique profiling request: session={request.session_id}, "
        f"ref={request.reference_driver}, compare={request.compare_drivers}, "
        f"corners={len(request.corners)}, session_part={request.session_part}"
    )

    corner_results_by_driver: dict[str, CornerAnalysisResult] = {}
    errors = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build query parameters
            all_drivers = [request.reference_driver] + request.compare_drivers
            drivers_param = "&".join([f"drivers={d}" for d in all_drivers])
            session_part_param = f"&session_part={request.session_part}" if request.session_part else ""

            # Fetch telemetry for all drivers
            telemetry_url = (
                f"{API_BASE_URL}/telemetry"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching telemetry from: {telemetry_url}")

            telemetry_response = await client.get(telemetry_url)
            if telemetry_response.status_code != 200:
                logger.error(f"Telemetry fetch failed: {telemetry_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch telemetry data: {telemetry_response.status_code}"
                )
            telemetry_data = telemetry_response.json()

            # Fetch sector times (contains official lap times)
            sectors_url = (
                f"{API_BASE_URL}/laps/sectors"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching sectors from: {sectors_url}")

            sectors_response = await client.get(sectors_url)
            if sectors_response.status_code != 200:
                logger.error(f"Sectors fetch failed: {sectors_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch sector/lap time data: {sectors_response.status_code}"
                )
            sectors_data = sectors_response.json()

        # Build lookup maps
        telemetry_map = {t["driver"]: t for t in telemetry_data}
        sectors_map = {s["driver"]: s for s in sectors_data}

        logger.info(
            f"Data fetched: {len(telemetry_map)} telemetry records, "
            f"{len(sectors_map)} sector records"
        )

        # Get reference driver data
        ref_telemetry = telemetry_map.get(request.reference_driver)
        ref_sectors = sectors_map.get(request.reference_driver)

        if not ref_telemetry:
            raise HTTPException(
                status_code=404,
                detail=f"Telemetry not found for reference driver: {request.reference_driver}"
            )
        if not ref_sectors:
            raise HTTPException(
                status_code=404,
                detail=f"Lap times not found for reference driver: {request.reference_driver}"
            )

        ref_official_time = ref_sectors["totalTime"]

        # Convert request corners to CornerInput dataclass
        corner_inputs = [
            CACornerInput(
                corner_number=c.corner_number,
                apex_distance=c.apex_distance,
                corner_type=c.corner_type,
                name=c.name
            )
            for c in request.corners
        ]

        # Step 1: Perform corner analysis for each comparison driver
        for comp_driver in request.compare_drivers:
            try:
                comp_telemetry = telemetry_map.get(comp_driver)
                comp_sectors = sectors_map.get(comp_driver)

                if not comp_telemetry:
                    logger.warning(f"Telemetry not found for {comp_driver}, skipping")
                    errors.append(f"No telemetry for {comp_driver}")
                    continue
                if not comp_sectors:
                    logger.warning(f"Lap times not found for {comp_driver}, skipping")
                    errors.append(f"No lap times for {comp_driver}")
                    continue

                comp_official_time = comp_sectors["totalTime"]

                # Calculate scaled delta (Phase 2)
                # Include relative_distance and time for Tier 1 algorithm
                ref_telem_dict = {
                    "distance": ref_telemetry["distance"],
                    "speed": ref_telemetry["speed"],
                    "relative_distance": ref_telemetry.get("relativeDistance"),
                    "time": ref_telemetry.get("time"),
                }
                comp_telem_dict = {
                    "distance": comp_telemetry["distance"],
                    "speed": comp_telemetry["speed"],
                    "relative_distance": comp_telemetry.get("relativeDistance"),
                    "time": comp_telemetry.get("time"),
                }

                delta_result = calculate_scaled_delta(
                    ref_telemetry=ref_telem_dict,
                    comp_telemetry=comp_telem_dict,
                    ref_official_time=ref_official_time,
                    comp_official_time=comp_official_time,
                    ref_driver=request.reference_driver,
                    comp_driver=comp_driver
                )

                # Perform corner analysis (Phase 3)
                # Use v2 if speed data is available
                ref_has_speed = "speed" in ref_telemetry and len(ref_telemetry["speed"]) > 0
                comp_has_speed = "speed" in comp_telemetry and len(comp_telemetry["speed"]) > 0

                if ref_has_speed and comp_has_speed:
                    corner_result = analyze_corners_v2(
                        delta_result=delta_result,
                        ref_distance=ref_telemetry["distance"],
                        ref_brake=ref_telemetry["brake"],
                        ref_speed=ref_telemetry["speed"],
                        comp_distance=comp_telemetry["distance"],
                        comp_brake=comp_telemetry["brake"],
                        comp_speed=comp_telemetry["speed"],
                        corners=corner_inputs,
                        circuit_id=request.circuit_id if hasattr(request, "circuit_id") else ""
                    )
                else:
                    corner_result = analyze_corners(
                        delta_result=delta_result,
                        ref_distance=ref_telemetry["distance"],
                        ref_brake=ref_telemetry["brake"],
                        comp_distance=comp_telemetry["distance"],
                        comp_brake=comp_telemetry["brake"],
                        corners=corner_inputs
                    )

                # Store for profiling
                corner_results_by_driver[comp_driver] = corner_result

                logger.debug(
                    f"Corner analysis for {comp_driver}: "
                    f"total_delta={corner_result.total_delta_change:+.3f}s"
                )

            except Exception as e:
                logger.error(f"Error analyzing {comp_driver}: {e}", exc_info=True)
                errors.append(f"Analysis error for {comp_driver}: {str(e)}")
                continue

        if not corner_results_by_driver:
            raise HTTPException(
                status_code=422,
                detail=f"Could not analyze any drivers. Errors: {errors}"
            )

        # Step 2: Profile drivers using technique profiling (Phase 4)
        profiles, session_percentiles = profile_drivers(
            corner_results_by_driver=corner_results_by_driver,
            reference_driver=request.reference_driver,
            weight_by_confidence=request.weight_by_confidence
        )

        # Convert to response schemas
        profile_schemas = []
        for profile in profiles:
            profile_schemas.append(TechniqueProfileSchema(
                driver=profile.driver,
                reference_driver=profile.reference_driver,
                braking=TechniqueDimensionSchema(
                    level=profile.braking.level.value,
                    descriptor=profile.braking.descriptor,
                    percentile=profile.braking.percentile,
                    raw_value=profile.braking.raw_value,
                    corner_count=profile.braking.corner_count,
                    avg_confidence=profile.braking.avg_confidence
                ),
                apex=TechniqueDimensionSchema(
                    level=profile.apex.level.value,
                    descriptor=profile.apex.descriptor,
                    percentile=profile.apex.percentile,
                    raw_value=profile.apex.raw_value,
                    corner_count=profile.apex.corner_count,
                    avg_confidence=profile.apex.avg_confidence
                ),
                exit=TechniqueDimensionSchema(
                    level=profile.exit.level.value,
                    descriptor=profile.exit.descriptor,
                    percentile=profile.exit.percentile,
                    raw_value=profile.exit.raw_value,
                    corner_count=profile.exit.corner_count,
                    avg_confidence=profile.exit.avg_confidence
                ),
                consistency=TechniqueDimensionSchema(
                    level=profile.consistency.level.value,
                    descriptor=profile.consistency.descriptor,
                    percentile=profile.consistency.percentile,
                    raw_value=profile.consistency.raw_value,
                    corner_count=profile.consistency.corner_count,
                    avg_confidence=profile.consistency.avg_confidence
                ),
                top_gaining_corners=profile.top_gaining_corners,
                top_losing_corners=profile.top_losing_corners,
                style_summary=profile.style_summary,
                overall_confidence=profile.overall_confidence,
                total_corners_analyzed=profile.total_corners_analyzed
            ))

            logger.info(
                f"Profiled {profile.driver}: {profile.style_summary} "
                f"(braking={profile.braking.level.value}, exit={profile.exit.level.value})"
            )

        session_percentiles_schema = SessionPercentilesSchema(
            braking_p30=session_percentiles.braking_p30,
            braking_p70=session_percentiles.braking_p70,
            apex_p30=session_percentiles.apex_p30,
            apex_p70=session_percentiles.apex_p70,
            exit_p30=session_percentiles.exit_p30,
            exit_p70=session_percentiles.exit_p70,
            consistency_p30=session_percentiles.consistency_p30,
            consistency_p70=session_percentiles.consistency_p70,
            driver_count=session_percentiles.driver_count
        )

        return TechniqueProfilingResponse(
            session_id=request.session_id,
            reference_driver=request.reference_driver,
            profiles=profile_schemas,
            session_percentiles=session_percentiles_schema,
            metadata={
                "session_part": request.session_part,
                "drivers_analyzed": len(profile_schemas),
                "corners_analyzed": len(request.corners),
                "drivers_failed": len(errors),
                "errors": errors if errors else None,
                "weight_by_confidence": request.weight_by_confidence
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in technique profiling: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error in technique profiling: {str(e)}"
        )


# =============================================================================
# Phase 5: Natural Language Insight Generation Endpoint
# =============================================================================

@app.post(
    "/ml/generate-insight",
    response_model=InsightGenerationResponse,
    summary="Generate natural language insights for drivers",
    description="""
    Generate human-readable insights from technique profiles.

    This endpoint chains Phase 2 -> 3 -> 4 -> 5 to:
    1. Calculate scaled deltas (Phase 2)
    2. Analyze corners (Phase 3)
    3. Generate technique profiles (Phase 4)
    4. Transform profiles into natural language insights (Phase 5)

    Supports two modes:
    - ENGINEER: Metrics-heavy with percentiles and raw values
    - DRIVER: Actionable feedback without technical details

    ANTI-HALLUCINATION: All text is template-based with data placeholders.
    No free-form text generation occurs.
    """,
    tags=["Phase 5 - Natural Language Insights"]
)
async def generate_driver_insights(request: InsightGenerationRequest):
    """
    Generate natural language insights for drivers.

    Chains all previous phases internally and produces human-readable output.
    """
    logger.info(
        f"Insight generation request: session={request.session_id}, "
        f"ref={request.reference_driver}, compare={request.compare_drivers}, "
        f"mode={request.mode}"
    )

    # Validate mode
    try:
        mode = InsightMode(request.mode.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{request.mode}'. Use 'engineer' or 'driver'."
        )

    # Build session context
    session_context = {}
    if request.circuit_name:
        session_context["circuit"] = request.circuit_name
    if request.session_part:
        session_context["session"] = request.session_part

    errors = []
    corner_results_by_driver: dict[str, CornerAnalysisResult] = {}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Build query parameters
            all_drivers = [request.reference_driver] + request.compare_drivers
            drivers_param = "&".join([f"drivers={d}" for d in all_drivers])
            session_part_param = f"&session_part={request.session_part}" if request.session_part else ""

            # Fetch telemetry for all drivers
            telemetry_url = (
                f"{API_BASE_URL}/telemetry"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching telemetry from: {telemetry_url}")

            telemetry_response = await client.get(telemetry_url)
            if telemetry_response.status_code != 200:
                logger.error(f"Telemetry fetch failed: {telemetry_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch telemetry data: {telemetry_response.status_code}"
                )
            telemetry_data = telemetry_response.json()

            # Fetch sector times (contains official lap times)
            sectors_url = (
                f"{API_BASE_URL}/laps/sectors"
                f"?session={request.session_id}&{drivers_param}{session_part_param}"
            )
            logger.debug(f"Fetching sectors from: {sectors_url}")

            sectors_response = await client.get(sectors_url)
            if sectors_response.status_code != 200:
                logger.error(f"Sectors fetch failed: {sectors_response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to fetch sector/lap time data: {sectors_response.status_code}"
                )
            sectors_data = sectors_response.json()

        # Build lookup maps
        telemetry_map = {t["driver"]: t for t in telemetry_data}
        sectors_map = {s["driver"]: s for s in sectors_data}

        logger.info(
            f"Data fetched: {len(telemetry_map)} telemetry records, "
            f"{len(sectors_map)} sector records"
        )

        # Get reference driver data
        ref_telemetry = telemetry_map.get(request.reference_driver)
        ref_sectors = sectors_map.get(request.reference_driver)

        if not ref_telemetry:
            raise HTTPException(
                status_code=404,
                detail=f"Telemetry not found for reference driver: {request.reference_driver}"
            )
        if not ref_sectors:
            raise HTTPException(
                status_code=404,
                detail=f"Lap times not found for reference driver: {request.reference_driver}"
            )

        ref_official_time = ref_sectors["totalTime"]

        # Convert request corners to CornerInput dataclass
        corner_inputs = [
            CACornerInput(
                corner_number=c.corner_number,
                apex_distance=c.apex_distance,
                corner_type=c.corner_type,
                name=c.name
            )
            for c in request.corners
        ]

        # Step 1: Perform corner analysis for each comparison driver (Phase 2 + 3)
        for comp_driver in request.compare_drivers:
            try:
                comp_telemetry = telemetry_map.get(comp_driver)
                comp_sectors = sectors_map.get(comp_driver)

                if not comp_telemetry:
                    logger.warning(f"Telemetry not found for {comp_driver}, skipping")
                    errors.append(f"No telemetry for {comp_driver}")
                    continue
                if not comp_sectors:
                    logger.warning(f"Lap times not found for {comp_driver}, skipping")
                    errors.append(f"No lap times for {comp_driver}")
                    continue

                comp_official_time = comp_sectors["totalTime"]

                # Calculate scaled delta (Phase 2)
                # Include relative_distance and time for Tier 1 algorithm
                ref_telem_dict = {
                    "distance": ref_telemetry["distance"],
                    "speed": ref_telemetry["speed"],
                    "relative_distance": ref_telemetry.get("relativeDistance"),
                    "time": ref_telemetry.get("time"),
                }
                comp_telem_dict = {
                    "distance": comp_telemetry["distance"],
                    "speed": comp_telemetry["speed"],
                    "relative_distance": comp_telemetry.get("relativeDistance"),
                    "time": comp_telemetry.get("time"),
                }

                delta_result = calculate_scaled_delta(
                    ref_telemetry=ref_telem_dict,
                    comp_telemetry=comp_telem_dict,
                    ref_official_time=ref_official_time,
                    comp_official_time=comp_official_time,
                    ref_driver=request.reference_driver,
                    comp_driver=comp_driver
                )

                # Perform corner analysis (Phase 3)
                # Use v2 if speed data is available
                ref_has_speed = "speed" in ref_telemetry and len(ref_telemetry["speed"]) > 0
                comp_has_speed = "speed" in comp_telemetry and len(comp_telemetry["speed"]) > 0

                if ref_has_speed and comp_has_speed:
                    corner_result = analyze_corners_v2(
                        delta_result=delta_result,
                        ref_distance=ref_telemetry["distance"],
                        ref_brake=ref_telemetry["brake"],
                        ref_speed=ref_telemetry["speed"],
                        comp_distance=comp_telemetry["distance"],
                        comp_brake=comp_telemetry["brake"],
                        comp_speed=comp_telemetry["speed"],
                        corners=corner_inputs,
                        circuit_id=""
                    )
                else:
                    corner_result = analyze_corners(
                        delta_result=delta_result,
                        ref_distance=ref_telemetry["distance"],
                        ref_brake=ref_telemetry["brake"],
                        comp_distance=comp_telemetry["distance"],
                        comp_brake=comp_telemetry["brake"],
                        corners=corner_inputs
                    )

                corner_results_by_driver[comp_driver] = corner_result

                logger.debug(
                    f"Corner analysis for {comp_driver}: "
                    f"total_delta={corner_result.total_delta_change:+.3f}s"
                )

            except Exception as e:
                logger.error(f"Error analyzing {comp_driver}: {e}", exc_info=True)
                errors.append(f"Analysis error for {comp_driver}: {str(e)}")
                continue

        if not corner_results_by_driver:
            raise HTTPException(
                status_code=422,
                detail=f"Could not analyze any drivers. Errors: {errors}"
            )

        # Step 2: Generate technique profiles (Phase 4)
        profiles, session_percentiles = profile_drivers(
            corner_results_by_driver=corner_results_by_driver,
            reference_driver=request.reference_driver,
            weight_by_confidence=True
        )

        # Step 3: Generate insights for each profile (Phase 5)
        insight_schemas = []

        for profile in profiles:
            try:
                result = generate_insights(
                    profile=profile,
                    mode=mode,
                    session_context=session_context
                )

                if result.success and result.insight:
                    insight = result.insight

                    # Convert dataclass to Pydantic schema
                    insight_schema = NaturalLanguageInsightSchema(
                        driver=insight.driver,
                        reference_driver=insight.reference_driver,
                        mode=insight.mode.value,
                        confidence_level=insight.confidence_level.value,
                        summary=insight.summary,
                        dimension_insights=[
                            DimensionInsightSchema(
                                dimension=d.dimension,
                                level=d.level,
                                percentile=d.percentile,
                                text=d.text,
                                raw_value_ms=d.raw_value_ms,
                                corner_count=d.corner_count,
                            )
                            for d in insight.dimension_insights
                        ],
                        corner_insights=[
                            CornerInsightSchema(
                                corner_name=c.corner_name,
                                delta_ms=c.delta_ms,
                                direction=c.direction,
                                cause=c.cause,
                                text=c.text,
                                confidence=c.confidence,
                            )
                            for c in insight.corner_insights
                        ],
                        opportunity_text=insight.opportunity_text,
                        hedging_prefix=insight.hedging_prefix,
                        total_corners=insight.total_corners,
                        session_context=insight.session_context,
                        style_summary=insight.style_summary,
                    )

                    insight_schemas.append(insight_schema)

                    logger.info(
                        f"Generated insight for {insight.driver}: "
                        f"mode={insight.mode.value}, confidence={insight.confidence_level.value}"
                    )
                else:
                    errors.append(f"Insight generation failed for {profile.driver}")

            except Exception as e:
                logger.error(f"Error generating insight for {profile.driver}: {e}", exc_info=True)
                errors.append(f"Insight error for {profile.driver}: {str(e)}")

        return InsightGenerationResponse(
            session_id=request.session_id,
            reference_driver=request.reference_driver,
            insights=insight_schemas,
            metadata={
                "mode": mode.value,
                "session_part": request.session_part,
                "circuit": request.circuit_name,
                "drivers_processed": len(insight_schemas),
                "drivers_failed": len(errors),
                "corners_analyzed": len(request.corners),
                "errors": errors if errors else None,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in insight generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error generating insights: {str(e)}"
        )


# =============================================================================
# Phase 6: Performance Insights Orchestrator Endpoint
# =============================================================================

@app.post(
    "/ml/performance-insights",
    response_model=PerformanceInsightsResponse,
    summary="Unified performance insights (chains Phases 2-5)",
    description="""
    Single-call endpoint that orchestrates the entire analysis pipeline.

    This is the Backend-for-Frontend (BFF) pattern that reduces frontend
    complexity from 4 API calls down to 1. It chains:
    1. Phase 2: Scaled Delta Analysis
    2. Phase 3: Corner Analysis
    3. Phase 4: Technique Profiling
    4. Phase 5: Natural Language Insights

    Returns complete analysis for all requested drivers in a single response,
    including timing information for each phase.

    Use this endpoint for production frontend integration. Use individual
    phase endpoints for debugging or partial analysis.
    """,
    tags=["Phase 6 - Performance Orchestrator"]
)
async def get_performance_insights(request: PerformanceInsightsRequest):
    """
    Orchestrate complete performance analysis pipeline.

    This endpoint is the primary integration point for frontend applications.
    It handles all telemetry fetching, analysis phases, and error handling
    internally, returning a unified response.
    """
    logger.info(
        f"Performance insights request: session={request.session_id}, "
        f"ref={request.reference_driver}, compare={request.compare_drivers}, "
        f"mode={request.mode}, corners={len(request.corners)}"
    )

    try:
        # Convert request corners to CornerInput dataclass
        corner_inputs = [
            CACornerInputForOrchestrator(
                corner_number=c.corner_number,
                apex_distance=c.apex_distance,
                corner_type=c.corner_type,
                name=c.name
            )
            for c in request.corners
        ]

        # Build orchestrator config
        config = PerformanceInsightsConfig(
            session_id=request.session_id,
            reference_driver=request.reference_driver,
            compare_drivers=request.compare_drivers,
            corners=corner_inputs,
            mode=request.mode,
            session_part=request.session_part,
            circuit_name=request.circuit_name,
            include_telemetry=request.include_telemetry,
            track_length=request.track_length,
        )

        # Run orchestration
        async with httpx.AsyncClient(timeout=60.0) as client:
            result = await orchestrate_performance_insights(config, client)

        # Convert orchestrator result to response schema
        driver_results = []
        for dr in result.results:
            driver_results.append(DriverPerformanceResult(
                driver=dr.driver,
                official_gap=dr.official_gap,
                scaling_confidence=dr.scaling_confidence,
                delta=dr.delta,
                distance=dr.distance,
                corners_gaining=dr.corners_gaining,
                corners_losing=dr.corners_losing,
                total_corner_delta=dr.total_corner_delta,
                corner_results=[
                    CornerResultSchema(
                        corner_number=cr["corner_number"],
                        name=cr.get("name"),
                        apex_distance=cr["apex_distance"],
                        brake_distance=cr["brake_distance"],
                        zone_start=cr["zone_start"],
                        zone_end=cr["zone_end"],
                        delta_change=cr["delta_change"],
                        cause=cr["cause"],
                        confidence=cr["confidence"],
                    )
                    for cr in dr.corner_results
                ] if dr.corner_results else [],
                lap_breakdown=LapBreakdownSchema(
                    corner_total=dr.lap_breakdown["corner_total"],
                    straight_total=dr.lap_breakdown["straight_total"],
                    official_gap=dr.lap_breakdown["official_gap"],
                    track_coverage=dr.lap_breakdown["track_coverage"],
                    straight_segments=[
                        StraightSegmentSchema(**seg)
                        for seg in dr.lap_breakdown.get("straight_segments", [])
                    ],
                    reconciliation_valid=dr.lap_breakdown["reconciliation_valid"],
                    reconciliation_error=dr.lap_breakdown["reconciliation_error"],
                    insight_text=dr.lap_breakdown.get("insight_text", ""),
                ) if dr.lap_breakdown else None,
                technique_profile=TechniqueProfileSchema(
                    driver=dr.technique_profile["driver"],
                    reference_driver=dr.technique_profile["reference_driver"],
                    braking=TechniqueDimensionSchema(**dr.technique_profile["braking"]),
                    apex=TechniqueDimensionSchema(**dr.technique_profile["apex"]),
                    exit=TechniqueDimensionSchema(**dr.technique_profile["exit"]),
                    consistency=TechniqueDimensionSchema(**dr.technique_profile["consistency"]),
                    top_gaining_corners=dr.technique_profile.get("top_gaining_corners", []),
                    top_losing_corners=dr.technique_profile.get("top_losing_corners", []),
                    style_summary=dr.technique_profile.get("style_summary", ""),
                    overall_confidence=dr.technique_profile.get("overall_confidence", 0.0),
                    total_corners_analyzed=dr.technique_profile.get("total_corners_analyzed", 0),
                ) if dr.technique_profile else None,
                insight=NaturalLanguageInsightSchema(
                    driver=dr.insight["driver"],
                    reference_driver=dr.insight["reference_driver"],
                    mode=dr.insight["mode"],
                    confidence_level=dr.insight["confidence_level"],
                    summary=dr.insight["summary"],
                    dimension_insights=[
                        DimensionInsightSchema(**di)
                        for di in dr.insight.get("dimension_insights", [])
                    ],
                    corner_insights=[
                        CornerInsightSchema(**ci)
                        for ci in dr.insight.get("corner_insights", [])
                    ],
                    opportunity_text=dr.insight.get("opportunity_text", ""),
                    hedging_prefix=dr.insight.get("hedging_prefix", ""),
                    total_corners=dr.insight.get("total_corners", 0),
                    session_context=dr.insight.get("session_context", {}),
                    style_summary=dr.insight.get("style_summary", ""),
                ) if dr.insight else None,
            ))

        # Convert session percentiles
        session_percentiles_schema = None
        if result.session_percentiles:
            session_percentiles_schema = SessionPercentilesSchema(
                braking_p30=result.session_percentiles["braking_p30"],
                braking_p70=result.session_percentiles["braking_p70"],
                apex_p30=result.session_percentiles["apex_p30"],
                apex_p70=result.session_percentiles["apex_p70"],
                exit_p30=result.session_percentiles["exit_p30"],
                exit_p70=result.session_percentiles["exit_p70"],
                consistency_p30=result.session_percentiles["consistency_p30"],
                consistency_p70=result.session_percentiles["consistency_p70"],
                driver_count=result.session_percentiles["driver_count"],
            )

        # Convert phase timing
        phase_timing = [
            PhaseTimingInfo(
                phase=pt.phase,
                duration_ms=pt.duration_ms,
                success=pt.success,
                error=pt.error,
            )
            for pt in result.phase_timing
        ]

        logger.info(
            f"Performance insights complete: "
            f"{result.total_drivers_processed}/{result.total_drivers_requested} drivers, "
            f"{result.total_duration_ms}ms total"
        )

        return PerformanceInsightsResponse(
            session_id=result.session_id,
            reference_driver=result.reference_driver,
            circuit_name=result.circuit_name,
            mode=result.mode,
            results=driver_results,
            session_percentiles=session_percentiles_schema,
            total_drivers_requested=result.total_drivers_requested,
            total_drivers_processed=result.total_drivers_processed,
            total_corners=result.total_corners,
            phase_timing=phase_timing,
            total_duration_ms=result.total_duration_ms,
            errors=result.errors,
            warnings=result.warnings,
        )

    except Exception as e:
        logger.error(f"Unexpected error in performance insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error in performance insights: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501, reload=True)

