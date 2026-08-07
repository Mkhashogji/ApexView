"""
Corner Analysis Configuration Module

Per-circuit tuning parameters for the v2 deceleration-based corner analysis system.

This module provides:
1. CornerAnalysisConfig dataclass with tunable parameters
2. Circuit-specific overrides for tracks with unique characteristics
3. Default values based on typical F1 telemetry (~5 Hz sampling, ~17m between samples)

Usage:
    from core.corner_config import CornerAnalysisConfig, get_config_for_circuit

    config = get_config_for_circuit("monza")
    threshold = config.braking_decel_threshold
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger("analysis_service.corner_config")


@dataclass
class CornerAnalysisConfig:
    """
    Per-circuit tuning parameters for corner analysis.

    Attributes:
        braking_decel_threshold: Deceleration threshold for heavy braking onset (m/s²)
        trail_braking_threshold: Deceleration threshold for trail braking (m/s²)
        acceleration_threshold: Acceleration threshold for exit detection (m/s²)
        decel_smoothing_window: Smoothing window size (higher for bumpy tracks)
        braking_point_tolerance: Distance tolerance for braking point alignment (meters)
        apex_search_margin: Search window for apex detection (meters)
        exit_speed_recovery_pct: Exit when speed reaches this % of pre-brake speed
        exit_sustained_points: Number of sustained accel points required for exit
        zone_start_speed_pct: Zone start requires both drivers >= this % of peak speed
        sector_validation_tolerance: Tolerance for sector validation (seconds)
        max_exit_search_distance: Maximum distance to search for exit point (meters)
    """

    # Deceleration thresholds (m/s²) - negative values = braking
    braking_decel_threshold: float = -5.0  # Heavy braking onset
    trail_braking_threshold: float = -1.0  # Trail braking threshold
    acceleration_threshold: float = 2.0  # Exit acceleration threshold

    # Smoothing (higher values for bumpy tracks like Singapore, Monaco)
    decel_smoothing_window: int = 5

    # Distance tolerances (meters) - accounts for ~5 Hz telemetry resolution
    braking_point_tolerance: float = 20.0  # ±20m at ~5 Hz
    apex_search_margin: float = 50.0  # Search window around nominal apex

    # Exit detection parameters
    exit_speed_recovery_pct: float = 0.85  # Exit when >= 85% of pre-brake speed
    exit_sustained_points: int = 3  # Sustained acceleration points required
    max_exit_search_distance: float = 200.0  # Maximum exit search distance from apex

    # Zone clamping
    zone_start_speed_pct: float = 0.95  # Both drivers >= 95% peak speed at zone start

    # Validation
    sector_validation_tolerance: float = 0.100  # ±100ms tolerance for sector validation


# Circuit-specific overrides based on track characteristics
CIRCUIT_CONFIGS: Dict[str, CornerAnalysisConfig] = {
    # High-speed tracks with heavy braking
    "monza": CornerAnalysisConfig(
        braking_decel_threshold=-6.0,  # Harder braking due to high speeds
        apex_search_margin=60.0,  # Larger margins for chicanes
    ),
    "spa": CornerAnalysisConfig(
        braking_decel_threshold=-5.5,
        max_exit_search_distance=250.0,  # Longer corners like Pouhon
    ),
    "baku": CornerAnalysisConfig(
        braking_decel_threshold=-6.5,  # Very heavy braking from high speeds
        braking_point_tolerance=25.0,  # More tolerance for street circuit variance
    ),
    "jeddah": CornerAnalysisConfig(
        braking_decel_threshold=-5.5,
        decel_smoothing_window=6,  # Fast, flowing street circuit
    ),
    # Street circuits with technical sections
    "monaco": CornerAnalysisConfig(
        braking_decel_threshold=-4.0,  # Lighter braking, lower speeds
        decel_smoothing_window=7,  # Bumpy surface
        apex_search_margin=40.0,  # Tighter corners, smaller margins
        max_exit_search_distance=150.0,  # Shorter corners
    ),
    "singapore": CornerAnalysisConfig(
        braking_decel_threshold=-4.5,
        decel_smoothing_window=7,  # Bumpy street circuit
        apex_search_margin=45.0,
    ),
    "las_vegas": CornerAnalysisConfig(
        braking_decel_threshold=-5.5,
        braking_point_tolerance=25.0,
    ),
    # Medium-speed circuits
    "rodriguez": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,  # Standard threshold
        decel_smoothing_window=5,  # Smooth surface
    ),
    "interlagos": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        decel_smoothing_window=6,  # Elevation changes
    ),
    "suzuka": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        max_exit_search_distance=300.0,  # Long corners like 130R
    ),
    "silverstone": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        apex_search_margin=55.0,  # Fast, flowing corners
    ),
    # Low-grip or unique circuits
    "qatar": CornerAnalysisConfig(
        braking_decel_threshold=-4.5,  # Lower grip, lighter braking
        decel_smoothing_window=6,
    ),
    "bahrain": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        exit_sustained_points=4,  # More points for sandy conditions
    ),
    "abu_dhabi": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        apex_search_margin=50.0,
    ),
    # =========================================================================
    # Additional circuits (completing 24-circuit 2025 F1 calendar)
    # =========================================================================
    # Australia - Albert Park (Street/Park circuit)
    "albert_park": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        decel_smoothing_window=6,  # Park circuit, some bumps
        apex_search_margin=50.0,
    ),
    # China - Shanghai International Circuit
    "shanghai": CornerAnalysisConfig(
        braking_decel_threshold=-5.5,  # Heavy braking into T14
        apex_search_margin=70.0,  # Long corners like T1-2-3
        max_exit_search_distance=250.0,
    ),
    # Miami International Autodrome
    "miami": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        decel_smoothing_window=7,  # Street circuit, bumpy
        braking_point_tolerance=25.0,
    ),
    # Imola - Autodromo Enzo e Dino Ferrari
    "imola": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        apex_search_margin=50.0,
        decel_smoothing_window=5,
    ),
    # Spain - Circuit de Barcelona-Catalunya
    "barcelona": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        apex_search_margin=55.0,  # High-speed final sector
        max_exit_search_distance=220.0,
    ),
    # Canada - Circuit Gilles Villeneuve (Montreal)
    "gilles_villeneuve": CornerAnalysisConfig(
        braking_decel_threshold=-6.0,  # Heavy braking chicanes
        braking_point_tolerance=25.0,  # Wall of Champions variance
        decel_smoothing_window=5,
    ),
    # Austria - Red Bull Ring
    "red_bull_ring": CornerAnalysisConfig(
        braking_decel_threshold=-5.5,  # Uphill heavy braking
        decel_smoothing_window=5,
        apex_search_margin=50.0,
    ),
    # Hungary - Hungaroring
    "hungaroring": CornerAnalysisConfig(
        braking_decel_threshold=-4.5,  # Twisty, lighter braking
        apex_search_margin=40.0,  # Tighter corners
        max_exit_search_distance=150.0,
    ),
    # Netherlands - Circuit Zandvoort
    "zandvoort": CornerAnalysisConfig(
        braking_decel_threshold=-5.0,
        apex_search_margin=45.0,  # Banked corners
        decel_smoothing_window=5,
    ),
    # USA - Circuit of the Americas (COTA)
    "americas": CornerAnalysisConfig(
        braking_decel_threshold=-5.5,
        decel_smoothing_window=7,  # Notoriously bumpy
        apex_search_margin=55.0,
    ),
}


# Circuit aliases for flexible lookup (country names, city names, abbreviations)
CIRCUIT_ALIASES: Dict[str, str] = {
    # Country names → canonical circuit ID
    "australia": "albert_park",
    "china": "shanghai",
    "spain": "barcelona",
    "canada": "gilles_villeneuve",
    "austria": "red_bull_ring",
    "hungary": "hungaroring",
    "netherlands": "zandvoort",
    "usa": "americas",
    "mexico": "rodriguez",
    "brazil": "interlagos",
    "belgium": "spa",
    "italy": "monza",
    "japan": "suzuka",
    "uk": "silverstone",
    "britain": "silverstone",
    "saudi_arabia": "jeddah",
    "saudi": "jeddah",
    # City/track names → canonical circuit ID
    "melbourne": "albert_park",
    "montreal": "gilles_villeneuve",
    "spielberg": "red_bull_ring",
    "budapest": "hungaroring",
    "austin": "americas",
    "cota": "americas",
    "sao_paulo": "interlagos",
    "marina_bay": "singapore",
    "yas_marina": "abu_dhabi",
    "lusail": "qatar",
    "mexico_city": "rodriguez",
    "emilia_romagna": "imola",
    "catalunya": "barcelona",
    "vegas": "las_vegas",
    "azerbaidjan": "baku",
}


def get_config_for_circuit(circuit_id: str) -> CornerAnalysisConfig:
    """
    Get the appropriate configuration for a circuit.

    Supports direct circuit IDs, country names, city names, and common aliases.
    Falls back to default configuration if circuit-specific config not found.

    Args:
        circuit_id: Circuit identifier (e.g., "monza", "monaco", "australia", "cota")

    Returns:
        CornerAnalysisConfig with appropriate parameters for the circuit
    """
    if not circuit_id:
        logger.debug("No circuit_id provided, using defaults")
        return CornerAnalysisConfig()

    # Normalize circuit_id (lowercase, replace spaces/hyphens)
    normalized_id = circuit_id.lower().replace("-", "_").replace(" ", "_")

    # Direct lookup
    if normalized_id in CIRCUIT_CONFIGS:
        logger.debug(f"Using circuit-specific config for {circuit_id}")
        return CIRCUIT_CONFIGS[normalized_id]

    # Alias lookup
    if normalized_id in CIRCUIT_ALIASES:
        canonical_id = CIRCUIT_ALIASES[normalized_id]
        if canonical_id in CIRCUIT_CONFIGS:
            logger.debug(f"Resolved alias {circuit_id} -> {canonical_id}")
            return CIRCUIT_CONFIGS[canonical_id]

    logger.debug(f"No circuit-specific config for {circuit_id}, using defaults")
    return CornerAnalysisConfig()


def get_all_circuit_ids() -> list:
    """Get list of all configured circuit IDs."""
    return list(CIRCUIT_CONFIGS.keys())


def get_circuit_count() -> int:
    """Get count of configured circuits."""
    return len(CIRCUIT_CONFIGS)
