```json
{
  "cleaned_data": [
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.0,
      "lon": 67.0,
      "timestamp": "2025-10-31T18:17:56.329390+00:00",
      "temperature_c": null,
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
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.0,
      "lon": 67.0,
      "timestamp": "2025-10-31T18:17:57.234323+00:00",
      "temperature_c": null,
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
    },
    {
      "id": "unknown",
      "event_id": "unknown",
      "lat": 24.0,
      "lon": 67.0,
      "timestamp": "2025-10-31T18:17:58.155390+00:00",
      "temperature_c": null,
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
  "validation_report": {
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
      "temperature_c": 3,
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
        "value": "NaN"
      }
    },
    "removed_by_missing": 0,
    "kept": 3,
    "recommendations": [
      "Add sensor registration metadata when possible to reduce inference reliance."
    ],
    "resolutions": [
      "No records were dropped due to missing values (missing percentage below 50%).",
      "No duplicate records were found based on 'lat', 'lon', and 'timestamp'.",
      "Imputation for 'temperature_c' was attempted using the median method, but no values were filled as all were missing, resulting in 'NaN' for the imputed value.",
      "Identifiers 'id' and 'event_id' remained 'unknown' as they were treated as existing values, not missing ones for auto-generation (auto_id_count: 0)."
    ]
  }
}
```