"""Tests for compute_progression_stats — cross-session progression analysis."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.models.dto import PracticeSessionsResponse
from app.services.practice.practice_data_service import compute_progression_stats


# =============================================================================
# Helpers
# =============================================================================


def _make_session_data(best_laps: dict) -> dict:
    """Build a minimal processed-data dict with session_best_laps."""
    return {
        'session_best_laps': best_laps,
        'stints': [],
        'session_info': {},
    }


def _make_best_lap(
    time: float,
    compound: str = 'SOFT',
    tyre_life: int = 3,
    team: str = 'Red Bull Racing',
    source: str = 'fastf1_flag',
) -> dict:
    """Helper to build a session_best_laps entry for one driver."""
    return {
        'session_best_time': time,
        'compound': compound,
        'tyre_life': tyre_life,
        'team': team,
        'source': source,
        'lap_number': 10,
    }


def _mock_sessions_response(sessions: list, year: int = 2025, round_num: int = 1):
    """Build a PracticeSessionsResponse DTO."""
    return PracticeSessionsResponse(
        year=year,
        round_num=round_num,
        sessions=sessions,
    )


# =============================================================================
# Test 1: Traditional weekend (3 sessions) — happy path
# =============================================================================


def test_traditional_weekend_three_sessions():
    """VER and LEC across FP1/FP2/FP3 — verify gaps, sorting, structure."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(91.0, 'MEDIUM'),
        'LEC': _make_best_lap(91.5, 'MEDIUM', team='Ferrari'),
    })
    fp2_data = _make_session_data({
        'VER': _make_best_lap(90.0, 'SOFT'),
        'LEC': _make_best_lap(90.2, 'SOFT', team='Ferrari'),
    })
    fp3_data = _make_session_data({
        'VER': _make_best_lap(89.5, 'SOFT'),
        'LEC': _make_best_lap(89.3, 'SOFT', team='Ferrari'),
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1', 'FP2', 'FP3']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            side_effect=lambda sid, **kw: {
                '2025_1_FP1': fp1_data,
                '2025_1_FP2': fp2_data,
                '2025_1_FP3': fp3_data,
            }[sid],
        ):
            result = await compute_progression_stats(2025, 1)

        assert result['year'] == 2025
        assert result['round_num'] == 1
        assert result['available_sessions'] == ['FP1', 'FP2', 'FP3']
        assert result['is_sprint_weekend'] is False
        assert result['total_drivers'] == 2
        assert len(result['drivers']) == 2

        # Both drivers should have 3 session entries
        for d in result['drivers']:
            assert len(d['sessions']) == 3

        # Fastest driver in FP3 is LEC (89.3), VER (89.5)
        # LEC has gap 0.0 in FP3 — best gap across all sessions is 0.0
        # VER has gap 0.0 in FP1 and FP2 — best gap across all sessions is 0.0
        # Both have min gap = 0.0, so order depends on stable sort

    asyncio.run(_run())


# =============================================================================
# Test 2: Sprint weekend — single session
# =============================================================================


def test_sprint_weekend_single_session():
    """Sprint weekend: only FP1, is_sprint_weekend = True."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(92.0, 'HARD'),
        'NOR': _make_best_lap(92.3, 'HARD', team='McLaren'),
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            return_value=fp1_data,
        ):
            result = await compute_progression_stats(2025, 5)

        assert result['is_sprint_weekend'] is True
        assert result['available_sessions'] == ['FP1']
        assert result['total_drivers'] == 2

        # VER: gap = 0.0, NOR: gap = 0.3
        ver = next(d for d in result['drivers'] if d['driver'] == 'VER')
        nor = next(d for d in result['drivers'] if d['driver'] == 'NOR')
        assert len(ver['sessions']) == 1
        assert ver['sessions'][0]['gap_to_session_best'] == 0.0
        assert nor['sessions'][0]['gap_to_session_best'] == pytest.approx(0.3, abs=1e-3)

    asyncio.run(_run())


# =============================================================================
# Test 3: Gap calculation — session best driver gets 0.000
# =============================================================================


def test_session_best_driver_gets_zero_gap():
    """The fastest driver in each session should have gap_to_session_best = 0.0."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(90.5),
        'HAM': _make_best_lap(91.0, team='Mercedes'),
        'LEC': _make_best_lap(90.5, team='Ferrari'),  # Tied with VER
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            return_value=fp1_data,
        ):
            result = await compute_progression_stats(2025, 1)

        # VER and LEC both posted 90.5 — both should be 0.0
        ver = next(d for d in result['drivers'] if d['driver'] == 'VER')
        lec = next(d for d in result['drivers'] if d['driver'] == 'LEC')
        ham = next(d for d in result['drivers'] if d['driver'] == 'HAM')

        assert ver['sessions'][0]['gap_to_session_best'] == 0.0
        assert lec['sessions'][0]['gap_to_session_best'] == 0.0
        assert ham['sessions'][0]['gap_to_session_best'] == pytest.approx(0.5, abs=1e-3)

    asyncio.run(_run())


# =============================================================================
# Test 4: Variable lineup — driver only in FP1 (rookie sub)
# =============================================================================


def test_variable_lineup_partial_driver():
    """A rookie who only drives FP1 gets only 1 session entry."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(91.0),
        'BEA': _make_best_lap(92.5, team='Red Bull Racing'),  # Rookie
    })
    fp2_data = _make_session_data({
        'VER': _make_best_lap(90.0),
        'PER': _make_best_lap(90.5, team='Red Bull Racing'),  # Regular driver
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1', 'FP2']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            side_effect=lambda sid, **kw: {
                '2025_1_FP1': fp1_data,
                '2025_1_FP2': fp2_data,
            }[sid],
        ):
            result = await compute_progression_stats(2025, 1)

        bea = next(d for d in result['drivers'] if d['driver'] == 'BEA')
        per = next(d for d in result['drivers'] if d['driver'] == 'PER')
        ver = next(d for d in result['drivers'] if d['driver'] == 'VER')

        assert len(bea['sessions']) == 1
        assert bea['sessions'][0]['session'] == 'FP1'
        assert len(per['sessions']) == 1
        assert per['sessions'][0]['session'] == 'FP2'
        assert len(ver['sessions']) == 2

    asyncio.run(_run())


# =============================================================================
# Test 5: Empty sessions — no available data
# =============================================================================


def test_empty_sessions_returns_empty():
    """If no sessions are available, returns empty drivers list."""
    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response([]),
        ):
            result = await compute_progression_stats(2025, 1)

        assert result['drivers'] == []
        assert result['total_drivers'] == 0
        assert result['available_sessions'] == []

    asyncio.run(_run())


# =============================================================================
# Test 6: Session load failure — partial results
# =============================================================================


def test_session_load_failure_partial_results():
    """If one session fails to load, other sessions still produce results."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(91.0),
    })

    async def _mock_load(sid, **kw):
        if '2025_1_FP2' in sid:
            raise Exception("FastF1 timeout")
        return fp1_data

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1', 'FP2']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            side_effect=_mock_load,
        ):
            result = await compute_progression_stats(2025, 1)

        # FP1 data should still be there despite FP2 failure
        assert result['total_drivers'] == 1
        assert result['available_sessions'] == ['FP1', 'FP2']
        ver = result['drivers'][0]
        assert len(ver['sessions']) == 1
        assert ver['sessions'][0]['session'] == 'FP1'

    asyncio.run(_run())


# =============================================================================
# Test 7: Compound and tyre_life propagated correctly
# =============================================================================


def test_compound_and_tyre_life_propagated():
    """Compound and tyre_life from session_best_laps flow through to entries."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(91.0, compound='HARD', tyre_life=12),
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            return_value=fp1_data,
        ):
            result = await compute_progression_stats(2025, 1)

        entry = result['drivers'][0]['sessions'][0]
        assert entry['compound'] == 'HARD'
        assert entry['tyre_life'] == 12
        assert entry['source'] == 'fastf1_flag'
        assert entry['best_lap_time'] == 91.0

    asyncio.run(_run())


# =============================================================================
# Test 8: Session ordering — entries sorted FP1 → FP2 → FP3
# =============================================================================


def test_session_entries_ordered():
    """A driver's sessions should be ordered FP1, FP2, FP3 regardless of load order."""
    fp1_data = _make_session_data({'VER': _make_best_lap(91.0)})
    fp2_data = _make_session_data({'VER': _make_best_lap(90.0)})
    fp3_data = _make_session_data({'VER': _make_best_lap(89.5)})

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1', 'FP2', 'FP3']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            side_effect=lambda sid, **kw: {
                '2025_1_FP1': fp1_data,
                '2025_1_FP2': fp2_data,
                '2025_1_FP3': fp3_data,
            }[sid],
        ):
            result = await compute_progression_stats(2025, 1)

        sessions = [e['session'] for e in result['drivers'][0]['sessions']]
        assert sessions == ['FP1', 'FP2', 'FP3']

    asyncio.run(_run())


# =============================================================================
# Test 9: Driver sorting — ordered by best gap across sessions
# =============================================================================


def test_driver_sorting_by_best_gap():
    """Drivers sorted by their minimum gap_to_session_best across all sessions."""
    fp1_data = _make_session_data({
        'VER': _make_best_lap(90.0),        # Gap: 0.0
        'HAM': _make_best_lap(90.8, team='Mercedes'),  # Gap: 0.8
        'NOR': _make_best_lap(90.5, team='McLaren'),    # Gap: 0.5
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            return_value=fp1_data,
        ):
            result = await compute_progression_stats(2025, 1)

        drivers = [d['driver'] for d in result['drivers']]
        assert drivers == ['VER', 'NOR', 'HAM']

    asyncio.run(_run())


# =============================================================================
# Test 10: All sessions fail — returns empty
# =============================================================================


def test_all_sessions_fail_returns_empty():
    """If all sessions fail to load, returns empty drivers list."""
    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1', 'FP2']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            side_effect=Exception("All sessions failed"),
        ):
            result = await compute_progression_stats(2025, 1)

        assert result['drivers'] == []
        assert result['total_drivers'] == 0
        assert result['is_sprint_weekend'] is False

    asyncio.run(_run())


# =============================================================================
# Test 11: Float guard — gap_to_session_best never negative
# =============================================================================


def test_gap_never_negative():
    """max(0.0, gap) prevents float imprecision from producing negative gaps."""
    # Both drivers at exactly the same time — rounding could theoretically
    # produce a tiny negative gap without the guard
    fp1_data = _make_session_data({
        'VER': _make_best_lap(90.123),
        'LEC': _make_best_lap(90.123, team='Ferrari'),
    })

    async def _run():
        with patch(
            'app.services.practice.practice_data_service.get_available_sessions',
            new_callable=AsyncMock,
            return_value=_mock_sessions_response(['FP1']),
        ), patch(
            'app.services.practice.practice_data_service.get_processed_practice_data',
            new_callable=AsyncMock,
            return_value=fp1_data,
        ):
            result = await compute_progression_stats(2025, 1)

        for d in result['drivers']:
            for entry in d['sessions']:
                assert entry['gap_to_session_best'] >= 0.0

    asyncio.run(_run())
