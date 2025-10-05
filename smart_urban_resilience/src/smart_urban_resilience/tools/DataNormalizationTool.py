import logging
import datetime
from typing import Any, Dict, List, Optional, Tuple, Type
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from timezonefinder import TimezoneFinder
import geopy
from geopy.geocoders import Nominatim


# ----------------- Input Schema -----------------
class DataNormalizationToolInput(BaseModel):
    records: List[Dict[str, Any]] = Field(
        ..., description="List of raw data records to normalize."
    )
    dedupe: bool = Field(
        default=True,
        description="Whether to perform deduplication on normalized records."
    )


# ----------------- Tool Class -----------------
class DataNormalizationTool(BaseTool):
    name: str = "Data Normalization Tool"
    description: str = (
        "Cleans, standardizes, and enriches raw sensor or citizen data by normalizing coordinates, "
        "timestamps, temperature units, and basic metadata."
    )
    args_schema: Type[BaseModel] = DataNormalizationToolInput

    def _run(self, records: List[Dict[str, Any]], dedupe: bool = True) -> Dict[str, Any]:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("DataNormalizer")

        logger.info(f"[DataNormalizationTool] Normalizing {len(records)} records (dedupe={dedupe})")

        normalized, errors = [], []
        seen = set()

        for rec in records:
            try:
                lat, lon = self._extract_latlon(rec)
                if lat is None or lon is None:
                    raise ValueError("Missing or invalid coordinates")

                timestamp = self._extract_timestamp(rec)
                temperature_c = self._extract_temperature(rec)
                event_id = str(rec.get("id", rec.get("event_id", "unknown")))

                # Reverse geocode city name (localized)
                geolocator = Nominatim(user_agent="smart_urban_resilience")
                location = geolocator.reverse(f"{lat}, {lon}", language="en", timeout=10)
                city_name = location.raw["address"].get("city", location.address) if location else "Unknown"

                normalized_rec = {
                    "id": event_id,
                    "event_id": event_id,
                    "lat": lat,
                    "lon": lon,
                    "timestamp": timestamp,
                    "temperature_c": temperature_c,
                    "location": {
                        "latitude": lat,
                        "longitude": lon,
                        "city": city_name
                    },
                    "raw_temperature": {
                        "temp_f": rec.get("temp_f"),
                        "temperature": rec.get("temperature")
                    }
                }

                # Deduplication logic
                if dedupe:
                    sig = (round(lat, 3), round(lon, 3), timestamp)
                    if sig in seen:
                        continue
                    seen.add(sig)

                normalized.append(normalized_rec)

            except Exception as e:
                errors.append({"record": rec, "error": str(e)})
                logger.error(f"Error normalizing record {rec.get('id')}: {e}")

        result = {
            "normalized": normalized,
            "errors": errors,
            "stats": {
                "input_count": len(records),
                "kept": len(normalized),
                "deduped": len(records) - len(normalized) if dedupe else 0,
                "errors": len(errors)
            }
        }
        return result

    # ----------------- Helper Methods -----------------
    def _extract_latlon(self, rec: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Try common key names and nested structures for coordinates."""
        keys = [
            ("lat", "lon"),
            ("latitude", "longitude"),
            ("lat", "lng"),
            ("Latitude", "Longitude")
        ]

        def lookup(k: str) -> Optional[Any]:
            if k in rec:
                return rec[k]
            for v in rec.values():
                if isinstance(v, dict) and k in v:
                    return v[k]
            return None

        for latk, lonk in keys:
            lat_val = lookup(latk)
            lon_val = lookup(lonk)
            try:
                lat_f = float(lat_val) if lat_val is not None else None
                lon_f = float(lon_val) if lon_val is not None else None
                if lat_f is not None and lon_f is not None:
                    return lat_f, lon_f
            except (TypeError, ValueError):
                continue

        return None, None

    def _extract_timestamp(self, rec: Dict[str, Any]) -> str:
        """Extract timestamp safely with UTC awareness."""
        ts_value = rec.get("timestamp") or rec.get("time") or rec.get("datetime")
        try:
            if isinstance(ts_value, (int, float)):
                dt = datetime.datetime.fromtimestamp(float(ts_value), tz=datetime.UTC)
            elif isinstance(ts_value, str):
                dt = datetime.datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
            else:
                dt = datetime.datetime.now(datetime.UTC)
            return dt.astimezone(ZoneInfo("UTC")).isoformat()
        except Exception:
            return datetime.datetime.now(datetime.UTC).isoformat()

    def _extract_temperature(self, rec: Dict[str, Any]) -> Optional[float]:
        """Normalize temperature to Celsius."""
        if "temperature" in rec:
            return float(rec["temperature"])
        if "temp_f" in rec:
            return round((float(rec["temp_f"]) - 32) * 5 / 9, 2)
        return None


# ----------------- JSON Schema Export -----------------
def get_tool_schema() -> Dict[str, Any]:
    """Return JSON schema for the DataNormalizationTool input."""
    return DataNormalizationToolInput.schema_json(indent=2)


if __name__ == "__main__":
    import json

    # Example test run
    sample_data = [
        {"id": "r1", "lat": 24.8607, "lon": 67.0011, "temperature": 89.0, "timestamp": "2025-10-05T12:00:00"},
        {"id": "r2", "location": {"lat": 24.86, "lng": 67.01}, "temp_f": 77.0, "time": 1696516800},
        {"id": "r3", "latitude": "invalid", "longitude": None, "temp_f": 70.0}
    ]

    tool = DataNormalizationTool()
    result = tool._run(sample_data)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\nJSON Schema:")
    print(get_tool_schema())
