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
