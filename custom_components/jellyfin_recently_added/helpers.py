from homeassistant.core import HomeAssistant
from .jellyfin_api import JellyfinApi

async def setup_client(
    hass: HomeAssistant,
    name: str,
    ssl: bool,
    api_key: str,
    user_id: str,
    max: int,
    on_deck: bool,
    host: str,
    port: int,
    section_types: list,
    section_libraries: list,
    exclude_keywords: list,
):
    client = JellyfinApi(hass, name, ssl, api_key, user_id, max, on_deck, host, port, section_types, section_libraries, exclude_keywords)

    await client.update()
    return client
