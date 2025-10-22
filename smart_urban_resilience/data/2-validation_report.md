```json
{
  "cleaned": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.8607,
      "lon": 67.0011,
      "timestamp": "2025-10-22T07:25:55.721457",
      "location": {
        "latitude": 24.8607,
        "longitude": 67.0011,
        "city": "Karachi",
        "country": "Pakistan"
      },
      "weather": {
        "temperature_celsius": 36.33,
        "humidity": 39,
        "precipitation_mm": 1.57,
        "cloud_cover_percent": 85,
        "wind_speed_mps": 1.84,
        "source": "Simulated",
        "timestamp": "2025-10-22T07:25:55.721457"
      },
      "air_quality": {
        "aqi": 66,
        "pm10": 36.9,
        "pm2_5": 26.4,
        "carbon_monoxide_ppm": 372.0,
        "ozone_ppb": 161.0,
        "source": "Open-Meteo Air Quality",
        "timestamp": "2025-10-22T07:25:57.250396"
      },
      "environment": {
        "uv_index": 8.1,
        "grass_pollen": 175,
        "tree_pollen": 38,
        "weed_pollen": 98,
        "wildfire_risk": 35,
        "flood_risk": 53,
        "source": "Simulated",
        "timestamp": "2025-10-22T07:25:58.674330"
      },
      "_meta": {
        "id_source": "original",
        "notes": "IDs could not be determined with available information."
      }
    }
  ],
  "report": {
    "input_count": 1,
    "auto_id_count": 0,
    "inferred_examples": [],
    "validator_issues": [],
    "missing_counts": {
      "id": 0,
      "event_id": 0,
      "lat": 0,
      "lon": 0,
      "timestamp": 0,
      "location": 0,
      "weather": 0,
      "air_quality": 0,
      "environment": 0,
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