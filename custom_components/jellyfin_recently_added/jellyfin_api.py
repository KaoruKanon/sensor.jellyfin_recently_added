import functools
import logging

import requests

from homeassistant.core import HomeAssistant

from .const import DEFAULT_PARSE_DICT, ITEM_FIELDS, REQUEST_TIMEOUT, SECTION_ITEM_TYPE
from .parser import parse_data
from .tmdb_api import get_tmdb_trailer_url

_LOGGER = logging.getLogger(__name__)


def _get_json(url: str, api_key: str):
    response = requests.get(
        url,
        headers={
            "X-Emby-Token": api_key,
            "Accept": "application/json",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


class JellyfinApi():
    def __init__(
        self,
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
        exclude_keywords: list
    ):
        self._hass = hass
        self._ssl = 's' if ssl else ''
        self._api_key = api_key
        self._user_id = user_id
        self._max = max
        self._on_deck = on_deck
        self._host = host
        self._port = port
        self._section_types = section_types
        self._section_libraries = section_libraries
        self._exclude_keywords = exclude_keywords
        self._images_base_url = f'/{name.lower() + "_" if len(name) > 0 else ""}jellyfin_recently_added'

    async def _get(self, url: str):
        return await self._hass.async_add_executor_job(functools.partial(_get_json, url, self._api_key))

    async def update(self):
        base_url = 'http{0}://{1}:{2}'.format(
            self._ssl,
            self._host,
            self._port
        )

        """ Getting the server identifier """
        try:
            info = await self._get(f'{base_url}/System/Info')
            identifier = info.get("Id")
        except (OSError, ValueError) as e:
            raise FailedToLogin from e

        """ Find the ID of all libraries (views) available to the configured user """
        sections = []
        libs = []
        try:
            views = await self._get(f'{base_url}/Users/{self._user_id}/Views')
            for view in views.get("Items", []):
                libs.append(view.get("Name"))
                collection_type = view.get("CollectionType")
                if collection_type in self._section_types and (len(self._section_libraries) == 0 or view.get("Name") in self._section_libraries):
                    sections.append({'type': collection_type, 'id': view.get("Id")})
        except (OSError, ValueError) as e:
            raise FailedToLogin from e

        """ Looping through all libraries (sections) """
        data = {
            'all': {}
        }
        for s in self._section_types:
            data[s] = []

        for library in sections:
            try:
                include_type = SECTION_ITEM_TYPE.get(library["type"])
                if self._on_deck:
                    url = (
                        f'{base_url}/Users/{self._user_id}/Items/Resume'
                        f'?ParentId={library["id"]}&Limit={self._max * 2}&Fields={ITEM_FIELDS}'
                    )
                else:
                    url = (
                        f'{base_url}/Users/{self._user_id}/Items/Latest'
                        f'?ParentId={library["id"]}&Limit={self._max * 2}&Fields={ITEM_FIELDS}'
                    )
                    if include_type:
                        url += f'&IncludeItemTypes={include_type}&GroupItems=false'

                payload = await self._get(url)
                items = payload.get("Items", payload) if isinstance(payload, dict) else payload

                # Fetch TMDB data (trailer, rating, genres) only when Jellyfin has none natively
                for item in items:
                    if item.get("RemoteTrailers"):
                        continue
                    search_title = item.get('SeriesName', item.get('Name', ''))
                    tmdb_data = await get_tmdb_trailer_url(self._hass, search_title, library['type'])
                    item['tmdb_trailer'] = tmdb_data['trailer']
                    item['tmdb_rating'] = tmdb_data['tmdb_rating']
                    item['tmdb_genres'] = tmdb_data['tmdb_genres']
                    item['tmdb_id'] = tmdb_data['tmdb_id']

                if library["type"] not in data['all']:
                    data['all'][library["type"]] = []
                data['all'][library["type"]] += items
                data[library["type"]] += items
            except (OSError, ValueError):
                # Skip this library if it fails to load
                continue

        data_out = {}
        for k in data.keys():
            parsed_data = parse_data(self._hass, data[k], self._max, base_url, identifier, k, self._images_base_url, k == "all")
            data_out[k] = {'data': [DEFAULT_PARSE_DICT] + parsed_data}

        return {
            "data": {**data_out},
            "online": True,
            "libraries": libs
        }


class FailedToLogin(Exception):
    "Raised when the Jellyfin user fail to Log-in"
    pass
