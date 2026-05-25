from __future__ import annotations

from custom_components.georgsmarthuette.sources import VosDisruptionsClient


_VOS_HTML = """
<ul>
  <li class="accordion-item bus_454" data-accordion-item>
    <a href="#" class="h5 accordion-title">Sperrung Oesede (Harderberg), Nordstraße</a>
    <div class="accordion-content" data-tab-content>
      <p>Die Haltestelle Oesede, Holunderstraße kann nicht bedient werden.<br>Bitte Ersatzhaltestelle nutzen.</p>
      <a href="https://fahrplaner.vbn.de/pdf/info.pdf">PDF</a>
    </div>
  </li>
  <li class="accordion-item bus_999" data-accordion-item>
    <a href="#" class="h5 accordion-title">Sperrung Musterstadt</a>
    <div class="accordion-content" data-tab-content><p>Nicht in GMH.</p></div>
  </li>
</ul>
"""


class TestVosDisruptionsParser:
    def test_parses_visible_accordion_items(self):
        result = VosDisruptionsClient.parse_disruptions(_VOS_HTML)
        assert result["total_count"] == 2
        assert result["items"][0]["title"] == "Sperrung Oesede (Harderberg), Nordstraße"
        assert result["items"][0]["lines"] == ["454"]
        assert result["items"][0]["links"] == ["https://fahrplaner.vbn.de/pdf/info.pdf"]

    def test_filters_gmh_relevant_items(self):
        result = VosDisruptionsClient.parse_disruptions(_VOS_HTML)
        assert result["relevant_count"] == 1
        assert result["relevant_items"][0]["title"].startswith("Sperrung Oesede")

    def test_line_only_relevance_for_regular_gmh_lines(self):
        html = """
        <li class="accordion-item bus_m3" data-accordion-item>
          <a href="#" class="h5 accordion-title">Sperrung Rosenplatz</a>
          <div class="accordion-content" data-tab-content><p>Linie M3 wird umgeleitet.</p></div>
        </li>
        """
        result = VosDisruptionsClient.parse_disruptions(html)
        assert result["relevant_count"] == 1
        assert result["relevant_items"][0]["lines"] == ["M3"]
