from __future__ import annotations

import re
import pytest
from aioresponses import aioresponses

from custom_components.georgsmarthuette.sources import GMH_NEWS_RSS_URL, GmhCityClient, RssItem, classify_rss_items

_RSS_URL = re.compile(r"https://www\.georgsmarienhuette\.de/portal/rss\.xml.*")
_LINK_URL = re.compile(r"https?://.*")

_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Georgsmarienhütte</title>
    <item>
      <title>Erste Meldung</title>
      <link>https://www.georgsmarienhuette.de/news/1</link>
      <description>Beschreibung eins</description>
      <pubDate>Sun, 24 May 2026 10:00:00 +0000</pubDate>
      <enclosure url="https://example.com/bild.jpg" type="image/jpeg" />
    </item>
    <item>
      <title>Zweite Meldung</title>
      <link>https://www.georgsmarienhuette.de/news/2</link>
      <description>Beschreibung zwei</description>
    </item>
  </channel>
</rss>
"""

_RSS_EMPTY = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>GMH</title></channel></rss>
"""


class TestGetRssItems:
    async def test_parses_title_and_link(self, session):
        with aioresponses() as m:
            m.get(_RSS_URL, body=_RSS_XML)
            items = await GmhCityClient(session).get_rss_items()
        assert len(items) == 2
        assert items[0].title == "Erste Meldung"
        assert items[0].link == "https://www.georgsmarienhuette.de/news/1"

    async def test_parses_enclosure_image(self, session):
        with aioresponses() as m:
            m.get(_RSS_URL, body=_RSS_XML)
            items = await GmhCityClient(session).get_rss_items()
        assert items[0].image == "https://example.com/bild.jpg"

    async def test_item_without_enclosure_has_none_image(self, session):
        with aioresponses() as m:
            m.get(_RSS_URL, body=_RSS_XML)
            items = await GmhCityClient(session).get_rss_items()
        assert items[1].image is None

    async def test_parses_pubdate(self, session):
        with aioresponses() as m:
            m.get(_RSS_URL, body=_RSS_XML)
            items = await GmhCityClient(session).get_rss_items()
        assert items[0].published == "Sun, 24 May 2026 10:00:00 +0000"

    async def test_empty_feed_returns_empty_list(self, session):
        with aioresponses() as m:
            m.get(_RSS_URL, body=_RSS_EMPTY)
            items = await GmhCityClient(session).get_rss_items()
        assert items == []

    async def test_raises_on_http_error(self, session):
        import aiohttp
        with aioresponses() as m:
            m.get(_RSS_URL, status=500)
            with pytest.raises(aiohttp.ClientResponseError):
                await GmhCityClient(session).get_rss_items()


class TestClassifyRssItems:
    def test_counts_matching_topic_items(self):
        items = [
            RssItem("Vollsperrung in Oesede", "https://example.com/1", "Umleitung eingerichtet", None, None),
            RssItem("Sommerkonzert im Rathaus", "https://example.com/2", "Veranstaltung am Markt", None, None),
        ]

        summary = classify_rss_items(items, "traffic")

        assert summary["count"] == 1
        assert summary["items"][0]["title"] == "Vollsperrung in Oesede"

    def test_matches_description(self):
        items = [
            RssItem("Neue Meldung", "https://example.com/1", "Starkregen und Hochwasser möglich", None, None),
        ]

        summary = classify_rss_items(items, "weather_flood")

        assert summary["count"] == 1

    def test_weather_topic_matches_drought_and_water_saving_notices(self):
        items = [
            RssItem("Stadt ruft zum Wassersparen auf", "https://example.com/1", "Hitze und Trockenheit halten an", None, None),
        ]

        summary = classify_rss_items(items, "weather_flood")

        assert summary["count"] == 1
        assert "wassersparen" in summary["keywords"]

    def test_returns_keywords_for_home_assistant_attributes(self):
        summary = classify_rss_items([], "administration")

        assert "rat" in summary["keywords"]
        assert summary["items"] == []


class TestCheckLinkSources:
    async def test_available_source(self, session):
        with aioresponses() as m:
            m.get(_LINK_URL, status=200, repeat=True)
            result = await GmhCityClient(session).check_link_sources()
        assert all(v["available"] for v in result.values())

    async def test_unavailable_source_on_404(self, session):
        with aioresponses() as m:
            m.get(_LINK_URL, status=404, repeat=True)
            result = await GmhCityClient(session).check_link_sources()
        assert all(not v["available"] for v in result.values())

    async def test_connection_error_marks_unavailable(self, session):
        import aiohttp
        with aioresponses() as m:
            m.get(_LINK_URL, exception=aiohttp.ClientConnectionError("refused"), repeat=True)
            result = await GmhCityClient(session).check_link_sources()
        for v in result.values():
            assert v["available"] is False
            assert "error" in v

    async def test_returns_all_link_sources(self, session):
        from custom_components.georgsmarthuette.sources import GMH_LINK_SOURCES
        with aioresponses() as m:
            m.get(_LINK_URL, status=200, repeat=True)
            result = await GmhCityClient(session).check_link_sources()
        assert set(result.keys()) == set(GMH_LINK_SOURCES.keys())


class TestCleanHtml:
    def test_strips_tags(self):
        assert GmhCityClient._clean_html("<b>Text</b>") == "Text"

    def test_replaces_br_with_space(self):
        result = GmhCityClient._clean_html("Zeile1<br/>Zeile2")
        assert result == "Zeile1 Zeile2"

    def test_decodes_html_entities(self):
        result = GmhCityClient._clean_html("&amp; &lt; &gt;")
        assert result == "& < >"

    def test_collapses_whitespace(self):
        result = GmhCityClient._clean_html("  viel   Leerzeichen  ")
        assert result == "viel Leerzeichen"

    def test_returns_empty_string_for_none(self):
        assert GmhCityClient._clean_html(None) == ""


class TestUtm32ToLatLon:
    def test_converts_gmh_coordinates(self):
        # Known UTM32 → WGS84 conversion for approx. Georgsmarienhütte city centre
        lat, lon = GmhCityClient._utm32_to_latlon(428000, 5789000)
        assert 52.0 < lat < 52.5
        assert 7.8 < lon < 8.3
