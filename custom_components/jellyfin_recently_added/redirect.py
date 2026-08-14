from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from aiohttp import web, ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.const import (
    CONF_API_KEY,
    CONF_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL
    )

from .const import DOMAIN

class ImagesRedirect(HomeAssistantView):
    def __init__(self, hass, config_entry: ConfigEntry):
        super().__init__()
        self._api_key = config_entry.data[CONF_API_KEY]
        self._base_url = f'http{"s" if config_entry.data[CONF_SSL] else ""}://{config_entry.data[CONF_HOST]}:{config_entry.data[CONF_PORT]}'
        self.name = f'{self._api_key}_Jellyfin_Recently_Added'
        self.url = f'/{config_entry.data[CONF_NAME].lower() + "_" if len(config_entry.data[CONF_NAME]) > 0 else ""}jellyfin_recently_added'
        self._session = async_get_clientsession(hass)

    async def get(self, request):
        item_id = request.query.get("item")
        image_type = request.query.get("type") or "Primary"
        tag = request.query.get("tag")

        if not item_id or item_id == "None":
            return web.HTTPNotFound()

        url = f'{self._base_url}/Items/{item_id}/Images/{image_type}'
        if tag and tag != "None":
            url += f'?tag={tag}'

        fwd_headers = {"X-Emby-Token": self._api_key}
        if_modified = request.headers.get("If-Modified-Since")
        if_none = request.headers.get("If-None-Match")
        if if_modified:
            fwd_headers["If-Modified-Since"] = if_modified
        if if_none:
            fwd_headers["If-None-Match"] = if_none

        try:
            async with self._session.get(url, headers=fwd_headers, timeout=10) as res:
                if res.status == 304:
                    return web.Response(status=304)

                ctype = res.headers.get("Content-Type", "")
                if res.status == 200 and ctype.startswith("image/"):
                    body = await res.read()
                    headers = {
                        "Content-Type": ctype or "image/jpeg",
                        "Cache-Control": "public, max-age=31536000, immutable",
                    }
                    etag = res.headers.get("ETag")
                    last_mod = res.headers.get("Last-Modified")
                    if etag:
                        headers["ETag"] = etag
                    if last_mod:
                        headers["Last-Modified"] = last_mod
                    return web.Response(body=body, headers=headers)

                _LOGGER.debug("Missing artwork (status=%s, ctype=%s) url=%s", res.status, ctype, url)
                return web.HTTPNotFound()
        except ClientError:
            _LOGGER.debug("Upstream image fetch failed url=%s", url)
            return web.HTTPBadGateway()
