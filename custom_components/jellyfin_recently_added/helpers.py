from homeassistant.core import HomeAssistant
from .jellyfin_api import JellyfinApi, resolve_user_id

async def setup_client(
    hass: HomeAssistant,
    name: str,
    ssl: bool,
    api_key: str,
    user_id: str,
    user_name: str,
    max: int,
    on_deck: bool,
    host: str,
    port: int,
    section_types: list,
    section_libraries: list,
    exclude_keywords: list,
):
    """Set up (and validate) a Jellyfin client, resolving user_name to a user_id if needed.

    Returns (client, resolved_user_id) — callers that persist config data should
    store the resolved ID rather than the name, so later reloads don't need to
    re-resolve it.
    """
    resolved_user_id = await resolve_user_id(hass, ssl, api_key, host, port, user_id, user_name)
    client = JellyfinApi(hass, name, ssl, api_key, resolved_user_id, max, on_deck, host, port, section_types, section_libraries, exclude_keywords)

    await client.update()
    return client, resolved_user_id
