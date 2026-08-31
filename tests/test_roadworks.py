from __future__ import annotations

from custom_components.georgsmarthuette.sources import CountyRoadworksClient


_ROADWORKS_HTML = """
<div class="card card-accordion" id="node-1">
  <button>
    <div class="headline">
      <h6 class="headline-title">B 51 / B 68 zwischen Osnabrück-Nahne und Georgsmarienhütte</h6>
      <div class="headline-subtitle">
        <time datetime="2026-02-16T07:00:00Z">16.02.2026</time> -
        <time datetime="2026-07-10T18:00:00Z">10.07.2026</time>
      </div>
    </div>
  </button>
  <div id="accordion-traffic1-content" class="collapse">
    <div class="card-body"><p>Die B51 wird in Richtung Georgsmarienhütte saniert.</p></div>
  </div>
</div>
<div class="card card-accordion" id="node-2">
  <button>
    <div class="headline">
      <h6 class="headline-title">K409 Melle-Meesdorf</h6>
      <div class="headline-subtitle"><time datetime="2026-06-08T07:00:00Z">08.06.2026</time></div>
    </div>
  </button>
  <div class="card-body"><p>Nicht in GMH.</p></div>
</div>
"""


class TestCountyRoadworksParser:
    def test_parses_accordion_cards(self):
        result = CountyRoadworksClient.parse_roadworks(_ROADWORKS_HTML)
        assert result["total_count"] == 2
        assert result["items"][0]["title"].startswith("B 51")
        assert result["items"][0]["start"] == "2026-02-16T07:00:00Z"
        assert result["items"][0]["end"] == "2026-07-10T18:00:00Z"

    def test_filters_gmh_relevant_roadworks(self):
        result = CountyRoadworksClient.parse_roadworks(_ROADWORKS_HTML)
        assert result["relevant_count"] == 1
        assert "Georgsmarienhütte" in result["relevant_items"][0]["title"]

    def test_b51_is_relevant_with_gmh_side_context(self):
        html = '<div class="card card-accordion" id="node-3"><h6 class="headline-title">B51 Richtung Bad Iburg</h6><div class="card-body"><p>Ausfahrt gesperrt.</p></div></div>'
        result = CountyRoadworksClient.parse_roadworks(html)
        assert result["relevant_count"] == 1

    def test_b51_alone_is_not_relevant(self):
        html = '<div class="card card-accordion" id="node-4"><h6 class="headline-title">B475 Füchtorfer Straße</h6><div class="card-body"><p>Die B 475 wird zwischen Kreisverkehr Münsterstraße und Kreisverkehr B 51 saniert.</p></div></div>'
        result = CountyRoadworksClient.parse_roadworks(html)
        assert result["relevant_count"] == 0
