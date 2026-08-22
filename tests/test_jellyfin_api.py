"""Unit tests for the connection/listing/resolution helpers in jellyfin_api.py.

These don't need a real Home Assistant instance: the only thing they call on
`hass` is async_add_executor_job, so a tiny fake stands in for it, and requests_mock
intercepts the underlying `requests` calls instead of hitting a real server.
"""
import pytest

from custom_components.jellyfin_recently_added.jellyfin_api import (
    FailedToLogin,
    list_users,
    resolve_user_id,
    # Aliased: an unaliased `test_connection` import would be collected by
    # pytest as a test itself (its name matches test_*), and fail since its
    # real parameters (ssl, api_key, host, port) aren't fixtures.
    test_connection as jf_test_connection,
)


class FakeHass:
    async def async_add_executor_job(self, func, *args):
        return func(*args)


@pytest.fixture
def fake_hass():
    return FakeHass()


USERS_PAYLOAD = [
    {"Id": "admin-id", "Name": "root", "Policy": {"IsAdministrator": True}},
    {"Id": "user-id", "Name": "kaoru", "Policy": {"IsAdministrator": False}},
]


async def test_connection_succeeds(fake_hass, requests_mock):
    requests_mock.get("http://jf.local:8096/System/Info", json={"Id": "server-1"})
    await jf_test_connection(fake_hass, False, "api-key", "jf.local", 8096)


async def test_connection_raises_on_http_error(fake_hass, requests_mock):
    requests_mock.get("http://jf.local:8096/System/Info", status_code=401)
    with pytest.raises(FailedToLogin):
        await jf_test_connection(fake_hass, False, "bad-key", "jf.local", 8096)


async def test_list_users_returns_parsed_accounts(fake_hass, requests_mock):
    requests_mock.get("http://jf.local:8096/Users", json=USERS_PAYLOAD)
    users = await list_users(fake_hass, False, "api-key", "jf.local", 8096)
    assert users == [
        {"id": "admin-id", "name": "root"},
        {"id": "user-id", "name": "kaoru"},
    ]


async def test_list_users_returns_empty_on_error_instead_of_raising(fake_hass, requests_mock):
    # A non-admin API key can't list every account — this must not block setup.
    requests_mock.get("http://jf.local:8096/Users", status_code=403)
    assert await list_users(fake_hass, False, "api-key", "jf.local", 8096) == []


async def test_resolve_user_id_prefers_explicit_id(fake_hass, requests_mock):
    # No HTTP call should happen at all when user_id is already given.
    resolved = await resolve_user_id(fake_hass, False, "api-key", "jf.local", 8096, "explicit-id", "root")
    assert resolved == "explicit-id"


async def test_resolve_user_id_looks_up_by_name_case_insensitively(fake_hass, requests_mock):
    requests_mock.get("http://jf.local:8096/Users", json=USERS_PAYLOAD)
    resolved = await resolve_user_id(fake_hass, False, "api-key", "jf.local", 8096, None, "ROOT")
    assert resolved == "admin-id"


async def test_resolve_user_id_raises_when_name_not_found(fake_hass, requests_mock):
    requests_mock.get("http://jf.local:8096/Users", json=USERS_PAYLOAD)
    with pytest.raises(FailedToLogin):
        await resolve_user_id(fake_hass, False, "api-key", "jf.local", 8096, None, "nobody")


async def test_resolve_user_id_raises_when_neither_given(fake_hass, requests_mock):
    with pytest.raises(FailedToLogin):
        await resolve_user_id(fake_hass, False, "api-key", "jf.local", 8096, None, None)
