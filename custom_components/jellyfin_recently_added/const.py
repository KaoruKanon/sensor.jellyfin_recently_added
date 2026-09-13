from typing import Final

DOMAIN: Final = "jellyfin_recently_added"
TIMEOUT_MINUTES: Final = 10
POLL_INTERVAL_MINUTES: Final = 10
SIGN_URL_TTL_MINUTES: Final = 10080  # 7 days


DEFAULT_NAME: Final = 'Jellyfin Recently Added'
CONF_USER_ID: Final = 'user_id'
CONF_USER_NAME: Final = 'user_name'
CONF_MAX: Final = 'max'
CONF_SECTION_TYPES: Final = 'section_types'
ALL_SECTION_TYPES: Final = ["movies", "tvshows", "music", "photos"]
CONF_SECTION_LIBRARIES: Final = 'section_libraries'
CONF_EXCLUDE_KEYWORDS: Final = 'exclude_keywords'
CONF_SECTION_LIBRARIES_LABEL: Final = 'Which libraries to consider:'
CONF_EXCLUDE_KEYWORDS_LABEL: Final = 'Keyword to be exclude from the sensor:'
CONF_ON_DECK: Final = 'on_deck'

REQUEST_TIMEOUT: Final = 10

# Jellyfin CollectionType -> ItemType(s) to request from the Latest/Resume endpoints
SECTION_ITEM_TYPE: Final = {
    "movies": "Movie",
    "tvshows": "Episode",
    "music": "Audio",
    "photos": "Photo",
}

ITEM_FIELDS: Final = (
    "Genres,Overview,ProviderIds,RemoteTrailers,DateCreated,PremiereDate,"
    "CommunityRating,ProductionYear,SeriesName,SeriesId,SeriesPrimaryImageTag,"
    "Studios,ParentBackdropImageTags,ParentBackdropItemId"
)

DEFAULT_PARSE_DICT: Final = {
    'title_default': '$title',
    'line1_default': '$episode',
    'line2_default': '$release',
    'line3_default': '$number - $rating - $runtime',
    'line4_default': '$genres',
    'icon': 'mdi:eye-off'
}
