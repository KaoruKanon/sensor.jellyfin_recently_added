from typing import Any
import logging
import voluptuous as vol

from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    ConstantSelector,
    ConstantSelectorConfig
)
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import (
    CONF_API_KEY,
    CONF_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL
)

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    CONF_USER_ID,
    CONF_MAX,
    CONF_SECTION_TYPES,
    ALL_SECTION_TYPES,
    CONF_SECTION_LIBRARIES,
    CONF_EXCLUDE_KEYWORDS,
    CONF_SECTION_LIBRARIES_LABEL,
    CONF_EXCLUDE_KEYWORDS_LABEL,
    CONF_ON_DECK
)

from .helpers import setup_client
from .jellyfin_api import (
    FailedToLogin,
)
from .options_flow import JellyfinOptionFlow

_LOGGER = logging.getLogger(__name__)

JELLYFIN_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default=''): vol.All(str),
    vol.Required(CONF_HOST, default='localhost'): vol.All(str),
    vol.Required(CONF_PORT, default=8096): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Required(CONF_API_KEY): vol.All(str),
    vol.Required(CONF_USER_ID): vol.All(str),
    vol.Optional(CONF_SSL, default=False): vol.All(bool),
    vol.Optional(CONF_MAX, default=5): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Optional(CONF_ON_DECK, default=False): vol.All(bool),
    vol.Optional(CONF_SECTION_TYPES, default={"movies", "tvshows"}): SelectSelector(SelectSelectorConfig(options=ALL_SECTION_TYPES, mode=SelectSelectorMode.DROPDOWN ,multiple=True)),
    vol.Optional(CONF_SECTION_LIBRARIES + "_label"): ConstantSelector(ConstantSelectorConfig(value=CONF_SECTION_LIBRARIES_LABEL)),
    vol.Optional(CONF_SECTION_LIBRARIES): TextSelector(TextSelectorConfig(multiple=True, multiline=False)),
    vol.Optional(CONF_EXCLUDE_KEYWORDS + "_label"): ConstantSelector(ConstantSelectorConfig(value=CONF_EXCLUDE_KEYWORDS_LABEL)),
    vol.Optional(CONF_EXCLUDE_KEYWORDS): TextSelector(TextSelectorConfig(multiple=True, multiline=False)),
})

class JellyfinConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for the Jellyfin integration."""
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> JellyfinOptionFlow:
        return JellyfinOptionFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        errors = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_API_KEY: user_input[CONF_API_KEY]})
            try:
                await setup_client(
                    self.hass,
                    user_input[CONF_NAME],
                    user_input[CONF_SSL],
                    user_input[CONF_API_KEY],
                    user_input[CONF_USER_ID],
                    user_input[CONF_MAX],
                    user_input[CONF_ON_DECK],
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input.get(CONF_SECTION_TYPES, []),
                    user_input.get(CONF_SECTION_LIBRARIES, []),
                    user_input.get(CONF_EXCLUDE_KEYWORDS, []),
                )
            except FailedToLogin as err:
                errors = {'base': 'failed_to_login'}
            else:
                return self.async_create_entry(title=user_input[CONF_NAME] if len(user_input[CONF_NAME]) > 0 else DEFAULT_NAME, data=user_input)

        schema = self.add_suggested_values_to_schema(JELLYFIN_SCHEMA, user_input)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            try:
                await setup_client(
                    self.hass,
                    user_input[CONF_NAME],
                    user_input[CONF_SSL],
                    user_input[CONF_API_KEY],
                    user_input[CONF_USER_ID],
                    user_input[CONF_MAX],
                    user_input[CONF_ON_DECK],
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input.get(CONF_SECTION_TYPES, []),
                    user_input.get(CONF_SECTION_LIBRARIES, []),
                    user_input.get(CONF_EXCLUDE_KEYWORDS, []),
                )
            except FailedToLogin as err:
                errors = {'base': 'failed_to_login'}
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **user_input},
                    reason="reconfigure_successful"
                )

        schema = self.add_suggested_values_to_schema(JELLYFIN_SCHEMA, entry.data)
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    async def async_step_import(self, import_config: dict[str, Any]) -> ConfigFlowResult:
        """Handle import of a jellyfin_recently_added block from configuration.yaml.

        Re-runs on every restart, so configuration.yaml (and secrets.yaml)
        stays the source of truth for entries created this way: an existing
        entry with the same API key gets its data refreshed instead of
        being duplicated or ignored.
        """
        try:
            await setup_client(
                self.hass,
                import_config[CONF_NAME],
                import_config[CONF_SSL],
                import_config[CONF_API_KEY],
                import_config[CONF_USER_ID],
                import_config[CONF_MAX],
                import_config[CONF_ON_DECK],
                import_config[CONF_HOST],
                import_config[CONF_PORT],
                import_config.get(CONF_SECTION_TYPES, []),
                import_config.get(CONF_SECTION_LIBRARIES, []),
                import_config.get(CONF_EXCLUDE_KEYWORDS, []),
            )
        except FailedToLogin:
            _LOGGER.error("Failed to log in to Jellyfin while importing configuration.yaml entry")
            return self.async_abort(reason="failed_to_login")

        existing_entry = next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.data.get(CONF_API_KEY) == import_config[CONF_API_KEY]
            ),
            None,
        )
        if existing_entry is not None:
            return self.async_update_reload_and_abort(
                existing_entry,
                data=import_config,
                reason="already_configured",
            )

        return self.async_create_entry(
            title=import_config[CONF_NAME] if len(import_config[CONF_NAME]) > 0 else DEFAULT_NAME,
            data=import_config,
        )
