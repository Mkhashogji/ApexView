"""
G0 continuation — dispatcher, route-translation and isolation tests.

Closes the review's contract-coverage gaps (findings L5-1/2/3/6):
- the acquisition dispatcher routes native/legacy/default correctly,
- NativeAcquisitionError propagates through the native path and is translated
  to a structured 502 at the routes (and never swallowed into []),
- /telemetry/meta honours mock-mode 501 AND env-legacy 501 (isolation),
- the native Parquet keyspace is provably disjoint from legacy.

Route handlers are invoked directly (no TestClient — keeps the suite free of
the httpx test dependency); HTTPException is asserted as the contract.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.services.telemetry.fastf1_client import (
    FastF1Client,
    NATIVE_TELEMETRY_DATA_TYPE,
)
from app.services.telemetry.native_acquisition import NativeAcquisitionError
import app.routes.telemetry as telemetry_routes


# =============================================================================
# Dispatcher matrix (review L5-1)
# =============================================================================

class TestAcquisitionDispatcher:
    def _client_with_sentinels(self):
        client = FastF1Client()
        client._get_telemetry_native = AsyncMock(return_value="NATIVE")
        client._get_telemetry_legacy = AsyncMock(return_value="LEGACY")
        client._get_delta_analysis_native = AsyncMock(return_value="D_NATIVE")
        client._get_delta_analysis_legacy = AsyncMock(return_value="D_LEGACY")
        return client

    def test_explicit_native_routes_native(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "legacy")
        client = self._client_with_sentinels()
        result = asyncio.run(client.get_telemetry("s", ["PIA"], acquisition="native"))
        assert result == "NATIVE"
        client._get_telemetry_legacy.assert_not_called()

    def test_explicit_legacy_routes_legacy(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "native")
        client = self._client_with_sentinels()
        result = asyncio.run(client.get_telemetry("s", ["PIA"], acquisition="legacy"))
        assert result == "LEGACY"
        client._get_telemetry_native.assert_not_called()

    def test_none_falls_back_to_settings_native(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "native")
        client = self._client_with_sentinels()
        assert asyncio.run(client.get_telemetry("s", ["PIA"])) == "NATIVE"

    def test_none_falls_back_to_settings_legacy(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "legacy")
        client = self._client_with_sentinels()
        assert asyncio.run(client.get_telemetry("s", ["PIA"])) == "LEGACY"

    def test_delta_dispatcher_same_matrix(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "native")
        client = self._client_with_sentinels()
        assert asyncio.run(client.get_delta_analysis("s", "PIA", ["RUS"])) == "D_NATIVE"
        assert asyncio.run(
            client.get_delta_analysis("s", "PIA", ["RUS"], acquisition="legacy")) == "D_LEGACY"


# =============================================================================
# Error propagation + route translation (review L5-2)
# =============================================================================

class TestErrorPropagation:
    def test_native_error_propagates_not_swallowed(self, monkeypatch):
        """The native path must RAISE on acquisition failure — never return []
        the way legacy does (ground rule 4 / no silent fallback)."""
        client = FastF1Client()
        import app.services.telemetry.fastf1_client as fc

        def boom(*a, **k):
            raise NativeAcquisitionError("get_car_data", "stream offline", "PIA", "s")

        monkeypatch.setattr(fc, "acquire_native_bundle", boom)
        monkeypatch.setattr(
            client, "_select_fastest_valid_lap", lambda *a, **k: object())
        monkeypatch.setattr(fc.fastf1, "get_session",
                            lambda *a, **k: MagicMock(load=lambda: None, laps=MagicMock()))
        with pytest.raises(NativeAcquisitionError) as exc:
            asyncio.run(client._get_telemetry_native("2025_2_Qualifying", ["PIA"],
                                                     session_part="Q3"))
        assert exc.value.stage == "get_car_data"

    def test_unexpected_exception_wrapped_structured(self, monkeypatch):
        """Review L4-2: ANY unexpected native-path exception wraps into
        NativeAcquisitionError('unexpected') — exhaustive 502 translation."""
        client = FastF1Client()
        import app.services.telemetry.fastf1_client as fc

        def explode(*a, **k):
            raise RuntimeError("pandas internals")

        monkeypatch.setattr(fc.fastf1, "get_session", explode)
        with pytest.raises(NativeAcquisitionError) as exc:
            asyncio.run(client._get_telemetry_native("2025_2_Qualifying", ["PIA"],
                                                     session_part="Q3"))
        assert exc.value.stage in ("load_session", "unexpected")

    def test_route_translates_to_structured_502(self, monkeypatch):
        class FailingService:
            async def get_telemetry(self, *a, **k):
                raise NativeAcquisitionError("get_car_data", "offline", "PIA", "s")

        monkeypatch.setattr(telemetry_routes, "get_data_service", lambda: FailingService())
        with pytest.raises(HTTPException) as exc:
            asyncio.run(telemetry_routes.get_telemetry(
                session="s", drivers=["PIA"], lap_type="fastest",
                downsample=True, session_part="Q3", acquisition="native"))
        assert exc.value.status_code == 502
        assert exc.value.detail["error"] == "native_acquisition_failed"
        assert exc.value.detail["driver"] == "PIA"

    def test_delta_route_translates_502(self, monkeypatch):
        class FailingService:
            async def get_delta_analysis(self, *a, **k):
                raise NativeAcquisitionError("get_pos_data", "offline", "RUS", "s")

        monkeypatch.setattr(telemetry_routes, "get_data_service", lambda: FailingService())
        with pytest.raises(HTTPException) as exc:
            asyncio.run(telemetry_routes.get_delta_analysis(
                session="s", reference_driver="PIA", compare_drivers=["RUS"],
                session_part="Q3", acquisition="native"))
        assert exc.value.status_code == 502
        assert exc.value.detail["error"] == "native_acquisition_failed"


# =============================================================================
# /telemetry/meta route guards (review L5-3 + L3-1 env-legacy isolation)
# =============================================================================

class TestMetaRouteGuards:
    def test_env_legacy_returns_501(self, monkeypatch):
        """Env-legacy rollback must not run native acquisition server-side."""
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "legacy")
        with pytest.raises(HTTPException) as exc:
            asyncio.run(telemetry_routes.get_telemetry_meta(
                session="s", drivers=["PIA"], session_part="Q3"))
        assert exc.value.status_code == 501
        assert exc.value.detail["error"] == "native_meta_unavailable"
        assert "legacy" in exc.value.detail["reason"]

    def test_mock_service_returns_501(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "native")

        class NoMetaService:  # MockDataService shape: no get_telemetry_meta
            pass

        monkeypatch.setattr(telemetry_routes, "get_data_service", lambda: NoMetaService())
        with pytest.raises(HTTPException) as exc:
            asyncio.run(telemetry_routes.get_telemetry_meta(
                session="s", drivers=["PIA"], session_part="Q3"))
        assert exc.value.status_code == 501
        assert "mock" in exc.value.detail["reason"]

    def test_meta_200_path(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "native")

        class GoodService:
            async def get_telemetry_meta(self, *a, **k):
                return [{"driver": "PIA", "lapNumber": 19, "gaps": [], "meta": {}}]

        monkeypatch.setattr(telemetry_routes, "get_data_service", lambda: GoodService())
        result = asyncio.run(telemetry_routes.get_telemetry_meta(
            session="s", drivers=["PIA"], session_part="Q3"))
        assert result[0]["driver"] == "PIA"

    def test_meta_translates_502(self, monkeypatch):
        monkeypatch.setattr(settings, "ACQUISITION_MODE", "native")

        class FailingService:
            async def get_telemetry_meta(self, *a, **k):
                raise NativeAcquisitionError("load_session", "no such round", session="s")

        monkeypatch.setattr(telemetry_routes, "get_data_service", lambda: FailingService())
        with pytest.raises(HTTPException) as exc:
            asyncio.run(telemetry_routes.get_telemetry_meta(
                session="s", drivers=["PIA"], session_part="Q3"))
        assert exc.value.status_code == 502


# =============================================================================
# Cache keyspace disjointness (review L5-6)
# =============================================================================

class TestCacheKeyspace:
    def test_native_data_type_disjoint_from_legacy(self):
        assert NATIVE_TELEMETRY_DATA_TYPE != "telemetry"
        assert NATIVE_TELEMETRY_DATA_TYPE.startswith("telemetry_native")

    def test_native_read_uses_versioned_key(self, monkeypatch):
        """The native cache read must query the versioned data_type — a
        regression to "telemetry" would serve merged-frame arrays on the
        native path with both A/B heads looking 'identical'."""
        client = FastF1Client()
        client.cache = MagicMock()
        client.cache.read.return_value = None
        import app.services.telemetry.fastf1_client as fc

        def stop(*a, **k):  # halt after the cache read — network not needed
            raise RuntimeError("stop-after-cache")

        monkeypatch.setattr(fc.fastf1, "get_session", stop)
        with pytest.raises(NativeAcquisitionError):
            asyncio.run(client._get_telemetry_native("2025_2_Qualifying", ["PIA"]))
        client.cache.read.assert_called_once()
        args, kwargs = client.cache.read.call_args
        assert args[1] == NATIVE_TELEMETRY_DATA_TYPE
