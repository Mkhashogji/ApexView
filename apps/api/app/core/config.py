from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_TITLE: str = "F1 Engineering API"
    API_VERSION: str = "0.1.0"
    
    # Feature Flags
    LIVE_DATA: bool = True  # Toggle between mock data and FastF1 (enabled for 2025 data)
    
    # FastF1 Settings
    CACHE_DIR: Path = Path("/app/data/cache")  # Docker-friendly path
    PARQUET_DIR: Path = CACHE_DIR / "parquet"
    DEFAULT_SEASON: int = 2025
    DOWNSAMPLE_THRESHOLD: int = 5000  # Max telemetry points before downsampling
    
    # ML Service Settings
    ML_SERVICE_URL: str = "http://ml:8501"
    
    # Mock Data Settings
    MOCK_DATA_DIR: Path = Path(__file__).parent.parent / "fixtures"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure cache directory exists
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.PARQUET_DIR.mkdir(parents=True, exist_ok=True)

# Ensure mock data directory exists
settings.MOCK_DATA_DIR.mkdir(parents=True, exist_ok=True)

