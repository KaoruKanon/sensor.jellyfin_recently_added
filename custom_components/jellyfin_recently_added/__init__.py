import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_NAME,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL
)

from .const import (
    DOMAIN,
    ALL_SECTION_TYPES,
    CONF_USER_ID,
    CONF_MAX,
    CONF_SECTION_TYPES,
    CONF_SECTION_LIBRARIES,
    CONF_EXCLUDE_KEYWORDS,
    CONF_ON_DECK
)

from .coordinator import JellyfinDataCoordinator
from .helpers import setup_client
from .jellyfin_api import (
    FailedToLogin,
)
from .redirect import ImagesRedirect

PLATFORMS = [
    Platform.SENSOR
]

# Optional configuration.yaml entry point, kept alongside the UI config flow.
# Any block found here is imported into a config entry on startup, so the two
# setup methods (UI and YAML/secrets.yaml) can be used interchangeably.
JELLYFIN_YAML_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default=''): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=8096): cv.port,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_USER_ID): cv.string,
    vol.Optional(CONF_SSL, default=False): cv.boolean,
    vol.Optional(CONF_MAX, default=5): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Optional(CONF_ON_DECK, default=False): cv.boolean,
    vol.Optional(CONF_SECTION_TYPES, default=["movies", "tvshows"]): vol.All(cv.ensure_list, [vol.In(ALL_SECTION_TYPES)]),
    vol.Optional(CONF_SECTION_LIBRARIES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_EXCLUDE_KEYWORDS, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [JELLYFIN_YAML_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Import any jellyfin_recently_added entries found in configuration.yaml."""
    if DOMAIN not in config:
        return True

    for entry_config in config[DOMAIN]:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=entry_config,
            )
        )

    return True

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    try:
        client = await setup_client(
            hass,
            config_entry.data[CONF_NAME],
            config_entry.data[CONF_SSL],
            config_entry.data[CONF_API_KEY],
            config_entry.data[CONF_USER_ID],
            config_entry.data[CONF_MAX],
            config_entry.data[CONF_ON_DECK],
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_PORT],
            config_entry.data.get(CONF_SECTION_TYPES, []),
            config_entry.data.get(CONF_SECTION_LIBRARIES, []),
            config_entry.data.get(CONF_EXCLUDE_KEYWORDS, []),
        )
    except FailedToLogin as err:
        raise ConfigEntryNotReady("Failed to Log-in") from err
    coordinator = JellyfinDataCoordinator(hass, client)

    hass.http.register_view(ImagesRedirect(hass, config_entry))
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Jellyfin config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        del hass.data[DOMAIN][config_entry.entry_id]
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
    return unload_ok

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
