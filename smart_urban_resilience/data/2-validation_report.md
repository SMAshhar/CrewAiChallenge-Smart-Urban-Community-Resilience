```json
{
  "cleaned": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.86,
      "lon": 67.01,
      "timestamp": "2025-10-20T07:52:42.198433+00:00",
      "temperature_c": 26.81,
      "location": {
        "latitude": 24.86,
        "longitude": 67.01,
        "city": "Karachi Division"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": 26.81
      },
      "_meta": {
        "id_source": "original"
      }
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.86,
      "lon": 67.01,
      "timestamp": "2025-10-20T07:52:43.088446+00:00",
      "temperature_c": 26.81,
      "location": {
        "latitude": 24.86,
        "longitude": 67.01,
        "city": "Karachi Division"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": null
      },
      "_meta": {
        "id_source": "original"
      }
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.86,
      "lon": 67.01,
      "timestamp": "2025-10-20T07:52:43.832152+00:00",
      "temperature_c": 26.81,
      "location": {
        "latitude": 24.86,
        "longitude": 67.01,
        "city": "Karachi Division"
      },
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
    "input_count": 3,
    "auto_id_count": 0,
    "inferred_examples": [],
    "validator_issues": [],
    "missing_counts": {
      "id": 0,
      "event_id": 0,
      "lat": 0,
      "lon": 0,
      "timestamp": 0,
      "temperature_c": 2,
      "location": 0,
      "raw_temperature": 0,
      "_meta": 0
    },
    "duplicate_examples": [],
    "outliers": [],
    "imputations": {
      "lat": {
        "method": "median",
        "filled": 0,
        "value": 24.86
      },
      "lon": {
        "method": "median",
        "filled": 0,
        "value": 67.01
      },
      "temperature_c": {
        "method": "median",
        "filled": 2,
        "value": 26.81
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