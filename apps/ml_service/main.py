"""
F1 ML Service - FastAPI microservice for machine learning features.

Provides endpoints for:
- Lap similarity calculation (cosine similarity)
- Driver style clustering (PCA + KMeans)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import __init__ as ml_service
from models.schemas import (
    LapSimilarityRequest,
    LapSimilarityResponse,
    ClusteringRequest,
    ClusteringResponse,
    HealthResponse,
    ErrorResponse,
    DriverCluster,
)
from services.similarity import compute_lap_similarity
from services.clustering import cluster_driving_styles

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
        raise HTTPException(
            status_code=500,
            detail=f"Error clustering drivers: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8501, reload=True)

