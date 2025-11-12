"""Parquet-based caching layer for F1 telemetry data."""
import hashlib
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import Optional
from app.core.config import settings


class ParquetCache:
    """
    Read-through/write-through Parquet cache for F1 data.
    
    Provides fast access to telemetry and lap data by caching
    DataFrames in Parquet format.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize ParquetCache with cache directory."""
        self.cache_dir = cache_dir or settings.PARQUET_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_key(self, session_id: str, data_type: str, **kwargs) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            session_id: Session identifier (e.g., "2024_1_Qualifying")
            data_type: Type of data ("laps", "telemetry", "delta")
            **kwargs: Additional parameters for key generation
            
        Returns:
            Cache key string
        """
        # Create deterministic key from parameters
        key_parts = [session_id, data_type]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, list):
                key_parts.append(f"{k}={'_'.join(sorted(v))}")
            else:
                key_parts.append(f"{k}={v}")
        
        key_string = "_".join(key_parts)
        # Use hash for long keys
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{data_type}_{key_hash}"
        
        # Sanitize for filesystem
        safe_key = key_string.replace("/", "_").replace("\\", "_")
        return safe_key
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{key}.parquet"
    
    def read(self, session_id: str, data_type: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        Read DataFrame from Parquet cache if it exists.
        
        Args:
            session_id: Session identifier
            data_type: Type of data to read
            **kwargs: Additional cache key parameters
            
        Returns:
            Cached DataFrame or None if not found
        """
        key = self._generate_key(session_id, data_type, **kwargs)
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                df = pq.read_table(cache_path).to_pandas()
                return df
            except Exception as e:
                print(f"Error reading cache {key}: {e}")
                return None
        
        return None
    
    def write(
        self,
        data: pd.DataFrame,
        session_id: str,
        data_type: str,
        **kwargs
    ) -> bool:
        """
        Write DataFrame to Parquet cache.
        
        Args:
            data: DataFrame to cache
            session_id: Session identifier
            data_type: Type of data being cached
            **kwargs: Additional cache key parameters
            
        Returns:
            True if write succeeded, False otherwise
        """
        if data is None or data.empty:
            return False
        
        key = self._generate_key(session_id, data_type, **kwargs)
        cache_path = self._get_cache_path(key)
        
        try:
            # Write with compression for space efficiency
            data.to_parquet(
                cache_path,
                engine='pyarrow',
                compression='snappy',
                index=False
            )
            return True
        except Exception as e:
            print(f"Error writing cache {key}: {e}")
            return False
    
    def clear(self, session_id: Optional[str] = None) -> int:
        """
        Clear cache entries.
        
        Args:
            session_id: If provided, only clear caches for this session.
                       If None, clear all caches.
        
        Returns:
            Number of cache files deleted
        """
        deleted = 0
        
        if session_id:
            # Clear specific session caches
            pattern = f"{session_id}_*.parquet"
            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
                deleted += 1
        else:
            # Clear all caches
            for cache_file in self.cache_dir.glob("*.parquet"):
                cache_file.unlink()
                deleted += 1
        
        return deleted
    
    def get_cache_size(self) -> int:
        """
        Get total size of cached data in bytes.
        
        Returns:
            Total cache size in bytes
        """
        total_size = 0
        for cache_file in self.cache_dir.glob("*.parquet"):
            total_size += cache_file.stat().st_size
        return total_size


# Global cache instance
parquet_cache = ParquetCache()

