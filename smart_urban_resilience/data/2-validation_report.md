```json
{
  "cleaned_record": {
    "latitude": 34,
    "longitude": 118,
    "weather": {
      "temperature": 26.91,
      "humidity": 36,
      "precipitation": 6.13,
      "cloud_cover": 87,
      "wind_speed": 3.12,
      "source": "Simulated",
      "timestamp": "2025-10-27T04:41:34.741505"
    },
    "air_quality": {
      "aqi": 76,
      "pm10": 18.6,
      "pm2_5": 11.8,
      "carbon_monoxide": 179.0,
      "ozone": 86.0,
      "source": "Open-Meteo Air Quality",
      "timestamp": "2025-10-27T04:41:39.619598"
    },
    "environment": {
      "uv_index": 7.5,
      "grass_pollen": 157,
      "tree_pollen": 239,
      "weed_pollen": 108,
      "wildfire_risk": 9,
      "flood_risk": 75,
      "source": "Simulated",
      "timestamp": "2025-10-27T04:41:43.485365"
    },
    "event_id": "evt-53d2fc6f40ee",
    "_meta": {
      "id_source": "generated"
    }
  },
  "validation_report": {
    "input_count": 1,
    "auto_id_count": 1,
    "inferred_examples": [],
    "validator_issues": [],
    "missing_counts": {
      "latitude": 0,
      "longitude": 0,
      "weather": 0,
      "air_quality": 0,
      "environment": 0,
      "event_id": 0,
      "_meta": 0
    },
    "duplicate_examples": [],
    "outliers": [],
    "imputations": {
      "latitude": {
        "method": "median",
        "filled": 0,
        "value": 34.0
      },
      "longitude": {
        "method": "median",
        "filled": 0,
        "value": 118.0
      }
    },
    "removed_by_missing": 0,
    "kept": 1,
    "recommendations": [
      "Add sensor registration metadata when possible to reduce inference reliance."
    ]
  }
}
```