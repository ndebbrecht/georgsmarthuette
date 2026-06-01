from custom_components.georgsmarthuette.sources import NinaWarningsClient


def test_nina_parse_warnings_keeps_county_scope():
    data = NinaWarningsClient.parse_warnings([
        {
            "id": "mow.test",
            "payload": {
                "data": {
                    "provider": "MOWAS",
                    "headline": "Probealarm Landkreis Osnabrück",
                    "severity": "Minor",
                    "urgency": "Expected",
                    "sent": "2026-06-01T08:00:00+00:00",
                    "description": "Testmeldung",
                    "instruction": "Keine Handlung erforderlich",
                }
            },
        }
    ])

    assert data["warning_count"] == 1
    assert data["coverage"] == "Landkreis Osnabrück (enthält Georgsmarienhütte)"
    assert data["warnings"][0]["headline"] == "Probealarm Landkreis Osnabrück"
    assert data["warnings"][0]["provider"] == "MOWAS"
