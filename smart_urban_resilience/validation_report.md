```json
{
  "cleaned": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.865,
      "lon": 67.015,
      "timestamp": "2025-10-08T01:50:58.473642+00:00",
      "temperature_c": 23.27,
      "location": {
        "latitude": 24.865,
        "longitude": 67.015,
        "city": "Karachi Division"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": 23.27
      }
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.865,
      "lon": 67.015,
      "timestamp": "2025-10-08T01:50:58.972978+00:00",
      "temperature_c": 23.27,
      "location": {
        "latitude": 24.865,
        "longitude": 67.015,
        "city": "Karachi Division"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": null
      }
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.865,
      "lon": 67.015,
      "timestamp": "2025-10-08T01:51:00.697208+00:00",
      "temperature_c": 23.27,
      "location": {
        "latitude": 24.865,
        "longitude": 67.015,
        "city": "Karachi Division"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": null
      }
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.865,
      "lon": 67.015,
      "timestamp": "2025-10-08T01:51:02.513296+00:00",
      "temperature_c": 23.27,
      "location": {
        "latitude": 24.865,
        "longitude": 67.015,
        "city": "Karachi Division"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": null
      }
    }
  ],
  "report": {
    "input_count": 4,
    "schema_validations": [],
    "duplicate_ids": [],
    "missing_counts": {
      "id": 0,
      "timestamp": 0,
      "location": 0,
      "lon": 0,
      "event_id": 0,
      "temperature_c": 3,
      "raw_temperature": 0,
      "lat": 0
    },
    "outliers": [],
    "imputations": {
      "temperature_c": {
        "method": "median",
        "filled": 3,
        "value": 23.27
      }
    },
    "removed_by_missing": 0,
    "kept": 4
  }
}
```