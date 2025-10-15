```json
{
  "cleaned": [
    {
      "weather": {
        "temperature": 24.68,
        "humidity": 52,
        "precipitation": 1.21,
        "cloud_cover": 85,
        "wind_speed": 1.16,
        "source": "Simulated",
        "timestamp": "2025-10-13T01:12:12.851628"
      },
      "air_quality": {
        "aqi": 69,
        "pm10": 49.2,
        "pm2_5": 35.5,
        "carbon_monoxide": 559.0,
        "ozone": 64.0,
        "source": "Open-Meteo Air Quality",
        "timestamp": "2025-10-13T01:12:23.738531"
      },
      "environment": {
        "uv_index": 4.6,
        "grass_pollen": 199,
        "tree_pollen": 192,
        "weed_pollen": 142,
        "wildfire_risk": 25,
        "flood_risk": 97,
        "source": "Simulated",
        "timestamp": "2025-10-13T01:12:24.491145"
      },
      "location": {
        "latitude": 24.86,
        "longitude": 67.01,
        "city": "Karachi Division"
      },
      "timestamp": "2025-10-13T01:12:24.491145",
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.86,
      "lon": 67.01,
      "temperature_c": null,
      "raw_temperature": {
        "temp_f": null,
        "temperature": null
      },
      "_meta": {
        "id_source": "original"
      }
    }
  ],
  "report": {
    "input_count": 1,
    "auto_id_count": 0,
    "inferred_examples": [],
    "validator_issues": [],
    "missing_counts": {
      "weather": 0,
      "id": 0,
      "temperature_c": 1,
      "event_id": 0,
      "lat": 0,
      "_meta": 0,
      "lon": 0,
      "timestamp": 0,
      "location": 0,
      "environment": 0,
      "air_quality": 0,
      "raw_temperature": 0
    },
    "duplicate_examples": [],
    "outliers": [],
    "imputations": {},
    "removed_by_missing": 0,
    "kept": 1,
    "recommendations": [
      "Install pandas for faster & richer validation pipelines."
    ]
  }
}
```