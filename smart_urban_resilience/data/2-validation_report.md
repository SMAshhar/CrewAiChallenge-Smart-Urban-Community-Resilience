```json
{
  "cleaned_data": [
    {
      "event_type": "weather",
      "latitude": 34.0,
      "longitude": 118.0,
      "location_details": {
        "latitude": 34.0,
        "longitude": 118.0,
        "city": "Suining County"
      },
      "timestamp": "2025-10-29T01:18:46.288595+00:00",
      "source": "Simulated",
      "temperature_c": 31.09,
      "humidity": 52.0,
      "precipitation": 8.13,
      "cloud_cover": 33.0,
      "wind_speed": 5.54,
      "event_id": "inf-d644055724e8",
      "_meta": {
        "id_source": "inferred"
      },
      "aqi": 76.0,
      "pm10": 50.0,
      "pm2_5": 46.5,
      "carbon_monoxide": 261.0,
      "ozone": 48.0,
      "uv_index": 8.7,
      "grass_pollen": 89.0,
      "tree_pollen": 165.0,
      "weed_pollen": 148.0,
      "wildfire_risk": 80.0,
      "flood_risk": 1.0
    },
    {
      "event_type": "air_quality",
      "latitude": 34.0,
      "longitude": 118.0,
      "location_details": {
        "latitude": 34.0,
        "longitude": 118.0,
        "city": "Suining County"
      },
      "timestamp": "2025-10-29T01:18:47.088445+00:00",
      "source": "Open-Meteo Air Quality",
      "temperature_c": 31.09,
      "humidity": 52.0,
      "precipitation": 8.13,
      "cloud_cover": 33.0,
      "wind_speed": 5.54,
      "event_id": "inf-f6822feb7fbe",
      "_meta": {
        "id_source": "inferred"
      },
      "aqi": 76.0,
      "pm10": 50.0,
      "pm2_5": 46.5,
      "carbon_monoxide": 261.0,
      "ozone": 48.0,
      "uv_index": 8.7,
      "grass_pollen": 89.0,
      "tree_pollen": 165.0,
      "weed_pollen": 148.0,
      "wildfire_risk": 80.0,
      "flood_risk": 1.0
    },
    {
      "event_type": "environment",
      "latitude": 34.0,
      "longitude": 118.0,
      "location_details": {
        "latitude": 34.0,
        "longitude": 118.0,
        "city": "Suining County"
      },
      "timestamp": "2025-10-29T01:18:48.137015+00:00",
      "source": "Simulated",
      "temperature_c": 31.09,
      "humidity": 52.0,
      "precipitation": 8.13,
      "cloud_cover": 33.0,
      "wind_speed": 5.54,
      "event_id": "inf-778490ccad7b",
      "_meta": {
        "id_source": "inferred"
      },
      "aqi": 76.0,
      "pm10": 50.0,
      "pm2_5": 46.5,
      "carbon_monoxide": 261.0,
      "ozone": 48.0,
      "uv_index": 8.7,
      "grass_pollen": 89.0,
      "tree_pollen": 165.0,
      "weed_pollen": 148.0,
      "wildfire_risk": 80.0,
      "flood_risk": 1.0
    }
  ],
  "validation_report": {
    "input_count": 3,
    "auto_id_count": 3,
    "inferred_examples": [
      {
        "event_id": "inf-d644055724e8",
        "lat": 34.0,
        "lon": 118.0,
        "timestamp": "2025-10-29T01:18:46.288595+00:00"
      },
      {
        "event_id": "inf-f6822feb7fbe",
        "lat": 34.0,
        "lon": 118.0,
        "timestamp": "2025-10-29T01:18:47.088445+00:00"
      },
      {
        "event_id": "inf-778490ccad7b",
        "lat": 34.0,
        "lon": 118.0,
        "timestamp": "2025-10-29T01:18:48.137015+00:00"
      }
    ],
    "validator_issues": [],
    "missing_counts": {
      "event_type": 0,
      "latitude": 0,
      "longitude": 0,
      "location_details": 0,
      "timestamp": 0,
      "source": 0,
      "temperature_c": 2,
      "humidity": 2,
      "precipitation": 2,
      "cloud_cover": 2,
      "wind_speed": 2,
      "event_id": 0,
      "_meta": 0,
      "aqi": 2,
      "pm10": 2,
      "pm2_5": 2,
      "carbon_monoxide": 2,
      "ozone": 2,
      "uv_index": 2,
      "grass_pollen": 2,
      "tree_pollen": 2,
      "weed_pollen": 2,
      "wildfire_risk": 2,
      "flood_risk": 2
    },
    "duplicate_examples": [],
    "outliers": [],
    "imputations": {
      "temperature_c": {
        "method": "median",
        "filled": 2,
        "value": 31.09
      },
      "humidity": {
        "method": "median",
        "filled": 2,
        "value": 52.0
      },
      "precipitation": {
        "method": "median",
        "filled": 2,
        "value": 8.13
      },
      "cloud_cover": {
        "method": "median",
        "filled": 2,
        "value": 33.0
      },
      "wind_speed": {
        "method": "median",
        "filled": 2,
        "value": 5.54
      },
      "aqi": {
        "method": "median",
        "filled": 2,
        "value": 76.0
      },
      "pm10": {
        "method": "median",
        "filled": 2,
        "value": 50.0
      },
      "pm2_5": {
        "method": "median",
        "filled": 2,
        "value": 46.5
      },
      "carbon_monoxide": {
        "method": "median",
        "filled": 2,
        "value": 261.0
      },
      "ozone": {
        "method": "median",
        "filled": 2,
        "value": 48.0
      },
      "uv_index": {
        "method": "median",
        "filled": 2,
        "value": 8.7
      },
      "grass_pollen": {
        "method": "median",
        "filled": 2,
        "value": 89.0
      },
      "tree_pollen": {
        "method": "median",
        "filled": 2,
        "value": 165.0
      },
      "weed_pollen": {
        "method": "median",
        "filled": 2,
        "value": 148.0
      },
      "wildfire_risk": {
        "method": "median",
        "filled": 2,
        "value": 80.0
      },
      "flood_risk": {
        "method": "median",
        "filled": 2,
        "value": 1.0
      }
    },
    "removed_by_missing": 0,
    "kept": 3,
    "recommendations": [
      "Add sensor registration metadata when possible to reduce inference reliance."
    ]
  }
}
```