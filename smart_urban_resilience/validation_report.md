```json
{
  "validated_data": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.8607,
      "lon": 67.0011,
      "timestamp": "2025-10-08T14:46:34.268860+00:00",
      "temperature_c": null,
      "location": {
        "latitude": 24.8607,
        "longitude": 67.0011,
        "city": "Embankment Road, Sarafa Bazaar, Lyari Town, Karachi District, Lyari Town, 75660, Pakistan"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": null
      },
      "validation_notes": [
        "temperature_c, temp_f, and temperature are null - investigate sensor/data feed",
        "id and event_id are 'unknown' - these fields should be populated with unique identifiers"
      ]
    }
  ],
  "validation_report": {
    "input_count": 1,
    "schema_validations": [],
    "duplicate_ids": [],
    "missing_counts": {
      "location": 0,
      "lon": 0,
      "event_id": 0,
      "raw_temperature": 0,
      "id": 0,
      "temperature_c": 1,
      "lat": 0,
      "timestamp": 0
    },
    "outliers": [],
    "imputations": {},
    "removed_by_missing": 0,
    "kept": 1,
    "overall_data_quality": "Low - Missing temperature data and non-unique IDs severely impact data usability."
  },
  "weather": {
    "temperature": 27.6,
    "humidity": 34,
    "precipitation": 2.58,
    "cloud_cover": 55,
    "wind_speed": 5.93,
    "source": "Simulated",
    "timestamp": "2025-10-08T14:46:09.166867"
  },
  "air_quality": {
    "aqi": 89,
    "pm10": 73.6,
    "pm2_5": 31.2,
    "carbon_monoxide": 716.0,
    "ozone": 27.0,
    "source": "Open-Meteo Air Quality",
    "timestamp": "2025-10-08T14:46:09.942904"
  },
  "environment": {
    "uv_index": 8.5,
    "grass_pollen": 191,
    "tree_pollen": 215,
    "weed_pollen": 80,
    "wildfire_risk": 95,
    "flood_risk": 54,
    "source": "Simulated",
    "timestamp": "2025-10-08T14:46:10.682643"
  }
}
```