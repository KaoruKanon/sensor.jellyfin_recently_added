"""Light integration test: exercises the real HA config flow manager end to end
(two-step wizard, duplicate-entry abort), mocking only the network-touching calls
(test_connection, list_users, JellyfinApi.update) so no real Jellyfin server is needed.
"""
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jellyfin_recently_added.const import DOMAIN
from custom_components.jellyfin_recently_added.jellyfin_api import FailedToLogin

CONNECTION_INPUT = {
    "name": "",
    "host": "jf.local",
    "port": 8096,
    "api_key": "api-key",
    "ssl": False,
}

DETAILS_INPUT = {
    "user_id": "admin-id",
    "max": 5,
    "on_deck": False,
    "section_types": ["movies", "tvshows"],
}


@patch(
    "custom_components.jellyfin_recently_added.helpers.JellyfinApi.update",
    new_callable=AsyncMock,
    return_value={"data": {}, "online": True, "libraries": []},
)
@patch(
    "custom_components.jellyfin_recently_added.config_flow.test_connection",
    new_callable=AsyncMock,
)
@patch(
    "custom_components.jellyfin_recently_added.config_flow.list_users",
    new_callable=AsyncMock,
    return_value=[{"id": "admin-id", "name": "root"}],
)
async def test_full_setup_flow_creates_entry(mock_list_users, mock_test_conn, mock_update, hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"

    # Step 1 (connection) succeeds -> moves to step 2 (details), account dropdown populated.
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "details"

    # Step 2 (details) succeeds -> entry created with the resolved user_id.
    result = await hass.config_entries.flow.async_configure(result["flow_id"], DETAILS_INPUT)
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["user_id"] == "admin-id"
    assert result["data"]["host"] == "jf.local"


@patch(
    "custom_components.jellyfin_recently_added.config_flow.test_connection",
    new_callable=AsyncMock,
)
async def test_duplicate_api_key_aborts(mock_test_conn, hass):
    MockConfigEntry(domain=DOMAIN, data={**CONNECTION_INPUT, "api_key": "dup-key"}).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**CONNECTION_INPUT, "api_key": "dup-key"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@patch(
    "custom_components.jellyfin_recently_added.config_flow.test_connection",
    new_callable=AsyncMock,
    side_effect=FailedToLogin("bad credentials"),
)
async def test_connection_failure_shows_error_not_traceback(mock_test_conn, hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], CONNECTION_INPUT)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "failed_to_login"}
