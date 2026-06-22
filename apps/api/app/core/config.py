from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Literal


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

    # G0 — Honest Acquisition. "native" serves telemetry from the dual-stream
    # native acquisition layer (real car samples only, provenance-tagged);
    # "legacy" keeps the pre-G0 merged get_telemetry() path, retained SOLELY
    # for the A/B harness and marked for removal at a later cleanup gate.
    # Literal-typed (continuation review L4-3): a typo'd env value fails at
    # startup instead of silently dispatching native.
    ACQUISITION_MODE: Literal["native", "legacy"] = "native"
    
    # Analysis Service Settings
    ANALYSIS_SERVICE_URL: str = "http://analysis:8501"
    
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

