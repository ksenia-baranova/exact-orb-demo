"""Pure admission checks before the build route owns terminal permit release."""

from __future__ import annotations

import asyncio
from dataclasses import replace

import pytest

from exact_orb.http_api.admission import (
    AdmissionController, AdmissionPermitError, AdmissionRejection, BuildPermit,
)
from tests.http_api.admission_cases import SmallLimiterPolicy, WindowLimit


@pytest.mark.asyncio
@pytest.mark.parametrize("bucket,method,code,detail", (
    ("session_create_ip", "reserve_session_create", "SESSION_CREATE_RATE_LIMITED", "IP_HOURLY_LIMIT"),
    ("place_search_ip", "reserve_place_search", "PLACE_SEARCH_RATE_LIMITED", "IP_MINUTE_LIMIT"),
))
async def test_late_rejection_does_not_shift_single_bucket_expiry(
    bucket: str, method: str, code: str, detail: str, scheduler,
) -> None:
    policy = replace(SmallLimiterPolicy(), **{bucket: WindowLimit(1, 7)})
    controller = AdmissionController(policy=policy, now=scheduler.now)
    reserve = getattr(controller, method)
    assert await reserve(client_ip="127.0.0.1") is None
    await scheduler.advance(3)
    rejected = await reserve(client_ip="127.0.0.1")
    assert isinstance(rejected, AdmissionRejection)
    assert (rejected.code, rejected.detail_code, rejected.retry_after) == (code, detail, 4)
    await scheduler.advance(4)
    assert await reserve(client_ip="127.0.0.1") is None


@pytest.mark.asyncio
async def test_rate_precedes_capacity_and_capacity_refusal_spends_no_window(scheduler) -> None:
    rule = WindowLimit(5, 7)
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=rule, build_session_daily=rule,
        build_ip_hourly=rule, build_ip_daily=rule,
    )
    controller = AdmissionController(policy=policy, now=scheduler.now)
    permits = [await controller.reserve_build(session_id="A", client_ip="127.0.0.1")
               for _ in range(5)]
    assert all(isinstance(permit, BuildPermit) for permit in permits)
    assert controller.active_build_count == 5

    rate = await controller.reserve_build(session_id="A", client_ip="127.0.0.1")
    assert isinstance(rate, AdmissionRejection)
    assert (rate.code, rate.detail_code, rate.retry_after) == (
        "BUILD_SESSION_RATE_LIMITED", "SESSION_DAILY_LIMIT", 7,
    )
    await scheduler.advance(7)
    capacity = await controller.reserve_build(session_id="A", client_ip="127.0.0.1")
    assert isinstance(capacity, AdmissionRejection)
    assert (capacity.code, capacity.detail_code, capacity.retry_after,
            capacity.status_code) == ("BUILD_CAPACITY_EXHAUSTED", None, 1, 503)
    assert controller.active_build_count == 5

    await permits[0].release()
    admitted = await controller.reserve_build(session_id="A", client_ip="127.0.0.1")
    assert isinstance(admitted, BuildPermit)
    assert controller.active_build_count == 5
    with pytest.raises(AdmissionPermitError):
        await permits[0].release()
    for permit in (*permits[1:], admitted):
        await permit.release()
    assert controller.active_build_count == 0


@pytest.mark.asyncio
async def test_two_concurrent_reservations_compete_for_one_rate_slot(scheduler) -> None:
    rule = WindowLimit(1, 7)
    policy = replace(
        SmallLimiterPolicy(),
        build_session_hourly=rule, build_session_daily=rule,
        build_ip_hourly=rule, build_ip_daily=rule,
    )
    controller = AdmissionController(policy=policy, now=scheduler.now)
    barrier = asyncio.Barrier(3)

    async def compete() -> BuildPermit | AdmissionRejection:
        await barrier.wait()
        return await controller.reserve_build(session_id="A", client_ip="127.0.0.1")

    tasks = [asyncio.create_task(compete()) for _ in range(2)]
    await asyncio.wait_for(barrier.wait(), timeout=1)
    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=1)
    permits = [result for result in results if isinstance(result, BuildPermit)]
    rejections = [result for result in results if isinstance(result, AdmissionRejection)]
    assert len(permits) == len(rejections) == 1
    assert rejections[0].code == "BUILD_SESSION_RATE_LIMITED"
    assert controller.active_build_count == 1
    await permits[0].release()


@pytest.mark.asyncio
async def test_later_ip_daily_window_dominates_and_expired_keys_are_pruned(scheduler) -> None:
    policy = SmallLimiterPolicy()
    controller = AdmissionController(policy=policy, now=scheduler.now)
    first = await controller.reserve_build(session_id="A", client_ip="127.0.0.1")
    second = await controller.reserve_build(session_id="A", client_ip="127.0.0.1")
    assert isinstance(first, BuildPermit) and isinstance(second, BuildPermit)
    await scheduler.advance(11)
    third = await controller.reserve_build(session_id="B", client_ip="127.0.0.1")
    fourth = await controller.reserve_build(session_id="B", client_ip="127.0.0.1")
    assert isinstance(third, BuildPermit) and isinstance(fourth, BuildPermit)
    await scheduler.advance(1)
    # Session B's hourly window opens at 18; IP's daily window opens at 29.
    rejected = await controller.reserve_build(session_id="B", client_ip="127.0.0.1")
    assert isinstance(rejected, AdmissionRejection)
    assert (rejected.code, rejected.detail_code, rejected.retry_after) == (
        "BUILD_IP_RATE_LIMITED", "IP_DAILY_LIMIT", 17,
    )
    for permit in (first, second, third, fourth):
        await permit.release()
    await scheduler.advance(29)
    fresh = await controller.reserve_build(session_id="C", client_ip="127.0.0.2")
    assert isinstance(fresh, BuildPermit)
    assert controller.active_bucket_count <= 4
    await fresh.release()
