"""HTTP client for ML microservice communication."""
import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings


class MLServiceClient:
    """
    Client for communicating with the ML microservice.
    
    Provides methods to call ML endpoints for lap similarity,
    driver style clustering, and other ML features.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ML service client.
        
        Args:
            base_url: Base URL of ML service (defaults to settings.ML_SERVICE_URL)
        """
        self.base_url = base_url or settings.ML_SERVICE_URL
        self.timeout = 30.0  # 30 second timeout for ML operations
    
    async def calculate_similarity(
        self,
        lap1_data: Dict[str, List[float]],
        lap2_data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        Calculate cosine similarity between two laps.
        
        Args:
            lap1_data: First lap telemetry data
            lap2_data: Second lap telemetry data
            
        Returns:
            Dictionary with similarity score and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/lap-similarity",
                    json={
                        "lap1": lap1_data,
                        "lap2": lap2_data
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error calling ML service similarity endpoint: {e}")
            return {"error": str(e), "similarity": 0.0}
        except Exception as e:
            print(f"Unexpected error in ML service call: {e}")
            return {"error": str(e), "similarity": 0.0}
    
    async def cluster_drivers(
        self,
        telemetry_data: List[Dict[str, Any]],
        n_clusters: int = 3
    ) -> Dict[str, Any]:
        """
        Cluster drivers by driving style using PCA + KMeans.
        
        Args:
            telemetry_data: List of driver telemetry data
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary with cluster labels and PCA projections
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/driver-style-clustering",
                    json={
                        "telemetry_data": telemetry_data,
                        "n_clusters": n_clusters
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error calling ML service clustering endpoint: {e}")
            return {"error": str(e), "labels": [], "projections": []}
        except Exception as e:
            print(f"Unexpected error in ML service call: {e}")
            return {"error": str(e), "labels": [], "projections": []}
    
    async def health_check(self) -> bool:
        """
        Check if ML service is healthy and reachable.
        
        Returns:
            True if ML service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global ML client instance
ml_client = MLServiceClient()

