"""
Data service factory pattern.
Returns appropriate data service based on configuration.
"""

from typing import Union
from app.core.config import settings
from app.services.telemetry.fastf1_client import FastF1Client
from app.services.mock_data import MockDataService


def get_data_service() -> Union[FastF1Client, MockDataService]:
    """
    Factory function to get the appropriate data service.
    
    Returns:
        FastF1Client if LIVE_DATA is True, MockDataService otherwise
    """
    if settings.LIVE_DATA:
        return FastF1Client()
    else:
        return MockDataService()

