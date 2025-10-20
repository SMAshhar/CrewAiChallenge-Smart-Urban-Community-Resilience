from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import requests
import random
import logging


logging.basicConfig(level=logging.INFO)

class DataFetchToolInput(BaseModel):
    """
    ====================================================================
    📘 TOOL DOCUMENTATION — DataFetchTool
    ====================================================================

    **Tool Name:** DataFetchTool  
    **Purpose:** 
    Fetches environmental, weather, air quality, pollen, UV index, and hazard data 
    from public APIs (Open-Meteo) with graceful simulation fallbacks for unavailable data.

    **Primary Role in the SmartUrbanCommunity System:**
    This tool supports the `data_collector` agent by providing a unified, normalized 
    data-fetching interface for environmental and weather intelligence. It ensures that 
    real-time or simulated urban environment data is always available for analysis and validation.

    ====================================================================
    🧩 CAPABILITIES
    ====================================================================
    1. **Weather Data Fetching**
    - Retrieves temperature, humidity, precipitation, wind speed, and cloud cover 
        from Open-Meteo’s free forecast API.
    - Provides simulated fallback if live fetch fails.

    2. **Air Quality Data Fetching**
    - Retrieves key pollutants (PM10, PM2.5, CO, O₃) and AQI index 
        via Open-Meteo Air Quality API.
    - Automatically switches to simulated values on failure.

    3. **Environmental Hazards & Health Data**
    - Fetches UV index, grass/tree/weed pollen levels, and wildfire risk.
    - Flood risk is simulated (no global free API).
    - Designed to help downstream agents assess city health, allergy risk, and safety.

    4. **Resilience & Fallback System**
    - When any network/API request fails, this tool generates realistic 
        synthetic data using statistical ranges.
    - The output structure remains consistent between real and simulated modes.

    5. **Comprehensive Master Fetch**
    - The `fetch_all()` method orchestrates all sub-fetches into a unified JSON output.
    - Provides structured, timestamped, and source-tagged data ready for validation.

    ====================================================================
    📦 OUTPUT FORMAT
    ====================================================================

    The unified dictionary returned by `fetch_all()` looks like this:

    {
    "weather": {
        "temperature": 33.2,
        "humidity": 45,
        "precipitation": 0.3,
        "cloud_cover": 56,
        "wind_speed": 3.5,
        "source": "Open-Meteo",
        "timestamp": "2025-10-05T12:03:21Z"
    },
    "air_quality": {
        "aqi": 87,
        "pm10": 45.6,
        "pm2_5": 21.3,
        "carbon_monoxide": 0.8,
        "ozone": 63.2,
        "source": "Open-Meteo Air Quality",
        "timestamp": "2025-10-05T12:03:22Z"
    },
    "environment": {
        "uv_index": 6.2,
        "grass_pollen": 70,
        "tree_pollen": 120,
        "weed_pollen": 40,
        "wildfire_risk": 10,
        "flood_risk": 45,
        "source": "Open-Meteo Environment + Simulated Flood",
        "timestamp": "2025-10-05T12:03:23Z"
    }
    }

    ====================================================================
    🧠 AGENTIC BEHAVIOR HINTS
    ====================================================================

    **Best Suited Agent(s):**
    - `data_collector`
    - `data_validator` (for cross-checking)

    **When to Use:**
    - When the agent needs **fresh or simulated environmental context**.
    - When other data sources fail or latency is acceptable.
    - When validating environmental impacts on city livability, risk scores, or citizen alerts.

    **When Not to Use:**
    - In real-time emergency response systems requiring <5s latency.
    - When the agent already has a local data stream from city APIs.

    **Expected Follow-Up Tools:**
    - `DataNormalizerTool` → for unifying schema & scale normalization
    - `DataStorageTool` → for persisting cleaned results
    - `EventDetectionTool` → for detecting hazard events (flood/fire/pollution spikes)

    ====================================================================
    ⚙️ DESIGN CHOICES & NOTES
    ====================================================================
    - Built on top of **Open-Meteo APIs** (free, no API key required)
    - Resilient to API downtime via simulated fallbacks
    - Compatible with CrewAI tool registration as `Tool(name="DataFetchTool", func=fetch_all)`
    - Lightweight, stateless, and deterministic output structure

    ====================================================================
    ✅ SUMMARY
    ====================================================================
    This tool ensures that SmartUrbanCommunity always has access to a reliable and normalized feed 
    of environmental and weather data — whether online or offline. It’s the foundation for 
    higher-level analytics like anomaly detection, city alerts, and public health correlation.

    ====================================================================
    """


    """Input schema for DataFetchTool."""
    latitude: float = Field(24.8607, description="Latitude of the city location.")
    longitude: float = Field(67.0011, description="Longitude of the city location.")
    data_type: Optional[str] = Field(
        "all",
        description="Specify which data to fetch: 'weather', 'air_quality', 'environment', or 'all'.",
    )


# ------------------- Tool Definition -------------------
class DataFetchTool(BaseTool):
    name: str = "Urban Data Fetch Tool"
    description: str = (
        "Fetches live or simulated environmental data (weather, air quality, pollen, UV index, "
        "wildfire, and flood risk) using free APIs from Open-Meteo. "
        "If APIs are unavailable, it generates realistic simulated data."
    )
    args_schema: Type[BaseModel] = DataFetchToolInput

    def _get_city_from_coords(self, latitude: float, longitude: float) -> str:
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
            headers = {"User-Agent": "SmartUrbanCommunity/1.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("address", {}).get("city") or data.get("address", {}).get("town") or data.get("address", {}).get("village") or "Unknown"
        except Exception as e:
            logging.warning(f"[Geocoding] Failed to resolve city: {e}")
            return "Unknown"


    def _run(self, latitude: float, longitude: float, data_type: str = "all") -> dict:
        logging.info(f"[DataFetchTool] Running data fetch for {data_type} @ ({latitude}, {longitude})")

        # API Base URLs
        base_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current="
        weather_url = base_url + "temperature_2m,humidity_2m,precipitation,cloud_cover,wind_speed_10m"
        air_quality_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={latitude}&longitude={longitude}&current=european_aqi,pm10,pm2_5,carbon_monoxide,ozone"
        environment_url = base_url + "uv_index,grass_pollen,tree_pollen,weed_pollen,wildfire_risk"

        # Selective execution
        result = {}
        if data_type in ["weather", "all"]:
            result["weather"] = self._fetch_weather(weather_url)
        if data_type in ["air_quality", "all"]:
            result["air_quality"] = self._fetch_air_quality(air_quality_url)
        if data_type in ["environment", "all"]:
            result["environment"] = self._fetch_environment(environment_url)

        return result

    # ------------------- Internal Fetchers -------------------
    def _fetch_weather(self, url: str) -> dict:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            return {
                "temperature": current.get("temperature_2m", 0),
                "humidity": current.get("humidity_2m", 0),
                "precipitation": current.get("precipitation", 0),
                "cloud_cover": current.get("cloud_cover", 0),
                "wind_speed": current.get("wind_speed_10m", 0),
                "source": "Open-Meteo",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logging.warning(f"[Weather] API failed: {e}")
            return self._simulate_weather()
        

    def _fetch_air_quality(self, url: str) -> dict:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            return {
                "aqi": current.get("european_aqi", 0),
                "pm10": current.get("pm10", 0),
                "pm2_5": current.get("pm2_5", 0),
                "carbon_monoxide": current.get("carbon_monoxide", 0),
                "ozone": current.get("ozone", 0),
                "source": "Open-Meteo Air Quality",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logging.warning(f"[Air Quality] API failed: {e}")
            return self._simulate_air_quality()

    def _fetch_environment(self, url: str) -> dict:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            return {
                "uv_index": current.get("uv_index", 0),
                "grass_pollen": current.get("grass_pollen", 0),
                "tree_pollen": current.get("tree_pollen", 0),
                "weed_pollen": current.get("weed_pollen", 0),
                "wildfire_risk": current.get("wildfire_risk", 0),
                "flood_risk": self._simulate_flood_risk(),
                "source": "Open-Meteo Environment + Simulated Flood",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logging.warning(f"[Environment] API failed: {e}")
            return self._simulate_environment()

    # ------------------- Simulators -------------------
    def _simulate_weather(self) -> dict:
        return {
            "temperature": round(random.uniform(22, 38), 2),
            "humidity": random.randint(30, 80),
            "precipitation": round(random.uniform(0, 10), 2),
            "cloud_cover": random.randint(10, 90),
            "wind_speed": round(random.uniform(0.5, 6.5), 2),
            "source": "Simulated",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _simulate_air_quality(self) -> dict:
        return {
            "aqi": random.randint(50, 180),
            "pm10": round(random.uniform(20, 200), 2),
            "pm2_5": round(random.uniform(10, 150), 2),
            "carbon_monoxide": round(random.uniform(0.1, 1.2), 2),
            "ozone": round(random.uniform(20, 120), 2),
            "source": "Simulated",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _simulate_environment(self) -> dict:
        return {
            "uv_index": round(random.uniform(3, 9), 1),
            "grass_pollen": random.randint(0, 200),
            "tree_pollen": random.randint(0, 300),
            "weed_pollen": random.randint(0, 150),
            "wildfire_risk": random.randint(0, 100),
            "flood_risk": self._simulate_flood_risk(),
            "source": "Simulated",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _simulate_flood_risk(self) -> int:
        return random.randint(0, 100)


# ------------------- Manual Test -------------------
if __name__ == "__main__":
    tool = DataFetchTool()
    output = tool._run(latitude=24.86, longitude=67.00, data_type="all")
    print(output)

# DataFetchTool_v2.py
# """
# DataFetchTool v2 - Real-data focussed (no simulated values)
# - Uses Open-Meteo (weather, UV, pollen, soil moisture)
# - Uses Open-Meteo Air Quality (modeled AQ)
# - Optionally augments AQ with OpenAQ station measurements
# - Uses NASA FIRMS detections to compute wildfire risk
# - Computes a flood-risk proxy from precipitation (24h) + soil moisture
# - Uses Nominatim reverse geocoding (cached, polite User-Agent)
# - Returns structured dictionary with provenance, timestamps, and error info

# Outputs explicitly avoid simulated numbers. If a field cannot be produced, its value is None,
# and the 'status' field for that block will explain why.
# """
# from typing import Type, Optional, Dict, Any, List, Tuple
# from pydantic import BaseModel, Field
# from datetime import datetime, timedelta
# import requests
# import logging
# import math
# import time
# from functools import lru_cache
# from crewai.tools import BaseTool

# # If integrated with CrewAI:
# try:
#     from crewai.tools import BaseTool
# except Exception:
#     # minimal fallback BaseTool for local testing if crewai not present
#     class BaseTool:
#         name: str
#         description: str
#         args_schema = BaseModel

#         def __init__(self):
#             pass

#         def run(self, *args, **kwargs):
#             return self._run(*args, **kwargs)


# # -------------- CONFIG --------------
# USER_AGENT = "SmartUrbanCommunity/1.0 (+https://example.org) DataFetchTool/2.0"
# REQUEST_TIMEOUT = 12  # seconds
# OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"
# OPEN_METEO_AQ_BASE = "https://air-quality-api.open-meteo.com/v1/air-quality"
# OPENAQ_BASE = "https://api.openaq.org/v2/measurements"
# NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
# NASA_FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"  # placeholder pattern; will use public CSV endpoint pattern
# LOG = logging.getLogger("DataFetchTool")
# LOG.setLevel(logging.INFO)
# # ------------------------------------

# class DataFetchToolInput(BaseModel):
#     latitude: float = Field(..., description="Latitude of the location")
#     longitude: float = Field(..., description="Longitude of the location")
#     data_type: Optional[str] = Field("all", description="Which block: 'weather', 'air_quality', 'environment', or 'all'")
#     use_openaq: Optional[bool] = Field(True, description="Attempt to augment AQ with OpenAQ station data when available")
#     wildfire_hours: Optional[int] = Field(24, description="Time range (hours) to consider for active-fire detections")
#     flood_precip_hours: Optional[int] = Field(24, description="Precipitation window (hours) to sum for flood proxy")


# class DataFetchTool(BaseTool):
#     name = "Data Fetch Tool"
#     description = "Fetches real environmental data (Open-Meteo, Open-Meteo Air Quality, OpenAQ, NASA FIRMS). No simulated data."
#     args_schema = DataFetchToolInput

#     def __init__(self):
#         super().__init__()
#         self.session = requests.Session()
#         self.session.headers.update({"User-Agent": USER_AGENT})
#         # small backoff settings
#         self.max_retries = 2

#     # ---------- Public runner ----------
#     def _run(self, latitude: float, longitude: float, data_type: str = "all",
#              use_openaq: bool = True, wildfire_hours: int = 24, flood_precip_hours: int = 24) -> dict:
#         """
#         Orchestrator. Returns unified dict:
#         {
#           "weather": {..., "status": "ok"|"partial"|"unavailable", "errors": [...]},
#           "air_quality": {..., "status": ..., "errors": [...]},
#           "environment": {..., "status": ..., "errors": [...]},
#           "metadata": {...}
#         }
#         """
#         LOG.info(f"[_run] fetch {data_type} @ ({latitude},{longitude}) use_openaq={use_openaq}")

#         out: Dict[str, Any] = {"metadata": {"requested_at": datetime.utcnow().isoformat(), "lat": latitude, "lon": longitude}}

#         # Resolve city (best-effort; cached)
#         city = self._reverse_geocode_cached(latitude, longitude)
#         out["metadata"]["city"] = city

#         errors_global: List[str] = []

#         # Weather block
#         if data_type in ("weather", "all"):
#             try:
#                 out["weather"] = self._fetch_weather_block(latitude, longitude)
#             except Exception as e:
#                 LOG.exception("Weather block failed")
#                 out["weather"] = {"status": "unavailable", "errors": [str(e)], "source": None}
#                 errors_global.append(f"weather: {e}")

#         # Air quality block
#         if data_type in ("air_quality", "all"):
#             try:
#                 out["air_quality"] = self._fetch_air_quality_block(latitude, longitude, use_openaq=use_openaq)
#             except Exception as e:
#                 LOG.exception("Air quality block failed")
#                 out["air_quality"] = {"status": "unavailable", "errors": [str(e)], "source": None}
#                 errors_global.append(f"air_quality: {e}")

#         # Environment block (UV, pollen, wildfire, flood)
#         if data_type in ("environment", "all"):
#             try:
#                 out["environment"] = self._fetch_environment_block(latitude, longitude,
#                                                                    wildfire_hours=wildfire_hours,
#                                                                    flood_precip_hours=flood_precip_hours)
#             except Exception as e:
#                 LOG.exception("Environment block failed")
#                 out["environment"] = {"status": "unavailable", "errors": [str(e)], "source": None}
#                 errors_global.append(f"environment: {e}")

#         out["metadata"]["errors"] = errors_global
#         return out

#     # ---------- Reverse geocode (cached) ----------
#     @lru_cache(maxsize=1024)
#     def _reverse_geocode_cached(self, lat: float, lon: float) -> str:
#         # use rounded coords to improve cache hits
#         return self._reverse_geocode(round(lat, 4), round(lon, 4))

#     def _reverse_geocode(self, lat: float, lon: float) -> str:
#         params = {"format": "json", "lat": lat, "lon": lon, "addressdetails": 1}
#         try:
#             resp = self.session.get(NOMINATIM_REVERSE, params=params, timeout=REQUEST_TIMEOUT)
#             resp.raise_for_status()
#             j = resp.json()
#             address = j.get("address", {})
#             city = address.get("city") or address.get("town") or address.get("village") or address.get("municipality")
#             return city or "Unknown"
#         except Exception as e:
#             LOG.warning(f"[Geocode] failed: {e}")
#             return "Unknown"

#     # ---------- Weather ----------
#     def _fetch_weather_block(self, lat: float, lon: float) -> dict:
#         """
#         Fetch current weather: temperature_2m, humidity_2m, precipitation, cloud_cover, wind_speed_10m
#         Additionally fetch hourly precipitation sum for flood proxy (done in environment block).
#         """
#         fields = ["temperature_2m", "humidity_2m", "precipitation", "cloud_cover", "wind_speed_10m"]
#         params = {
#             "latitude": lat,
#             "longitude": lon,
#             "current": ",".join(fields),
#             "timezone": "UTC",
#         }
#         url = OPEN_METEO_BASE
#         errors = []
#         for attempt in range(self.max_retries):
#             try:
#                 resp = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
#                 resp.raise_for_status()
#                 j = resp.json()
#                 current = j.get("current", {})
#                 # Map fields, return None when not present
#                 data = {
#                     "temperature": current.get("temperature_2m"),
#                     "humidity": current.get("humidity_2m"),
#                     "precipitation": current.get("precipitation"),
#                     "cloud_cover": current.get("cloud_cover"),
#                     "wind_speed": current.get("wind_speed_10m"),
#                     "source": "Open-Meteo",
#                     "fetched_at": datetime.utcnow().isoformat(),
#                     "status": "ok" if current else "partial" if j else "unavailable",
#                     "errors": []
#                 }
#                 # if no current, indicate partial/unavailable
#                 if not current:
#                     data["status"] = "unavailable"
#                     data["errors"].append("Open-Meteo returned no 'current' block for weather")
#                 return data
#             except requests.RequestException as e:
#                 LOG.warning(f"[Weather] attempt {attempt+1} failed: {e}")
#                 errors.append(str(e))
#                 time.sleep(1 + attempt)
#             except Exception as e:
#                 LOG.exception("[Weather] unexpected")
#                 errors.append(str(e))
#                 break

#         return {"status": "unavailable", "source": None, "errors": errors,
#                 "temperature": None, "humidity": None, "precipitation": None, "cloud_cover": None, "wind_speed": None}

#     # ---------- Air Quality ----------
#     def _fetch_air_quality_block(self, lat: float, lon: float, use_openaq: bool = True) -> dict:
#         """
#         1) Fetch modeled AQ from Open-Meteo Air Quality
#         2) If use_openaq=True, attempt to fetch nearest station measurement and prefer it if recent.
#         """
#         errors: List[str] = []
#         aq_data = {"aqi": None, "pm10": None, "pm2_5": None, "carbon_monoxide": None, "ozone": None,
#                    "source": None, "fetched_at": datetime.utcnow().isoformat(), "status": None, "errors": []}

#         # 1) Open-Meteo modeled AQ
#         params = {"latitude": lat, "longitude": lon, "current": "european_aqi,pm10,pm2_5,carbon_monoxide,ozone", "timezone": "UTC"}
#         try:
#             resp = self.session.get(OPEN_METEO_AQ_BASE, params=params, timeout=REQUEST_TIMEOUT)
#             resp.raise_for_status()
#             j = resp.json()
#             current = j.get("current", {})
#             if current:
#                 aq_data.update({
#                     "aqi": current.get("european_aqi"),
#                     "pm10": current.get("pm10"),
#                     "pm2_5": current.get("pm2_5"),
#                     "carbon_monoxide": current.get("carbon_monoxide"),
#                     "ozone": current.get("ozone"),
#                     "source": "Open-Meteo Air Quality",
#                     "status": "ok",
#                 })
#             else:
#                 aq_data["status"] = "unavailable"
#                 aq_data["errors"].append("Open-Meteo Air Quality returned no 'current' block")
#         except Exception as e:
#             LOG.warning(f"[AirQuality] Open-Meteo failed: {e}")
#             errors.append(f"open-meteo:{e}")

#         # 2) Optionally check OpenAQ for nearby station data and prefer it if recent and complete
#         if use_openaq:
#             try:
#                 station = self._fetch_nearest_openaq(lat, lon, radius_m=5000)
#                 if station and self._is_openaq_recent_enough(station):
#                     # override only the fields present in station
#                     values = station.get("values", {})
#                     # convert key names from OpenAQ to our fields
#                     if "pm25" in values and values["pm25"] is not None:
#                         aq_data["pm2_5"] = values["pm25"]
#                     if "pm10" in values and values["pm10"] is not None:
#                         aq_data["pm10"] = values["pm10"]
#                     if "co" in values and values["co"] is not None:
#                         aq_data["carbon_monoxide"] = values["co"]
#                     if "o3" in values and values["o3"] is not None:
#                         aq_data["ozone"] = values["o3"]
#                     # compute aqi if provider supplies or leave None (OpenAQ provides measured values but not a uniform AQI)
#                     aq_data["source"] = f"Open-Meteo Air Quality + OpenAQ ({station.get('station_id')})"
#                     aq_data["status"] = "ok"
#             except Exception as e:
#                 LOG.warning(f"[AirQuality] OpenAQ augmentation failed: {e}")
#                 errors.append(f"openaq:{e}")

#         # prepare final status
#         if aq_data["status"] is None:
#             # we had no Open-Meteo and no OpenAQ
#             aq_data["status"] = "unavailable"
#             if not aq_data["errors"]:
#                 aq_data["errors"] = errors or ["No data sources succeeded"]
#         else:
#             # add any collected errors as warnings
#             if errors:
#                 aq_data.setdefault("errors", []).extend(errors)

#         return aq_data

#     def _fetch_nearest_openaq(self, lat: float, lon: float, radius_m: int = 5000) -> Optional[dict]:
#         """
#         Query OpenAQ measurements endpoint for nearest valid station measurement.
#         Returns a dict with 'station_id', 'location', 'values' (pm25, pm10, co, o3), 'timestamp'
#         """
#         params = {
#             "coordinates": f"{lat},{lon}",
#             "radius": radius_m,
#             "limit": 20,
#             "order_by": "distance",
#             "sort": "asc",
#         }
#         resp = self.session.get(OPENAQ_BASE, params=params, timeout=REQUEST_TIMEOUT)
#         resp.raise_for_status()
#         j = resp.json()
#         results = j.get("results", [])
#         if not results:
#             return None

#         # aggregate latest per parameter from nearest station(s) - take the nearest location id with multiple params
#         # we'll pick the first location that has at least one of PM2.5 or PM10
#         for item in results:
#             location = item.get("location")
#             params_list = item.get("parameter")
#             # OpenAQ v2 returns results as individual measurements; for simplicity use the returned result as single param
#             # Better: call locations endpoint or measurements with parameter filtering. Here treat this result as a single measurement.
#             # To keep it robust, construct a simple wrapper:
#             measurement = {
#                 "station_id": item.get("location"),
#                 "location": item.get("coordinates"),
#                 "values": {item.get("parameter"): item.get("value")},
#                 "timestamp": item.get("date", {}).get("utc"),
#             }
#             # return the first meaningful measurement
#             return measurement
#         return None

#     @staticmethod
#     def _is_openaq_recent_enough(station_measurement: dict, max_age_minutes: int = 180) -> bool:
#         ts = station_measurement.get("timestamp")
#         if not ts:
#             return False
#         try:
#             dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
#             return (datetime.utcnow() - dt) <= timedelta(minutes=max_age_minutes)
#         except Exception:
#             return False

#     # ---------- Environment: UV, pollen, wildfire, flood proxy ----------
#     def _fetch_environment_block(self, lat: float, lon: float, wildfire_hours: int = 24, flood_precip_hours: int = 24) -> dict:
#         """
#         - UV and pollen via Open-Meteo environment vars (if available)
#         - soil_moisture + precipitation hourly used to compute flood proxy
#         - wildfire risk computed from NASA FIRMS active fire detections
#         """
#         errors: List[str] = []
#         env_out = {
#             "uv_index": None,
#             "grass_pollen": None,
#             "tree_pollen": None,
#             "weed_pollen": None,
#             "wildfire_risk": None,
#             "wildfire_meta": None,
#             "flood_risk": None,
#             "flood_meta": None,
#             "source": None,
#             "fetched_at": datetime.utcnow().isoformat(),
#             "status": None,
#             "errors": []
#         }

#         # --- Fetch Open-Meteo current + hourly for soil moisture/precip window + uv/pollen if provided ---
#         # request both current and hourly precipitation & soil moisture (hourly arrays) to compute sums over last N hours
#         env_vars_current = ["uv_index", "grass_pollen", "tree_pollen", "weed_pollen"]
#         env_vars_hourly = ["precipitation", "soil_moisture"]  # soil_moisture variable name depends on provider; Open-Meteo supports near-surface soil moisture 'soil_moisture_0_1cm' etc. Here we'll try 'soil_moisture'
#         params = {
#             "latitude": lat,
#             "longitude": lon,
#             "current": ",".join(env_vars_current),
#             "hourly": ",".join(env_vars_hourly),
#             "timezone": "UTC"
#         }
#         errors_local = []
#         try:
#             resp = self.session.get(OPEN_METEO_BASE, params=params, timeout=REQUEST_TIMEOUT)
#             resp.raise_for_status()
#             j = resp.json()
#             # UV / pollen from current
#             current = j.get("current", {})
#             hourly = j.get("hourly", {})
#             # map uv and pollen
#             env_out["uv_index"] = current.get("uv_index")
#             env_out["grass_pollen"] = current.get("grass_pollen")
#             env_out["tree_pollen"] = current.get("tree_pollen")
#             env_out["weed_pollen"] = current.get("weed_pollen")
#             env_out["source"] = "Open-Meteo"
#             env_out["status"] = "ok"
#         except Exception as e:
#             LOG.warning(f"[Environment] Open-Meteo current/hourly failed: {e}")
#             errors_local.append(str(e))
#             env_out["status"] = "partial"  # we may still compute wildfire/flood

#         # --- Compute precipitation sum over requested hours ---
#         precip_sum_hrs = None
#         soil_moisture_latest = None
#         try:
#             if hourly:
#                 times = hourly.get("time", [])
#                 precip_arr = hourly.get("precipitation", [])
#                 soil_arr = hourly.get("soil_moisture", []) or hourly.get("soil_moisture_0_1cm", []) or hourly.get("soil_moisture_0_7cm", [])
#                 # find last N hours from the end
#                 if precip_arr and times:
#                     # sum last flood_precip_hours elements (assuming hourly aligned)
#                     n = min(len(precip_arr), flood_precip_hours)
#                     precip_sum_hrs = sum(float(x) for x in precip_arr[-n:])
#                 if soil_arr:
#                     # take latest available
#                     soil_moisture_latest = float(soil_arr[-1])
#         except Exception as e:
#             LOG.warning(f"[Environment] computing precip/soil_moisture failed: {e}")
#             errors_local.append(str(e))

#         # --- Flood risk proxy ---
#         try:
#             flood_score, flood_meta = self._compute_flood_proxy(precip_sum_hrs, soil_moisture_latest, precip_window_hours=flood_precip_hours)
#             env_out["flood_risk"] = flood_score
#             env_out["flood_meta"] = flood_meta
#         except Exception as e:
#             LOG.warning(f"[Environment] flood proxy failed: {e}")
#             errors_local.append(str(e))

#         # --- Wildfire risk using NASA FIRMS detections ---
#         try:
#             detections = self._fetch_firms_detections(lat, lon, hours=wildfire_hours)
#             if detections is not None:
#                 wildfire_score, wildfire_meta = self._compute_wildfire_risk_from_detections(detections, lat, lon)
#                 env_out["wildfire_risk"] = wildfire_score
#                 env_out["wildfire_meta"] = wildfire_meta
#             else:
#                 env_out["wildfire_risk"] = None
#                 env_out["wildfire_meta"] = {"note": "FIRMS data unavailable"}
#                 errors_local.append("FIRMS returned no detections or was unavailable")
#         except Exception as e:
#             LOG.warning(f"[Environment] FIRMS/wildfire failed: {e}")
#             errors_local.append(str(e))

#         # consolidate errors
#         env_out["errors"] = errors_local
#         if env_out["status"] != "ok" and errors_local:
#             env_out["status"] = "partial" if any([env_out.get(k) for k in ["wildfire_risk", "flood_risk", "uv_index"]]) else "unavailable"

#         return env_out

#     def _compute_flood_proxy(self, precip_sum_mm: Optional[float], soil_moisture: Optional[float], precip_window_hours: int = 24) -> Tuple[Optional[int], dict]:
#         """
#         Compute a 0-100 flood risk proxy using:
#          - recent precipitation sum over window (mm)
#          - relative soil moisture (0-1 or volumetric; interpret defensively)

#         Heuristic (MVP):
#          - if precip_sum is None -> cannot compute -> return None
#          - Normalize precip into 0-70 weight, soil moisture into 0-30 weight.
#          - precip_score = min(70, (precip_sum_mm / threshold_mm) * 70)
#              where threshold_mm = 50mm for 24h window (configurable)
#          - soil_score = min(30, soil_moisture_normalized * 30)
#              where soil_moisture_normalized: if soil_moisture is in [0,0.5] treat as 0-1 scale; else heuristically clamp.
#          - final = clamp(0, 100, precip_score + soil_score)
#         """
#         meta = {"precip_sum_mm": precip_sum_mm, "soil_moisture": soil_moisture, "precip_window_hours": precip_window_hours}
#         if precip_sum_mm is None:
#             return None, {**meta, "note": "precipitation sum unavailable"}
#         # configurable thresholds
#         if precip_window_hours <= 24:
#             threshold_mm = 50.0  # 50 mm in 24h is heavy; adjust per region
#         else:
#             threshold_mm = 75.0
#         precip_score = min(70.0, (precip_sum_mm / threshold_mm) * 70.0)
#         # soil moisture normalization: attempt to interpret value; Open-Meteo soil moisture usually in m3/m3 (0-0.5)
#         soil_score = 0.0
#         if soil_moisture is not None:
#             # clamp and normalize
#             sm = float(soil_moisture)
#             # If soil moisture > 1, it's probably in percent scaled; normalize heuristically
#             if sm > 1.0:
#                 sm = sm / 100.0
#             sm_clamped = max(0.0, min(1.0, sm))
#             soil_score = min(30.0, sm_clamped * 30.0)
#         final = int(max(0, min(100, round(precip_score + soil_score))))
#         return final, {**meta, "precip_score": precip_score, "soil_score": soil_score, "final": final}

#     # ---------- FIRMS (NASA) integration ----------
#     def _fetch_firms_detections(self, lat: float, lon: float, hours: int = 24) -> Optional[List[dict]]:
#         """
#         Query NASA FIRMS for recent active fire detections near lat/lon within a certain time window.
#         NOTE: FIRMS offers multiple delivery mechanisms (CSV, GeoJSON) and there are public endpoints.
#         For this MVP we'll use a simple public CSV/GeoJSON pattern if available; if blocked, return None.

#         Implementation detail:
#         - FIRMS public data is often available as CSV files per region (MODIS/VIIRS). For a robust solution,
#           consider downloading the global VIIRS/Modis feed and filtering by distance/time locally.
#         """
#         try:
#             # concrete approach for MVP: use NASA FIRMS VIIRS/Modis point data via the "VIIRS" JSON might be available,
#             # but remote public API urls vary. As a resilient approach, attempt GeoJSON endpoints and fall back if not reachable.
#             # For this code, we'll attempt the MODIS/VIIRS JSON endpoints (these are commonly hosted) - if not reachable, return None.
#             # Example public URL patterns vary by deployment; we'll attempt a known FIRMS API URL for last 24h GeoJSON:
#             # NOTE: This is kept as a best-effort. For production, configure exact FIRMS endpoint & credentials if needed.
#             # We'll attempt to query the VIIRS all-satellite aggregated GeoJSON (this file often exists):
#             # https://firms.modaps.eosdis.nasa.gov/geojson/viirs/viirs-global-24h.geojson
#             geojson_url = f"https://firms.modaps.eosdis.nasa.gov/geojson/viirs/viirs-global-{hours}h.geojson"
#             resp = self.session.get(geojson_url, timeout=REQUEST_TIMEOUT)
#             if resp.status_code == 200:
#                 g = resp.json()
#                 features = g.get("features", [])
#                 detections = []
#                 # filter by distance threshold (e.g., 200 km)
#                 max_dist_km = 200
#                 for feat in features:
#                     prop = feat.get("properties", {})
#                     coords = feat.get("geometry", {}).get("coordinates")  # [lon, lat]
#                     if not coords:
#                         continue
#                     det_lon, det_lat = coords[0], coords[1]
#                     dist_km = self._haversine_km(lat, lon, det_lat, det_lon)
#                     if dist_km <= max_dist_km:
#                         detections.append({
#                             "latitude": det_lat,
#                             "longitude": det_lon,
#                             "acq_date": prop.get("acq_date"),
#                             "acq_time": prop.get("acq_time"),
#                             "confidence": prop.get("confidence"),
#                             "brightness": prop.get("brightness"),
#                             "dist_km": dist_km,
#                             "source": "FIRMS-viirs-24h"
#                         })
#                 return detections
#             else:
#                 LOG.warning(f"[FIRMS] geojson URL returned status {resp.status_code}")
#                 return None
#         except Exception as e:
#             LOG.warning(f"[FIRMS] fetch failed: {e}")
#             return None

#     def _compute_wildfire_risk_from_detections(self, detections: List[dict], lat: float, lon: float) -> Tuple[int, dict]:
#         """
#         Convert a list of FIRMS detections near the point into a 0-100 wildfire risk score.
#         Heuristic:
#           - score per detection = confidence_weight * distance_weight * brightness_weight
#           - confidence: if string like 'nominal' or percent -> attempt numeric; else map low/nominal/high to 0.5/0.8/1.0
#           - distance_weight = max(0.0, 1 - (dist_km / 200))  (200km influence cap)
#           - brightness normalized by expected range (e.g., 300-400 typical) -> clamp
#           - final = 100 * min(1, sum(detection_scores) / normalization_factor)
#         """
#         if not detections:
#             return 0, {"note": "no recent FIRMS detections within influence radius"}

#         total_score = 0.0
#         for d in detections:
#             conf = d.get("confidence")
#             # parse confidence
#             conf_val = 0.6
#             try:
#                 if isinstance(conf, (int, float)):
#                     conf_val = float(conf) / 100.0 if conf > 1 else float(conf)
#                 elif isinstance(conf, str):
#                     s = conf.lower()
#                     if s.isdigit():
#                         conf_val = float(s) / 100.0
#                     elif "high" in s:
#                         conf_val = 1.0
#                     elif "nominal" in s or "medium" in s:
#                         conf_val = 0.75
#                     elif "low" in s:
#                         conf_val = 0.5
#             except Exception:
#                 conf_val = 0.6
#             # distance weight
#             dist = d.get("dist_km", 200)
#             dist_w = max(0.0, 1.0 - (dist / 200.0))
#             # brightness weight
#             bright = d.get("brightness") or 0.0
#             bright_w = min(1.0, bright / 400.0)  # assume 400 is bright
#             det_score = conf_val * (0.5 * dist_w + 0.5 * bright_w)
#             total_score += det_score

#         # normalize: assume 10 strong detections near => high risk
#         norm = max(1.0, len(detections))
#         raw = total_score / norm
#         final = int(max(0, min(100, round(raw * 100))))
#         meta = {"n_detections": len(detections), "raw": raw, "detections_sample": detections[:5]}
#         return final, meta

#     # ---------- Utilities ----------
#     @staticmethod
#     def _haversine_km(lat1, lon1, lat2, lon2):
#         # returns distance in kilometers
#         R = 6371.0
#         phi1 = math.radians(lat1)
#         phi2 = math.radians(lat2)
#         dphi = math.radians(lat2 - lat1)
#         dlambda = math.radians(lon2 - lon1)
#         a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
#         return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# # -------------- Manual test --------------
# if __name__ == "__main__":
#     tool = DataFetchTool()
#     output = tool._run(latitude=24.8607, longitude=67.0011, data_type="all", use_openaq=True)
#     import json
#     print(json.dumps(output, indent=2, ensure_ascii=False))
