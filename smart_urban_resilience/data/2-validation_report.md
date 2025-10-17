```json
{
  "cleaned": [
    {
      "weather": {
        "temperature": 24.86,
        "humidity": 77,
        "precipitation": 4.05,
        "cloud_cover": 30,
        "wind_speed": 1.96,
        "source": "Simulated",
        "timestamp": "2025-10-17T14:28:11.772681"
      },
      "air_quality": {
        "aqi": 74,
        "pm10": 40.5,
        "pm2_5": 36.1,
        "carbon_monoxide": 970.0,
        "ozone": 86.0,
        "source": "Open-Meteo Air Quality",
        "timestamp": "2025-10-17T14:28:12.751712"
      },
      "environment": {
        "uv_index": 8.3,
        "grass_pollen": 104,
        "tree_pollen": 238,
        "weed_pollen": 44,
        "wildfire_risk": 74,
        "flood_risk": 18,
        "source": "Simulated",
        "timestamp": "2025-10-17T14:28:12.756714"
      },
      "event_id": "evt-b32e27256339",
      "_meta": {
        "id_source": "generated"
      }
    }
  ],
  "report": {
    "input_count": 1,
    "auto_id_count": 1,
    "inferred_examples": [],
    "validator_issues": [],
    "missing_counts": {
      "weather": 0,
      "air_quality": 0,
      "environment": 0,
      "event_id": 0,
      "_meta": 0
    },
    "duplicate_examples": [],
    "outliers": [],
    "imputations": {},
    "removed_by_missing": 0,
    "kept": 1,
    "recommendations": [
      "Add sensor registration metadata when possible to reduce inference reliance."
    ]
  }
}
```