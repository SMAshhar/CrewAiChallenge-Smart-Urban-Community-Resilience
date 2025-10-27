```json
{
  "cleaned": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.0,
      "lon": 67.0,
      "timestamp": "2025-10-27T20:31:08.282177+00:00",
      "temperature_c": NaN,
      "location": {
        "latitude": 24.0,
        "longitude": 67.0,
        "city": "Unknown"
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
      "temperature_c": 1,
      "location": 0,
      "raw_temperature": 0,
      "_meta": 0
    },
    "duplicate_examples": [],
    "outliers": [],
    "imputations": {
      "temperature_c": {
        "method": "median",
        "filled": 0,
        "value": NaN
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