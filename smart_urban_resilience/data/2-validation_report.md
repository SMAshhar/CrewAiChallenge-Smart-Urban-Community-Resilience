```json
{
  "cleaned": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 34.0,
      "lon": 118.0,
      "timestamp": "2025-10-27T08:27:32.710300+00:00",
      "temperature_c": 36.5,
      "location": {
        "latitude": 34.0,
        "longitude": 118.0,
        "city": "Suining County"
      },
      "raw_temperature": {
        "temp_f": null,
        "temperature": 36.5
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
    "duplicate_examples": [
      {
        "lat": 34.0,
        "lon": 118.0
      },
      {
        "lat": 34.0,
        "lon": 118.0
      }
    ],
    "outliers": [],
    "imputations": {
      "temperature_c": {
        "method": "median",
        "filled": 2,
        "value": 36.5
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