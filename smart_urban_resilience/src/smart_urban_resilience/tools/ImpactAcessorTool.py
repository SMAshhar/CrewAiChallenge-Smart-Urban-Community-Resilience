# src/smart_urban_resilience/tools/ImpactAssessmentTool.py
import json
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import datetime, timezone

# Optional spatial libs
try:
    import psycopg2
    print("psycopg2 imported successfully")
    HAVE_PG = True
except Exception:
    print("not available: psycopg2")
    psycopg2 = None
    HAVE_PG = False

try:
    import geopandas as gpd
    print("geopandas imported successfully")
    from shapely.geometry import Point
    print("shapely imported successfully")
    HAVE_GEOPANDAS = True
except Exception:
    gpd = None
    Point = None
    HAVE_GEOPANDAS = False

# light-weight fallback
import csv
from math import radians, sin, cos, sqrt, atan2

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("ImpactAssessmentTool")


# ----------------- Input schema -----------------
class ImpactAssessmentInput(BaseModel):
    detected_events: List[Dict[str, Any]] = Field(..., description="List of detected events with location and type.")
    geography: Optional[Dict[str, Any]] = Field(None, description="Optional config for PostGIS connection or local shapefiles.")
    population_layer_csv: Optional[str] = Field(None, description="Optional path to CSV with population grid (lat,lon,pop).")
    buffer_meters: Optional[float] = Field(500.0, description="Buffer radius (meters) around event location for impact estimation.")
    severity_config: Optional[Dict[str, Any]] = Field(None, description="Optional domain-specific thresholds to derive severity.")


# ----------------- Helper functions -----------------
def haversine_meters(lat1, lon1, lat2, lon2) -> float:
    # returns distance in meters
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2.0) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2.0) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def bbox_from_point(lat, lon, meters) -> Tuple[float, float, float, float]:
    # rough bounding box (degrees) — conservative
    # 1 deg lat ~ 111.32 km
    lat_deg = meters / 111320.0
    lon_deg = meters / (111320.0 * max(0.0001, cos(math.radians(lat))))
    return lat - lat_deg, lon - lon_deg, lat + lat_deg, lon + lon_deg


def load_population_grid(csv_path: str) -> List[Tuple[float, float, int]]:
    grid = []
    if not csv_path or not os.path.exists(csv_path):
        return grid
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        for r in rdr:
            try:
                lat = float(r.get("lat") or r.get("latitude"))
                lon = float(r.get("lon") or r.get("longitude"))
                pop = int(float(r.get("pop") or r.get("population") or 0))
                grid.append((lat, lon, pop))
            except Exception:
                continue
    return grid


def estimate_population_simple(lat: float, lon: float, radius_m: float, grid: List[Tuple[float, float, int]]) -> int:
    if not grid:
        return 0
    total = 0
    for glat, glon, pop in grid:
        try:
            if haversine_meters(lat, lon, glat, glon) <= radius_m:
                total += pop
        except Exception:
            continue
    return total


# ----------------- Tool -----------------
class ImpactAssessmentTool(BaseTool):
    name: str = "Impact Assessment Tool"
    description: str = (
        "Estimate spatial impact of detected events. Uses PostGIS when configured, falls back to GeoPandas/Shapely, "
        "and finally to a simple CSV-grid/haversine fallback. Returns severity, affected geometry summary, "
        "estimated population affected, infrastructure impact hints, and score breakdown."
    )
    args_schema: Type[BaseModel] = ImpactAssessmentInput

    def _run(
        self,
        detected_events: List[Dict[str, Any]],
        geography: Optional[Dict[str, Any]] = None,
        population_layer_csv: Optional[str] = None,
        buffer_meters: float = 500.0,
        severity_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        LOG.info(f"[ImpactAssessmentTool] Assessing {len(detected_events)} events (buffer={buffer_meters}m)")

        # load population grid (lightweight)
        pop_grid = load_population_grid(population_layer_csv) if population_layer_csv else []

        results = []
        for ev in detected_events:
            ev_loc = ev.get("location") or {}
            lat = None
            lon = None
            if isinstance(ev_loc, dict):
                lat = ev_loc.get("latitude") or ev_loc.get("lat")
                lon = ev_loc.get("longitude") or ev_loc.get("lon")
            try:
                lat = float(lat) if lat is not None else None
                lon = float(lon) if lon is not None else None
            except Exception:
                lat, lon = None, None

            # severity base on event type and any numeric risk in raw_record
            severity_score = self._derive_severity(ev, severity_config)

            affected = None
            est_pop = 0
            infra_impacted = []
            rationale = []

            # Prefer PostGIS if configured
            if geography and geography.get("postgis") and HAVE_PG:
                try:
                    postgis_cfg = geography["postgis"]
                    est_pop, affected, infra_impacted = self._postgis_assess(ev, postgis_cfg, buffer_meters)
                    rationale.append("assessed_with_postgis")
                except Exception as e:
                    LOG.warning("[ImpactAssessmentTool] PostGIS assess failed: %s", e)
                    rationale.append("postgis_failed")
            elif HAVE_GEOPANDAS and lat is not None and lon is not None:
                # local shapefile approach (expects 'geography' to point to local shapefiles if given)
                try:
                    affected_geom_wkt, est_pop, infra_impacted = self._geopandas_assess(ev, geography, lat, lon, buffer_meters, pop_grid)
                    affected = {"wkt": affected_geom_wkt}
                    rationale.append("assessed_with_geopandas")
                except Exception as e:
                    LOG.warning("[ImpactAssessmentTool] GeoPandas assess failed: %s", e)
                    rationale.append("geopandas_failed")
            else:
                # simple fallback: bounding box + population grid
                if lat is not None and lon is not None:
                    north, west, south, east = None, None, None, None
                    try:
                        south, west, north, east = bbox_from_point(lat, lon, buffer_meters)
                        affected = {"bbox": {"south": south, "west": west, "north": north, "east": east}}
                        est_pop = estimate_population_simple(lat, lon, buffer_meters, pop_grid)
                        rationale.append("assessed_with_fallback")
                    except Exception as e:
                        LOG.warning("[ImpactAssessmentTool] fallback assess failed: %s", e)
                        rationale.append("fallback_failed")
                else:
                    rationale.append("no_location")

            # infrastructure heuristics (simple rules)
            infra_impacted = infra_impacted or self._infer_infrastructure_impact(ev, severity_score)

            result = {
                "event_id": ev.get("event_id") or ev.get("source_record_id") or f"ev-{uuid_gen()}",
                "detected_type": ev.get("detected_type") or ev.get("type"),
                "severity": round(float(severity_score), 3),
                "affected": affected,
                "estimated_population": int(est_pop),
                "infrastructure_impacted": infra_impacted,
                "rationale": rationale,
                "score_breakdown": self._score_breakdown(ev, severity_score),
                "assessed_at": datetime.now(timezone.utc).isoformat()
            }
            results.append(result)

        return {"assessments": results, "meta": {"method": "ImpactAssessmentTool", "count": len(results)}}

    # ----------------- helpers -----------------
    def _derive_severity(self, ev: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> float:
        # base heuristics per event type
        etype = (ev.get("detected_type") or ev.get("type") or "").lower()
        raw = ev.get("raw_record") or ev.get("raw") or {}
        score = 0.0
        # map some known fields to 0-1 partial scores
        if etype in ("flood", "flooding", "flood_risk"):
            val = self._get_nested(raw, ["environment", "flood_risk"]) or self._get_nested(raw, ["flood_risk"])
            if val is not None:
                score = min(1.0, float(val) / 100.0)
            else:
                score = 0.6
        elif etype in ("wildfire", "fire", "wildfire_risk"):
            val = self._get_nested(raw, ["environment", "wildfire_risk"]) or raw.get("wildfire_risk")
            if val is not None:
                score = min(1.0, float(val) / 100.0)
            else:
                score = 0.7
        elif etype in ("air_quality", "aqi", "pollution"):
            val = self._get_nested(raw, ["air_quality", "aqi"]) or raw.get("aqi")
            if val is not None:
                score = min(1.0, float(val) / 500.0)  # 500 -> severe
            else:
                score = 0.5
        else:
            # fallback: use provided confidence if any
            score = float(ev.get("confidence") or ev.get("score") or 0.4)
        # allow severity_config override/scale
        if cfg and etype in cfg:
            try:
                scale = float(cfg[etype].get("scale", 1.0))
                score = max(0.0, min(1.0, score * scale))
            except Exception:
                pass
        return score

    def _postgis_assess(self, ev: Dict[str, Any], cfg: Dict[str, Any], buffer_meters: float) -> Tuple[int, Any, List[str]]:
        # expects cfg with keys: dsn / table_names: geometries_table, population_table, infra_table
        dsn = cfg.get("dsn")
        geom_table = cfg.get("geometries_table")
        pop_table = cfg.get("population_table")
        infra_table = cfg.get("infrastructure_table")
        lat, lon = None, None
        loc = ev.get("location") or {}
        try:
            lat = float(loc.get("latitude"))
            lon = float(loc.get("longitude"))
        except Exception:
            raise RuntimeError("Invalid location for PostGIS assessment")

        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        # buffer point and intersect
        sql = f"""
            WITH pt AS (
                SELECT ST_Transform(ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326), 3857) AS geom3857
            ), buf AS (
                SELECT ST_Transform(ST_Buffer(pt.geom3857, {buffer_meters}), 4326) AS bufgeom
                FROM pt
            )
            SELECT COALESCE(SUM(p.population),0) as pop_sum
            FROM {pop_table} p, buf b
            WHERE ST_Intersects(p.geom, b.bufgeom);
        """
        cur.execute(sql)
        pop_sum = cur.fetchone()[0] or 0
        # infra simple query (names)
        infra_hits = []
        if infra_table:
            sql2 = f"""
                SELECT i.name, i.type FROM {infra_table} i, buf b
                WHERE ST_Intersects(i.geom, b.bufgeom) LIMIT 20;
            """
            cur.execute(sql2)
            for row in cur.fetchall():
                infra_hits.append({"name": row[0], "type": row[1]})
        cur.close()
        conn.close()
        return int(pop_sum), {"method": "postgis"}, infra_hits

    def _geopandas_assess(self, ev: Dict[str, Any], geography: Optional[Dict[str, Any]], lat: float, lon: float, buffer_meters: float, pop_grid: List[Tuple[float, float, int]]):
        # expects geography maybe contains 'shapefile_path' to city polygons
        shp = None
        if geography and geography.get("shapefile_path") and HAVE_GEOPANDAS:
            shp = geography["shapefile_path"]
            gdf = gpd.read_file(shp)
        else:
            # attempt to find ./data/city_polygons.shp
            if os.path.exists("data/city_polygons.shp"):
                gdf = gpd.read_file("data/city_polygons.shp")
            else:
                gdf = None

        pt = Point(lon, lat)
        buf_m = pt.buffer(buffer_meters / 111320.0)  # rough deg buffer; optional more accurate transform
        affected_polys = []
        infra_hits = []
        est_pop = 0
        if gdf is not None:
            hits = gdf[gdf.geometry.intersects(buf_m)]
            for _, row in hits.iterrows():
                affected_polys.append(row.get("name") or row.get("id") or row.geometry.wkt[:200])
        # estimate population from grid
        est_pop = estimate_population_simple(lat, lon, buffer_meters, pop_grid)
        return (", ".join(affected_polys) if affected_polys else None), int(est_pop), infra_hits

    def _infer_infrastructure_impact(self, ev: Dict[str, Any], severity: float) -> List[str]:
        # lightweight heuristic mapping
        etype = (ev.get("detected_type") or ev.get("type") or "").lower()
        infra = []
        if "flood" in etype:
            infra += ["roads", "drainage", "low-lying homes"]
            if severity > 0.6:
                infra += ["power_substations", "critical_access_routes"]
        if "wildfire" in etype or "fire" in etype:
            infra += ["power_lines", "vegetation", "nearby_buildings"]
            if severity > 0.7:
                infra += ["evac_routes"]
        if "air_quality" in etype:
            infra += ["schools", "hospitals"]
        return infra

    def _score_breakdown(self, ev: Dict[str, Any], severity: float) -> Dict[str, Any]:
        # small explainable breakdown for the judge
        return {
            "base_confidence": float(ev.get("confidence") or 0.0),
            "severity_computed": round(float(severity), 3),
            "rules_used": ev.get("rationale", []) or [],
        }

    @staticmethod
    def _get_nested(d: Dict[str, Any], path: List[str]) -> Optional[Any]:
        cur = d
        for p in path:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(p)
            if cur is None:
                return None
        return cur


# small uuid helper
def uuid_gen():
    return uuid.uuid4().hex[:10]


# ----------------- Test harness -----------------
if __name__ == "__main__":
    # simple synthetic test
    sample_detected = [
        {
            "event_id": "det-1",
            "detected_type": "flood",
            "confidence": 0.88,
            "timestamp": "2025-10-05T12:00:00Z",
            "location": {"latitude": 24.8607, "longitude": 67.0011},
            "raw_record": {"environment": {"flood_risk": 82}},
        },
        {
            "event_id": "det-2",
            "detected_type": "wildfire",
            "confidence": 0.75,
            "timestamp": "2025-10-05T12:05:00Z",
            "location": {"latitude": 24.95, "longitude": 67.10},
            "raw_record": {"environment": {"wildfire_risk": 55}},
        },
        {
            "event_id": "det-3",
            "detected_type": "air_quality",
            "confidence": 0.65,
            "timestamp": "2025-10-05T12:10:00Z",
            "location": {"latitude": 24.86, "longitude": 67.01},
            "raw_record": {"air_quality": {"aqi": 220}},
        },
    ]

    tool = ImpactAssessmentTool()
    out = tool._run(detected_events=sample_detected, population_layer_csv=None, buffer_meters=1000)
    print(json.dumps(out, indent=2, ensure_ascii=False))
