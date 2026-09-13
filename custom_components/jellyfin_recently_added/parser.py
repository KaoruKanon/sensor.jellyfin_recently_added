import math
from datetime import timedelta
from time import time

from homeassistant.core import HomeAssistant
from homeassistant.components.http.auth import async_sign_path

from .const import SIGN_URL_TTL_MINUTES

import logging
_LOGGER = logging.getLogger(__name__)

# Stable signed-path cache: prevents new URLs on each 10-min refresh
# Re-signs only when near expiry, so browsers don't re-download unchanged images.
_SIGNED_URL_CACHE = {}           # key: raw_path, value: (signed_url, expires_epoch)
_STALE_MARGIN_SEC = 24 * 3600    # renew 1 day before expiry to be safe

def _stable_signed_path(hass: HomeAssistant, raw_path: str, ttl_minutes: int) -> str:
    now = time()
    entry = _SIGNED_URL_CACHE.get(raw_path)
    if entry:
        signed_url, exp = entry
        if exp - now > _STALE_MARGIN_SEC:
            return signed_url
    signed = async_sign_path(hass, raw_path, timedelta(minutes=ttl_minutes))
    _SIGNED_URL_CACHE[raw_path] = (signed, now + ttl_minutes * 60)
    return signed

def _date_only(value):
    return value[:10] if value else ""

def _poster_ids(item):
    if item.get("Type") == "Episode" and item.get("SeriesPrimaryImageTag") and item.get("SeriesId"):
        return item["SeriesId"], item["SeriesPrimaryImageTag"]
    image_tags = item.get("ImageTags") or {}
    if image_tags.get("Primary"):
        return item.get("Id"), image_tags["Primary"]
    return None, None

def _fanart_ids(item):
    parent_backdrops = item.get("ParentBackdropImageTags") or []
    if parent_backdrops and item.get("ParentBackdropItemId"):
        return item["ParentBackdropItemId"], parent_backdrops[0]
    own_backdrops = item.get("BackdropImageTags") or []
    if own_backdrops:
        return item.get("Id"), own_backdrops[0]
    return None, None

def parse_data(hass: HomeAssistant, data, max, base_url, identifier, section_key, images_base_url, is_all = False):
    if is_all:
        sorted_data = []
        for k in data.keys():
            type_sorted = sorted(data[k], key=lambda i: i.get('DateCreated', ''), reverse=True)[:max]
            sorted_data += type_sorted
        sorted_data = sorted(sorted_data, key=lambda i: i.get('DateCreated', ''), reverse=True)
    else:
        sorted_data = sorted(data, key=lambda i: i.get('DateCreated', ''), reverse=True)[:max]

    output = []
    for item in sorted_data:
        if not item.get("DateCreated"):
            continue

        item_type = item.get("Type", "")
        data_output = {}

        data_output["airdate"] = f'{item["DateCreated"][:19]}Z'
        data_output["aired"] = _date_only(item.get("PremiereDate"))
        data_output["release"] = '$day, $date $time'

        user_data = item.get("UserData") or {}
        data_output["flag"] = not user_data.get("Played", False)

        if item_type == "Episode":
            data_output["title"] = item.get("SeriesName") or item.get("Name", "")
            data_output["episode"] = item.get("Name", "")
        else:
            data_output["title"] = item.get("Name", "")
            data_output["episode"] = ""

        season_num = item.get("ParentIndexNumber")
        episode_num = item.get("IndexNumber")
        if season_num is not None:
            data_output["season_num"] = season_num
        if episode_num is not None:
            data_output["episode_num"] = episode_num
        if season_num is not None and episode_num is not None:
            data_output["number"] = f'S{"{:0>2}".format(season_num)}E{"{:0>2}".format(episode_num)}'
        else:
            data_output["number"] = ''

        run_time_ticks = item.get("RunTimeTicks") or 0
        if run_time_ticks > 0:
            data_output["runtime"] = math.floor(run_time_ticks / 600000000)

        studios = item.get("Studios") or []
        data_output["studio"] = studios[0].get("Name", "") if studios else ""

        genres = (item.get("Genres") or [])[:3]
        if not genres:
            genres = (item.get('tmdb_genres') or [])[:3]
        data_output["genres"] = ", ".join(genres)

        community_rating = float(item.get("CommunityRating") or 0)
        tmdb_rating = float(item.get("tmdb_rating") or 0)
        if community_rating > 0:
            data_output["rating"] = '\N{BLACK STAR} ' + str(round(community_rating, 1))
        elif tmdb_rating > 0:
            data_output["rating"] = '\N{BLACK STAR} ' + str(round(tmdb_rating, 1))
        else:
            data_output["rating"] = ''

        provider_tmdb_id = (item.get("ProviderIds") or {}).get("Tmdb")
        data_output["tmdb_id"] = provider_tmdb_id or item.get('tmdb_id', '')
        data_output['summary'] = item.get('Overview') or ''

        remote_trailers = item.get("RemoteTrailers") or []
        data_output['trailer'] = remote_trailers[0].get("Url") if remote_trailers else item.get('tmdb_trailer')

        poster_item_id, poster_tag = _poster_ids(item)
        data_output["poster"] = _stable_signed_path(
            hass,
            f'{images_base_url}?item={poster_item_id}&type=Primary&tag={poster_tag}',
            SIGN_URL_TTL_MINUTES
        ) if poster_item_id else ""

        fanart_item_id, fanart_tag = _fanart_ids(item)
        data_output["fanart"] = _stable_signed_path(
            hass,
            f'{images_base_url}?item={fanart_item_id}&type=Backdrop&tag={fanart_tag}',
            SIGN_URL_TTL_MINUTES
        ) if fanart_item_id else ""

        item_id = item.get("Id")
        data_output["deep_link"] = f'{base_url}/web/index.html#!/details?id={item_id}&serverId={identifier}' if identifier and item_id else None

        output.append(data_output)

    return output
