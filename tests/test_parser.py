"""Unit tests for parser.parse_data — pure logic, no real Home Assistant instance needed.

async_sign_path is the only thing here that touches Home Assistant (it needs a running
http component to sign a path), so it's stubbed out; everything else is plain data
transformation and can be asserted on directly.
"""
from unittest.mock import patch

from custom_components.jellyfin_recently_added.parser import parse_data

FAKE_HASS = object()

MOVIE_ITEM = {
    "Id": "movie-1",
    "Type": "Movie",
    "Name": "Sample Movie",
    "DateCreated": "2026-01-01T12:00:00.0000000Z",
    "PremiereDate": "2020-05-04T00:00:00.0000000Z",
    "RunTimeTicks": 60 * 600000000,  # 60 minutes
    "Genres": ["Action", "Adventure", "Comedy", "Drama"],
    "CommunityRating": 7.8,
    "Overview": "A sample overview.",
    "ProviderIds": {"Tmdb": "12345"},
    "RemoteTrailers": [{"Url": "https://youtube.com/watch?v=abc"}],
    "ImageTags": {"Primary": "poster-tag"},
    "BackdropImageTags": ["backdrop-tag"],
    "UserData": {"Played": False},
}

EPISODE_ITEM = {
    "Id": "episode-1",
    "Type": "Episode",
    "Name": "Pilot",
    "SeriesName": "Sample Show",
    "SeriesId": "series-1",
    "SeriesPrimaryImageTag": "series-poster-tag",
    "ParentBackdropItemId": "series-1",
    "ParentBackdropImageTags": ["series-backdrop-tag"],
    "DateCreated": "2026-02-02T08:30:00.0000000Z",
    "PremiereDate": "2019-09-09T00:00:00.0000000Z",
    "ParentIndexNumber": 1,
    "IndexNumber": 3,
    "RunTimeTicks": 42 * 600000000,
    "Genres": [],
    "CommunityRating": 0,
    "Overview": "",
    "UserData": {"Played": True},
}


def _sign_stub(hass, path, ttl):
    return f"/signed{path}"


@patch("custom_components.jellyfin_recently_added.parser.async_sign_path", side_effect=_sign_stub)
def test_parse_movie(mock_sign):
    output = parse_data(
        FAKE_HASS, [MOVIE_ITEM], max=5, base_url="http://jf.local:8096",
        identifier="server-1", section_key="movies", images_base_url="/jf",
    )

    assert len(output) == 1
    item = output[0]
    assert item["title"] == "Sample Movie"
    assert item["episode"] == ""
    assert item["number"] == ""
    assert item["runtime"] == 60
    assert item["rating"] == "\N{BLACK STAR} 7.8"
    assert item["genres"] == "Action, Adventure, Comedy"
    assert item["tmdb_id"] == "12345"
    assert item["trailer"] == "https://youtube.com/watch?v=abc"
    assert item["flag"] is True
    assert item["aired"] == "2020-05-04"
    assert item["deep_link"] == "http://jf.local:8096/web/index.html#!/details?id=movie-1&serverId=server-1"
    assert item["poster"] == "/signed/jf?item=movie-1&type=Primary&tag=poster-tag"
    assert item["fanart"] == "/signed/jf?item=movie-1&type=Backdrop&tag=backdrop-tag"


@patch("custom_components.jellyfin_recently_added.parser.async_sign_path", side_effect=_sign_stub)
def test_parse_episode_uses_series_title_and_artwork(mock_sign):
    output = parse_data(
        FAKE_HASS, [EPISODE_ITEM], max=5, base_url="http://jf.local:8096",
        identifier="server-1", section_key="tvshows", images_base_url="/jf",
    )

    item = output[0]
    assert item["title"] == "Sample Show"
    assert item["episode"] == "Pilot"
    assert item["season_num"] == 1
    assert item["episode_num"] == 3
    assert item["number"] == "S01E03"
    assert item["flag"] is False
    assert item["rating"] == ""
    assert item["genres"] == ""
    # Episodes borrow the series' artwork, not their own.
    assert item["poster"] == "/signed/jf?item=series-1&type=Primary&tag=series-poster-tag"
    assert item["fanart"] == "/signed/jf?item=series-1&type=Backdrop&tag=series-backdrop-tag"


@patch("custom_components.jellyfin_recently_added.parser.async_sign_path", side_effect=_sign_stub)
def test_parse_data_is_all_merges_and_caps_per_type(mock_sign):
    newer_movie = {**MOVIE_ITEM, "Id": "movie-2", "DateCreated": "2026-03-01T00:00:00.0000000Z"}
    data = {
        "movies": [MOVIE_ITEM, newer_movie],
        "tvshows": [EPISODE_ITEM],
    }

    output = parse_data(
        FAKE_HASS, data, max=1, base_url="http://jf.local:8096",
        identifier="server-1", section_key="all", images_base_url="/jf", is_all=True,
    )

    # max=1 keeps only the newest movie (movie-2), plus the one episode.
    deep_links = {item["deep_link"] for item in output}
    assert deep_links == {
        "http://jf.local:8096/web/index.html#!/details?id=movie-2&serverId=server-1",
        "http://jf.local:8096/web/index.html#!/details?id=episode-1&serverId=server-1",
    }


@patch("custom_components.jellyfin_recently_added.parser.async_sign_path", side_effect=_sign_stub)
def test_parse_data_skips_items_without_date_created(mock_sign):
    output = parse_data(
        FAKE_HASS, [{**MOVIE_ITEM, "DateCreated": None}], max=5, base_url="http://jf.local:8096",
        identifier="server-1", section_key="movies", images_base_url="/jf",
    )
    assert output == []
