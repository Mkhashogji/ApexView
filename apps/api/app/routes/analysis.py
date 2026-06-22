"""Analysis service proxy routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from pydantic import BaseModel
from app.services.analysis_proxy.client import analysis_client
from app.services.telemetry.fastf1_client import FastF1Client
from app.services.telemetry.native_acquisition import NativeAcquisitionError


router = APIRouter()


class LapSimilarityRequest(BaseModel):
    """Request for lap similarity via proxy."""
    session_id: str
    driver1: str
    driver2: str


class ClusteringRequest(BaseModel):
    """Request for driver clustering via proxy."""
    session_id: str
    drivers: List[str]
    n_clusters: int = 3


@router.get("/health")
async def analysis_service_health():
    """
    Check Analysis service health.
    
    Returns:
        Health status of Analysis service
    """
    is_healthy = await analysis_client.health_check()
    
    if is_healthy:
        return {"status": "healthy", "service": "analysis"}
    else:
        raise HTTPException(
            status_code=503,
            detail="Analysis service is unavailable"
        )


@router.post("/lap-similarity")
async def calculate_lap_similarity(request: LapSimilarityRequest):
    """
    Calculate similarity between two drivers' fastest laps.
    
    This endpoint:
    1. Fetches telemetry for both drivers from the session
    2. Calls Analysis service to compute similarity
    3. Returns similarity score and breakdown
    
    Args:
        request: Lap similarity request
        
    Returns:
        Similarity analysis from Analysis service
    """
    try:
        # Fetch telemetry for both drivers
        client = FastF1Client()
        telemetry_data = await client.get_telemetry(
            request.session_id,
            [request.driver1, request.driver2]
        )
        
        if len(telemetry_data) < 2:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch telemetry for both drivers"
            )
        
        # Find telemetry for each driver
        driver1_telem = next((t for t in telemetry_data if t.driver == request.driver1), None)
        driver2_telem = next((t for t in telemetry_data if t.driver == request.driver2), None)
        
        if not driver1_telem or not driver2_telem:
            raise HTTPException(
                status_code=404,
                detail="Telemetry not found for one or both drivers"
            )
        
        # Prepare data for Analysis service
        lap1_data = {
            "distance": driver1_telem.distance,
            "speed": driver1_telem.speed,
            "throttle": driver1_telem.throttle,
            "brake": driver1_telem.brake,
        }
        
        lap2_data = {
            "distance": driver2_telem.distance,
            "speed": driver2_telem.speed,
            "throttle": driver2_telem.throttle,
            "brake": driver2_telem.brake,
        }
        
        # Call Analysis service
        result = await analysis_client.calculate_similarity(lap1_data, lap2_data)
        
        return {
            "session_id": request.session_id,
            "driver1": request.driver1,
            "driver2": request.driver2,
            "similarity": result.get("similarity", 0.0),
            "feature_scores": result.get("feature_scores", {}),
            "metadata": result.get("metadata", {}),
        }
    
    except HTTPException:
        raise
    except NativeAcquisitionError as e:
        # G0: native acquisition failures surface structured, never as a
        # stringified 500 (continuation review L2-2/L4-1).
        raise HTTPException(status_code=502, detail=e.to_detail())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating similarity: {str(e)}"
        )


@router.post("/driver-style-clustering")
async def cluster_driver_styles(request: ClusteringRequest):
    """
    Cluster drivers by driving style using telemetry analysis.
    
    This endpoint:
    1. Fetches telemetry for all specified drivers
    2. Calls Analysis service to perform PCA + KMeans clustering
    3. Returns cluster assignments and PCA projections
    
    Args:
        request: Clustering request
        
    Returns:
        Cluster assignments and visualization data
    """
    try:
        # Fetch telemetry for all drivers
        client = FastF1Client()
        telemetry_data = await client.get_telemetry(
            request.session_id,
            request.drivers
        )
        
        if len(telemetry_data) < 2:
            raise HTTPException(
                status_code=400,
                detail="Need at least 2 drivers for clustering"
            )
        
        # Prepare data for Analysis service
        driver_telemetry = []
        for telem in telemetry_data:
            driver_telemetry.append({
                "driver": telem.driver,
                "telemetry": {
                    "distance": telem.distance,
                    "speed": telem.speed,
                    "throttle": telem.throttle,
                    "brake": telem.brake,
                }
            })
        
        # Call Analysis service
        result = await analysis_client.cluster_drivers(
            driver_telemetry,
            n_clusters=min(request.n_clusters, len(driver_telemetry))
        )
        
        return {
            "session_id": request.session_id,
            "clusters": result.get("clusters", []),
            "cluster_descriptions": result.get("cluster_descriptions", {}),
            "explained_variance": result.get("explained_variance", []),
            "metadata": result.get("metadata", {}),
        }
    
    except HTTPException:
        raise
    except NativeAcquisitionError as e:
        # G0: structured 502 for native acquisition failures (review L2-2/L4-1).
        raise HTTPException(status_code=502, detail=e.to_detail())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clustering drivers: {str(e)}"
        )


@router.get("/insights/{session_id}")
async def get_session_insights(
    session_id: str,
    drivers: List[str] = Query(..., description="Driver abbreviations")
):
    """
    Get data-driven insights for a session.
    
    Combines multiple analysis features to provide actionable insights:
    - Identifies similar driving styles
    - Groups drivers by characteristics
    - Highlights outliers
    
    Args:
        session_id: Session identifier
        drivers: List of drivers to analyze
        
    Returns:
        Compiled insights from multiple analysis methods
    """
    insights = {
        "session_id": session_id,
        "drivers": drivers,
        "insights": [],
        "clusters": None,
    }
    
    try:
        # Try to get clustering data if enough drivers
        if len(drivers) >= 3:
            cluster_result = await cluster_driver_styles(
                ClusteringRequest(
                    session_id=session_id,
                    drivers=drivers,
                    n_clusters=min(3, len(drivers))
                )
            )
            insights["clusters"] = cluster_result
            
            # Generate insights from clusters
            for desc_id, description in cluster_result.get("cluster_descriptions", {}).items():
                insights["insights"].append({
                    "type": "cluster",
                    "message": f"Cluster {desc_id}: {description}"
                })
        
        return insights
    
    except Exception as e:
        # Return partial insights even if clustering fails
        insights["insights"].append({
            "type": "error",
            "message": f"Could not generate all insights: {str(e)}"
        })
        return insights

