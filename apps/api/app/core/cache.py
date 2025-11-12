import fastf1
from app.core.config import settings


def enable_cache():
    """Enable FastF1 cache."""
    fastf1.Cache.enable_cache(str(settings.CACHE_DIR))


def clear_cache():
    """Clear FastF1 cache."""
    import shutil
    if settings.CACHE_DIR.exists():
        shutil.rmtree(settings.CACHE_DIR)
        settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)

