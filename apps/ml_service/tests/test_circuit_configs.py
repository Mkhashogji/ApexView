"""
Tests for circuit configuration module.

Tests that all 24 F1 circuits are properly configured with appropriate
parameters and that alias resolution works correctly.
"""

import pytest
from core.corner_config import (
    get_config_for_circuit,
    get_all_circuit_ids,
    get_circuit_count,
    CornerAnalysisConfig,
    CIRCUIT_CONFIGS,
    CIRCUIT_ALIASES,
)


class TestCircuitConfigs:
    """Tests for complete 24-circuit configuration coverage."""

    def test_all_24_circuits_configured(self):
        """Verify all 24 F1 circuits have configurations."""
        assert get_circuit_count() == 24, f"Expected 24 circuits, got {get_circuit_count()}"

    def test_circuit_list_complete(self):
        """Verify specific circuits are present in the 2025 F1 calendar."""
        expected_circuits = [
            "albert_park",      # Australia
            "shanghai",         # China
            "suzuka",           # Japan
            "bahrain",          # Bahrain
            "jeddah",           # Saudi Arabia
            "miami",            # Miami
            "imola",            # Emilia Romagna
            "monaco",           # Monaco
            "barcelona",        # Spain
            "gilles_villeneuve", # Canada
            "red_bull_ring",    # Austria
            "silverstone",      # UK
            "spa",              # Belgium
            "hungaroring",      # Hungary
            "zandvoort",        # Netherlands
            "monza",            # Italy
            "baku",             # Azerbaijan
            "singapore",        # Singapore
            "americas",         # USA (COTA)
            "rodriguez",        # Mexico
            "interlagos",       # Brazil
            "las_vegas",        # Las Vegas
            "qatar",            # Qatar
            "abu_dhabi",        # Abu Dhabi
        ]

        actual_circuits = get_all_circuit_ids()

        for circuit in expected_circuits:
            assert circuit in actual_circuits, f"Missing circuit: {circuit}"

    def test_all_circuits_return_config_instance(self):
        """All configured circuits should return a CornerAnalysisConfig instance."""
        for circuit_id in get_all_circuit_ids():
            config = get_config_for_circuit(circuit_id)
            assert isinstance(config, CornerAnalysisConfig), f"{circuit_id} should return config"


class TestCircuitAliases:
    """Tests for circuit alias resolution."""

    def test_country_name_aliases(self):
        """Country names should resolve to correct circuits."""
        country_mappings = [
            ("australia", "albert_park"),
            ("china", "shanghai"),
            ("spain", "barcelona"),
            ("canada", "gilles_villeneuve"),
            ("austria", "red_bull_ring"),
            ("hungary", "hungaroring"),
            ("netherlands", "zandvoort"),
            ("usa", "americas"),
            ("mexico", "rodriguez"),
            ("brazil", "interlagos"),
            ("belgium", "spa"),
            ("italy", "monza"),
            ("japan", "suzuka"),
            ("uk", "silverstone"),
            ("britain", "silverstone"),
        ]

        for alias, expected_circuit in country_mappings:
            config_alias = get_config_for_circuit(alias)
            config_direct = get_config_for_circuit(expected_circuit)
            assert config_alias == config_direct, f"{alias} should resolve to {expected_circuit}"

    def test_city_name_aliases(self):
        """City/track names should resolve to correct circuits."""
        city_mappings = [
            ("melbourne", "albert_park"),
            ("montreal", "gilles_villeneuve"),
            ("spielberg", "red_bull_ring"),
            ("budapest", "hungaroring"),
            ("austin", "americas"),
            ("cota", "americas"),
            ("sao_paulo", "interlagos"),
            ("marina_bay", "singapore"),
            ("yas_marina", "abu_dhabi"),
            ("lusail", "qatar"),
        ]

        for alias, expected_circuit in city_mappings:
            config_alias = get_config_for_circuit(alias)
            config_direct = get_config_for_circuit(expected_circuit)
            assert config_alias == config_direct, f"{alias} should resolve to {expected_circuit}"

    def test_case_insensitive_lookup(self):
        """Circuit lookup should be case-insensitive."""
        assert get_config_for_circuit("MONZA") == get_config_for_circuit("monza")
        assert get_config_for_circuit("Monaco") == get_config_for_circuit("monaco")
        assert get_config_for_circuit("SILVERSTONE") == get_config_for_circuit("silverstone")
        assert get_config_for_circuit("Spa") == get_config_for_circuit("spa")

    def test_hyphen_and_space_normalization(self):
        """Hyphens and spaces should be normalized to underscores."""
        assert get_config_for_circuit("albert-park") == get_config_for_circuit("albert_park")
        assert get_config_for_circuit("albert park") == get_config_for_circuit("albert_park")
        assert get_config_for_circuit("red-bull-ring") == get_config_for_circuit("red_bull_ring")
        assert get_config_for_circuit("red bull ring") == get_config_for_circuit("red_bull_ring")

    def test_unknown_circuit_returns_default(self):
        """Unknown circuit should return default configuration."""
        config = get_config_for_circuit("unknown_track_xyz")
        default = CornerAnalysisConfig()

        assert config.braking_decel_threshold == default.braking_decel_threshold
        assert config.decel_smoothing_window == default.decel_smoothing_window
        assert config.apex_search_margin == default.apex_search_margin

    def test_empty_circuit_id_returns_default(self):
        """Empty or None circuit_id should return default config."""
        default = CornerAnalysisConfig()

        config_empty = get_config_for_circuit("")
        assert config_empty.braking_decel_threshold == default.braking_decel_threshold

        # Note: get_config_for_circuit handles None gracefully


class TestCircuitSpecificThresholds:
    """Tests for circuit-specific threshold values."""

    def test_monza_has_heavy_braking_threshold(self):
        """Monza should have heavier braking threshold (lower value) than default."""
        monza = get_config_for_circuit("monza")
        default = CornerAnalysisConfig()

        # Monza should have more negative threshold (heavier braking)
        assert monza.braking_decel_threshold < default.braking_decel_threshold
        assert monza.braking_decel_threshold == -6.0

    def test_monaco_has_light_braking_threshold(self):
        """Monaco should have lighter braking threshold (closer to zero) than default."""
        monaco = get_config_for_circuit("monaco")
        default = CornerAnalysisConfig()

        # Monaco should have less negative threshold (lighter braking)
        assert monaco.braking_decel_threshold > default.braking_decel_threshold
        assert monaco.braking_decel_threshold == -4.0

    def test_baku_has_very_heavy_braking(self):
        """Baku should have very heavy braking threshold for T1."""
        baku = get_config_for_circuit("baku")
        assert baku.braking_decel_threshold == -6.5

    def test_street_circuits_have_higher_smoothing(self):
        """Street circuits should have higher smoothing for bumpy surfaces."""
        street_circuits = ["monaco", "singapore", "miami"]

        for circuit in street_circuits:
            config = get_config_for_circuit(circuit)
            assert config.decel_smoothing_window >= 6, (
                f"{circuit} smoothing ({config.decel_smoothing_window}) should be >= 6"
            )

    def test_high_speed_circuits_have_longer_exit_search(self):
        """High-speed circuits should have longer exit search distance."""
        long_corner_circuits = ["spa", "suzuka", "shanghai"]

        for circuit in long_corner_circuits:
            config = get_config_for_circuit(circuit)
            assert config.max_exit_search_distance >= 250.0, (
                f"{circuit} should have max_exit_search_distance >= 250m"
            )

    def test_tight_circuits_have_smaller_apex_margin(self):
        """Tight circuits like Monaco and Hungaroring should have smaller apex search margins."""
        tight_circuits = ["monaco", "hungaroring"]

        for circuit in tight_circuits:
            config = get_config_for_circuit(circuit)
            assert config.apex_search_margin <= 45.0, (
                f"{circuit} should have apex_search_margin <= 45m"
            )


class TestConfigDataclassDefaults:
    """Tests for CornerAnalysisConfig dataclass default values."""

    def test_default_braking_threshold(self):
        """Default braking threshold should be -5.0 m/s²."""
        config = CornerAnalysisConfig()
        assert config.braking_decel_threshold == -5.0

    def test_default_trail_braking_threshold(self):
        """Default trail braking threshold should be -1.0 m/s²."""
        config = CornerAnalysisConfig()
        assert config.trail_braking_threshold == -1.0

    def test_default_acceleration_threshold(self):
        """Default acceleration threshold should be 2.0 m/s²."""
        config = CornerAnalysisConfig()
        assert config.acceleration_threshold == 2.0

    def test_default_smoothing_window(self):
        """Default smoothing window should be 5."""
        config = CornerAnalysisConfig()
        assert config.decel_smoothing_window == 5

    def test_default_apex_search_margin(self):
        """Default apex search margin should be 50.0 meters."""
        config = CornerAnalysisConfig()
        assert config.apex_search_margin == 50.0

    def test_default_exit_speed_recovery(self):
        """Default exit speed recovery should be 85%."""
        config = CornerAnalysisConfig()
        assert config.exit_speed_recovery_pct == 0.85

    def test_default_sector_validation_tolerance(self):
        """Default sector validation tolerance should be 100ms."""
        config = CornerAnalysisConfig()
        assert config.sector_validation_tolerance == 0.100


class TestConfigIntegrity:
    """Tests for configuration integrity and consistency."""

    def test_all_configs_have_valid_braking_threshold(self):
        """All circuits should have negative braking thresholds."""
        for circuit_id in get_all_circuit_ids():
            config = get_config_for_circuit(circuit_id)
            assert config.braking_decel_threshold < 0, (
                f"{circuit_id} braking threshold should be negative"
            )

    def test_all_configs_have_valid_smoothing_window(self):
        """All circuits should have smoothing window >= 3."""
        for circuit_id in get_all_circuit_ids():
            config = get_config_for_circuit(circuit_id)
            assert config.decel_smoothing_window >= 3, (
                f"{circuit_id} smoothing window should be >= 3"
            )

    def test_all_configs_have_valid_exit_recovery(self):
        """All circuits should have exit recovery percentage between 0 and 1."""
        for circuit_id in get_all_circuit_ids():
            config = get_config_for_circuit(circuit_id)
            assert 0 < config.exit_speed_recovery_pct <= 1, (
                f"{circuit_id} exit recovery should be between 0 and 1"
            )

    def test_all_configs_have_positive_apex_margin(self):
        """All circuits should have positive apex search margin."""
        for circuit_id in get_all_circuit_ids():
            config = get_config_for_circuit(circuit_id)
            assert config.apex_search_margin > 0, (
                f"{circuit_id} apex margin should be positive"
            )
