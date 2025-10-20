# # src/smart_urban_resilience/tools/ResourcePlannerTool.py
# """
# ResourcePlannerTool — CrewAI BaseTool

# One-file, production-ready resource planner for the Resource Recommender & Logistics agents.
# Features:
# - CrewAI-compatible BaseTool subclass (crewai.tools.BaseTool)
# - Greedy solver (fast, explainable)
# - Optional LP solver using pulp (guarded import, time-limited)
# - Optional OSRM routing for realistic ETAs (guarded requests)
# - Configurable constraints: resource_type_map, max_travel_minutes, capacity handling, multi-resource requirements
# - Returns JSON-serializable plan, metadata, and diagnostics for observability / judge scoring.
# """

# from __future__ import annotations
# import math
# import time
# import logging
# import json
# from typing import Any, Dict, List, Optional, Tuple, Type, Union
# from datetime import datetime, timezone
# from pydantic import BaseModel, Field
# from crewai.tools import BaseTool

# # Optional libs (guarded)
# try:
#     import requests
# except Exception:
#     requests = None

# try:
#     import pulp
#     HAVE_PULP = True
# except Exception:
#     pulp = None
#     HAVE_PULP = False

# # logging
# logging.basicConfig(level=logging.INFO)
# LOG = logging.getLogger("ResourcePlannerTool")


# # ----------------------------
# # Pydantic input schema
# # ----------------------------
# # class ResourcePlannerInput(BaseModel):
# #     assessed_events: List[Dict[str, Any]] = Field(..., description="Event assessments from ImpactAssessorTool.")
# #     resources: List[Dict[str, Any]] = Field(..., description="Available resources (id,type,location,status,capacity).")
# #     osrm_url: Optional[str] = Field(None, description="Optional OSRM server base URL for routing.")
# #     avg_speed_kmph: Optional[float] = Field(40.0, description="Fallback travel speed when OSRM not available.")
# #     solver: Optional[str] = Field("greedy", description="Solver: 'greedy' | 'lp' (requires pulp).")
# #     constraints: Optional[Dict[str, Any]] = Field(None, description="Optional constraints like max_travel_minutes, resource_type_map.")
# #     max_assignments_per_resource: Optional[int] = Field(1, description="Max simultaneous assignments per resource.")
# #     consider_capacity: Optional[bool] = Field(True, description="Respect resource.capacity fields if present.")
# #     multi_resource_requirements: Optional[Dict[str, int]] = Field(None, description="Event-level required resource counts by type, e.g. {'flood':['pump',2]}")
# #     time_limit_s: Optional[int] = Field(8, description="LP solver time limit in seconds (if using pulp).")
# class ResourcePlannerInput(BaseModel):
#     assessed_events: List[Dict[str, Any]] = Field(..., description="List of event assessments (from ImpactAssessmentTool).")
#     resources: List[Dict[str, Any]] = Field(..., description="List of available resources with location, type, status.")
#     osrm_url: Optional[str] = Field(None)
#     avg_speed_kmph: Optional[float] = Field(40.0)
#     solver: Optional[str] = Field("greedy")
#     constraints: Optional[Dict[str, Any]] = Field(None)
#     max_assignments_per_resource: Optional[int] = Field(1)
#     consider_capacity: Optional[bool] = Field(True)
#     # NEW: accept multi_resource_requirements as dict[str, Union[int, List[Union[str,int]]]]
#     multi_resource_requirements: Optional[Dict[str, Union[int, List[Union[str, int]]]]] = Field(
#         None,
#         description=(
#             "Event-level required resource counts by type; flexible forms allowed:\n"
#             " {'flood': 2}  OR  {'flood': ['pump', 2]} (typeName, count)"
#         )
#     )
#     time_limit_s: Optional[int] = Field(None)


# # ----------------------------
# # Utility functions
# # ----------------------------
# def safe_float(x: Any, default: float = 0.0) -> float:
#     try:
#         return float(x)
#     except Exception:
#         return default


# def haversine_minutes(lat1: float, lon1: float, lat2: float, lon2: float, speed_kmph: float = 40.0) -> float:
#     # great-circle distance -> time in minutes using speed_kmph
#     R = 6371.0  # km
#     dlat = math.radians(lat2 - lat1)
#     dlon = math.radians(lon2 - lon1)
#     a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
#     c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
#     km = R * c
#     hours = km / max(0.1, speed_kmph)
#     return hours * 60.0


# def extract_latlon(obj: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
#     if not obj:
#         return None, None
#     if "location" in obj and isinstance(obj["location"], dict):
#         lat = obj["location"].get("latitude") or obj["location"].get("lat")
#         lon = obj["location"].get("longitude") or obj["location"].get("lon")
#     else:
#         lat = obj.get("latitude") or obj.get("lat")
#         lon = obj.get("longitude") or obj.get("lon")
#     try:
#         return (float(lat), float(lon)) if lat is not None and lon is not None else (None, None)
#     except Exception:
#         return None, None


# # ----------------------------
# # Tool implementation
# # ----------------------------
# class ResourcePlannerTool(BaseTool):
#     name: str = "Resource Planner Tool"
#     description: str = (
#         "Matches resources to assessed events. Uses OSRM if available, otherwise haversine-based ETA. "
#         "Supports greedy and pulp LP solvers (LP guarded). Returns recommended plans and diagnostics."
#     )
#     args_schema: Type[BaseModel] = ResourcePlannerInput

#     def _run(
#         self,
#         assessed_events: List[Dict[str, Any]],
#         resources: List[Dict[str, Any]],
#         osrm_url: Optional[str] = None,
#         avg_speed_kmph: float = 40.0,
#         solver: Optional[str] = "greedy",
#         constraints: Optional[Dict[str, Any]] = None,
#         max_assignments_per_resource: int = 1,
#         consider_capacity: bool = True,
#         multi_resource_requirements: Optional[Dict[str, int]] = None,
#         time_limit_s: int = 8,
#     ) -> Dict[str, Any]:
#         """Main entry point used by CrewAI agents."""
#         t0 = time.time()
#         solver = (solver or "greedy").lower()
#         constraints = constraints or {}
#         max_travel = float(constraints.get("max_travel_minutes", 99999))
#         resource_type_map = constraints.get("resource_type_map", {})  # e.g., {"flood": ["pump","engine"]}

#         # Defensive copies
#         events = [dict(e) for e in assessed_events]
#         res = [dict(r) for r in resources]

#         # Basic normalization
#         for e in events:
#             e.setdefault("priority", safe_float(e.get("severity", 0.0)) * (1.0 + math.log1p(max(0, int(e.get("estimated_population") or 0)))))

#         # Locations
#         event_locs = [extract_latlon(e.get("affected") or e.get("location") or {}) for e in events]
#         resource_locs = [extract_latlon(r.get("location") or {}) for r in res]

#         # Build ETA matrix (minutes)
#         n_res = len(res)
#         n_ev = len(events)
#         etas: List[List[float]] = [[float("inf")] * n_ev for _ in range(n_res)]

#         for i in range(n_res):
#             rlat, rlon = resource_locs[i]
#             for j in range(n_ev):
#                 elat, elon = event_locs[j]
#                 if rlat is None or elat is None:
#                     continue
#                 # try OSRM
#                 eta_min = None
#                 if osrm_url and requests:
#                     try:
#                         url = f"{osrm_url.rstrip('/')}/route/v1/driving/{rlon},{rlat};{elon},{elat}?overview=false"
#                         resp = requests.get(url, timeout=4)
#                         if resp.status_code == 200:
#                             routes = resp.json().get("routes")
#                             if routes:
#                                 duration_s = safe_float(routes[0].get("duration", 0.0), 0.0)
#                                 eta_min = duration_s / 60.0
#                     except Exception as e:
#                         LOG.debug("OSRM call failed: %s", e)
#                 if eta_min is None:
#                     eta_min = haversine_minutes(rlat, rlon, elat, elon, speed_kmph=avg_speed_kmph)
#                 etas[i][j] = max(0.0, float(eta_min))

#         # Resource availability & capacity
#         available_idx = []
#         capacity = {}
#         for i, r in enumerate(res):
#             status = (r.get("status") or "").lower()
#             cap = int(r.get("capacity") or max_assignments_per_resource)
#             capacity[i] = cap
#             if status in ("available", "idle", "ready", "") or cap > 0:
#                 available_idx.append(i)

#         # Helper scoring (higher is better)
#         def score_pair(i: int, j: int) -> float:
#             sev = safe_float(events[j].get("severity", 0.0))
#             pop = int(events[j].get("estimated_population") or 0)
#             base = sev * (1.0 + math.log1p(pop))
#             eta = etas[i][j] if (etas[i][j] is not None) else 99999.0
#             eta_factor = 1.0 / (1.0 + eta / 30.0)  # 30-min scale
#             return base * eta_factor

#         assignments: List[Dict[str, Any]] = []
#         diagnostic = {"raw_etas": etas, "available_resources": len(available_idx)}

#         # ---------------------------
#         # LP solver (pulp) - optional
#         # ---------------------------
#         if solver == "lp" and HAVE_PULP:
#             LOG.info("Running pulp LP solver")
#             try:
#                 prob = pulp.LpProblem("resource_assignment", pulp.LpMinimize)
#                 # binary vars x_i_j
#                 x = {}
#                 for i in range(n_res):
#                     for j in range(n_ev):
#                         x[(i, j)] = pulp.LpVariable(f"x_{i}_{j}", cat="Binary")
#                 # objective: minimize weighted ETA (weight = severity * (1+log(pop)))
#                 prob += pulp.lpSum([safe_float(events[j].get("severity", 0.0)) * (etas[i][j] or 99999.0) * x[(i, j)]
#                                      for i in range(n_res) for j in range(n_ev)])
#                 # each event assigned at most required count (default 1)
#                 for j in range(n_ev):
#                     required = int(events[j].get("required_resources") or 1)
#                     prob += pulp.lpSum([x[(i, j)] for i in range(n_res)]) >= min(required, n_res)  # allow >= required (or change to == if strict)
#                 # resource capacity
#                 for i in range(n_res):
#                     cap = int(res[i].get("capacity") or max_assignments_per_resource)
#                     prob += pulp.lpSum([x[(i, j)] for j in range(n_ev)]) <= cap
#                 # travel limit constraints
#                 for i in range(n_res):
#                     for j in range(n_ev):
#                         if etas[i][j] is None or etas[i][j] > max_travel:
#                             prob += x[(i, j)] == 0
#                 # Solve with time limit
#                 solver_cmd = pulp.PULP_CBC_CMD(msg=False, timeLimit=int(time_limit_s))
#                 prob.solve(solver_cmd)
#                 status = pulp.LpStatus.get(prob.status, str(prob.status))
#                 diagnostic["lp_status"] = status
#                 # parse assignments
#                 for i in range(n_res):
#                     for j in range(n_ev):
#                         val = pulp.value(x[(i, j)])
#                         if val is not None and val > 0.5:
#                             assignments.append({
#                                 "resource_index": i,
#                                 "event_index": j,
#                                 "resource_id": res[i].get("id") or f"res-{i}",
#                                 "event_id": events[j].get("event_id") or f"ev-{j}",
#                                 "eta_min": round(float(etas[i][j]), 2),
#                                 "score": round(score_pair(i, j), 3),
#                             })
#                 meta = {"algorithm": "lp", "status": diagnostic.get("lp_status"), "pulp_available": True}
#                 elapsed = time.time() - t0
#                 return {"plans_recommended": assignments, "meta": meta, "diagnostic": diagnostic, "elapsed_s": round(elapsed, 3)}
#             except Exception as e:
#                 LOG.warning("LP solver failed, falling back to greedy: %s", e)
#                 diagnostic["lp_error"] = str(e)

#         # ---------------------------
#         # Greedy solver (default)
#         # ---------------------------
#         LOG.info("Running greedy solver")
#         used = {i: 0 for i in range(n_res)}
#         event_assigned = {j: [] for j in range(n_ev)}

#         # event priority order (high first)
#         priorities = sorted([(events[j].get("priority", 0.0), j) for j in range(n_ev)], reverse=True)
#         for _, j in priorities:
#             required = int(events[j].get("required_resources") or 1)
#             assigned_count = 0
#             # find best candidates
#             candidates = []
#             for i in available_idx:
#                 if used[i] >= capacity.get(i, max_assignments_per_resource):
#                     continue
#                 # type matching (if resource_type_map provided)
#                 etype = (events[j].get("detected_type") or events[j].get("type") or "").lower()
#                 allowed = resource_type_map.get(etype)
#                 if allowed:
#                     rtype = (res[i].get("type") or "").lower()
#                     if rtype not in [a.lower() for a in allowed]:
#                         continue
#                 eta = etas[i][j]
#                 if eta is None or eta > max_travel:
#                     continue
#                 candidates.append((score_pair(i, j), i, eta))
#             # pick top required
#             candidates.sort(reverse=True, key=lambda x: x[0])
#             for score_val, i, eta in candidates[:required]:
#                 assigned_count += 1
#                 used[i] += 1
#                 event_assigned[j].append(i)
#                 assignments.append({
#                     "resource_index": i,
#                     "event_index": j,
#                     "resource_id": res[i].get("id") or f"res-{i}",
#                     "event_id": events[j].get("event_id") or f"ev-{j}",
#                     "eta_min": round(float(eta), 2),
#                     "score": round(float(score_val), 3),
#                 })
#                 # respect capacity: if used up, remove from available
#                 if used[i] >= capacity.get(i, max_assignments_per_resource) and i in available_idx:
#                     available_idx.remove(i)
#                 if assigned_count >= required:
#                     break

#         elapsed = time.time() - t0
#         meta = {"algorithm": "greedy", "pulp_available": HAVE_PULP, "assignments": len(assignments)}
#         return {"plans_recommended": assignments, "meta": meta, "diagnostic": diagnostic, "elapsed_s": round(elapsed, 3)}


# # ----------------------------
# # Test harness
# # ----------------------------
# if __name__ == "__main__":
#     # Synthetic events and resources for quick local testing
#     sample_events = [
#         {"event_id": "ev1", "detected_type": "flood", "severity": 0.92, "estimated_population": 1200,
#          "location": {"latitude": 24.8607, "longitude": 67.0011}, "required_resources": 1},
#         {"event_id": "ev2", "detected_type": "wildfire", "severity": 0.8, "estimated_population": 300,
#          "location": {"latitude": 24.95, "longitude": 67.10}, "required_resources": 1},
#         {"event_id": "ev3", "detected_type": "air_quality", "severity": 0.6, "estimated_population": 500,
#          "location": {"latitude": 24.87, "longitude": 67.02}, "required_resources": 1},
#     ]
#     sample_resources = [
#         {"id": "res1", "type": "pump", "status": "available", "capacity": 1, "location": {"latitude": 24.86, "longitude": 67.00}},
#         {"id": "res2", "type": "fire_truck", "status": "available", "capacity": 1, "location": {"latitude": 24.96, "longitude": 67.11}},
#         {"id": "res3", "type": "ambulance", "status": "available", "capacity": 1, "location": {"latitude": 24.865, "longitude": 67.02}},
#     ]

#     tool = ResourcePlannerTool()
#     out = tool._run(assessed_events=sample_events, resources=sample_resources, osrm_url=None, solver="greedy", constraints={"max_travel_minutes": 120})
#     print(json.dumps(out, indent=2, ensure_ascii=False))

# src/smart_urban_resilience/tools/ResourcePlannerTool.py
"""
ResourcePlannerTool — CrewAI BaseTool

One-file, production-ready resource planner for the Resource Recommender & Logistics agents.
Features:
- CrewAI-compatible BaseTool subclass (crewai.tools.BaseTool)
- Greedy solver (fast, explainable)
- Optional LP solver using pulp (guarded import, time-limited)
- Optional OSRM routing for realistic ETAs (guarded requests)
- Configurable constraints: resource_type_map, max_travel_minutes, capacity handling, multi-resource requirements
- Returns JSON-serializable plan, metadata, and diagnostics for observability / judge scoring.
"""

from __future__ import annotations
import math
import time
import logging
import json
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Optional libs (guarded)
try:
    import requests
except Exception:
    requests = None

try:
    import pulp
    HAVE_PULP = True
except Exception:
    pulp = None
    HAVE_PULP = False

# logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("ResourcePlannerTool")


# ----------------------------
# Pydantic input schema
# ----------------------------
class ResourcePlannerInput(BaseModel):
    assessed_events: List[Dict[str, Any]] = Field(..., description="List of event assessments (from ImpactAssessmentTool).")
    resources: List[Dict[str, Any]] = Field(..., description="List of available resources with location, type, status.")
    osrm_url: Optional[str] = Field(None)
    avg_speed_kmph: Optional[float] = Field(40.0)
    solver: Optional[str] = Field("greedy")
    constraints: Optional[Dict[str, Any]] = Field(None)
    max_assignments_per_resource: Optional[int] = Field(1)
    consider_capacity: Optional[bool] = Field(True)
    # NEW: accept multi_resource_requirements as dict[str, Union[int, List[Union[str,int]], dict[str,int]]]
    multi_resource_requirements: Optional[Dict[str, Union[int, List[Union[str, int]], Dict[str, int]]]] = Field(
        None,
        description=(
            "Event-level required resource counts by type; flexible forms allowed:\n"
            " {'flood': 2}  OR  {'flood': ['pump', 2]}  OR {'flood': {'pump':2, 'boat':1}}"
        )
    )
    time_limit_s: Optional[int] = Field(None)


# ----------------------------
# Utility functions
# ----------------------------
def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def haversine_minutes(lat1: float, lon1: float, lat2: float, lon2: float, speed_kmph: float = 40.0) -> float:
    # great-circle distance -> time in minutes using speed_kmph
    R = 6371.0  # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    km = R * c
    hours = km / max(0.1, speed_kmph)
    return hours * 60.0


def extract_latlon(obj: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    if not obj:
        return None, None
    if "location" in obj and isinstance(obj["location"], dict):
        lat = obj["location"].get("latitude") or obj["location"].get("lat")
        lon = obj["location"].get("longitude") or obj["location"].get("lon")
    else:
        lat = obj.get("latitude") or obj.get("lat")
        lon = obj.get("longitude") or obj.get("lon")
    try:
        return (float(lat), float(lon)) if lat is not None and lon is not None else (None, None)
    except Exception:
        return None, None


def _canonicalize_multi_req(mr_raw: Any) -> Dict[str, Dict[str, int]]:
    """
    Convert many possible input forms into canonical:
      { event_type_lower: {resource_type_or_'any': count, ... }, ... }
    Accepts:
      - {"flood": 2}
      - {"flood": ["pump", 2]}
      - {"flood": {"pump":2, "boat":1}}
    """
    canonical: Dict[str, Dict[str, int]] = {}
    if not mr_raw or not isinstance(mr_raw, dict):
        return canonical
    for etype, val in mr_raw.items():
        key = str(etype).lower()
        if isinstance(val, int):
            canonical[key] = {"any": int(val)}
        elif isinstance(val, (list, tuple)) and len(val) == 2:
            rtype = str(val[0])
            try:
                cnt = int(val[1])
            except Exception:
                cnt = 1
            canonical.setdefault(key, {})[rtype.lower()] = cnt
        elif isinstance(val, dict):
            canonical.setdefault(key, {})
            for rt, cnt in val.items():
                try:
                    canonical[key][str(rt).lower()] = int(cnt)
                except Exception:
                    canonical[key][str(rt).lower()] = 1
        else:
            # try numeric conversion
            try:
                canonical[key] = {"any": int(val)}
            except Exception:
                canonical[key] = {"any": 1}
    return canonical


# ----------------------------
# Tool implementation
# ----------------------------
class ResourcePlannerTool(BaseTool):
    name: str = "Resource Planner Tool"
    description: str = (
        "Matches resources to assessed events. Uses OSRM if available, otherwise haversine-based ETA. "
        "Supports greedy and pulp LP solvers (LP guarded). Returns recommended plans and diagnostics."
    )
    args_schema: Type[BaseModel] = ResourcePlannerInput

    def _run(
        self,
        assessed_events: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        osrm_url: Optional[str] = None,
        avg_speed_kmph: float = 40.0,
        solver: Optional[str] = "greedy",
        constraints: Optional[Dict[str, Any]] = None,
        max_assignments_per_resource: int = 1,
        consider_capacity: bool = True,
        multi_resource_requirements: Optional[Dict[str, Union[int, List[Union[str, int]], Dict[str, int]]]] = None,
        time_limit_s: int = 8,
    ) -> Dict[str, Any]:
        """Main entry point used by CrewAI agents."""
        t0 = time.time()
        solver = (solver or "greedy").lower()
        constraints = constraints or {}
        max_travel = float(constraints.get("max_travel_minutes", 99999))
        resource_type_map = constraints.get("resource_type_map", {})  # e.g., {"flood": ["pump","engine"]}

        # merge multi_resource_requirements from direct param and constraints (param overrides)
        mr_raw = {}
        if isinstance(constraints.get("multi_resource_requirements"), dict):
            mr_raw.update(constraints.get("multi_resource_requirements"))
        if isinstance(multi_resource_requirements, dict):
            mr_raw.update(multi_resource_requirements)
        canonical_mr = _canonicalize_multi_req(mr_raw)

        # Defensive copies
        events = [dict(e) for e in assessed_events]
        res = [dict(r) for r in resources]

        # Basic normalization
        for e in events:
            e.setdefault("priority", safe_float(e.get("severity", 0.0)) * (1.0 + math.log1p(max(0, int(e.get("estimated_population") or 0)))))
            # If event had required_resources (legacy), keep it but canonical_mr takes precedence
            if "required_resources" not in e:
                e["required_resources"] = 1

        # Locations
        event_locs = [extract_latlon(e.get("affected") or e.get("location") or {}) for e in events]
        resource_locs = [extract_latlon(r.get("location") or {}) for r in res]

        # Build ETA matrix (minutes)
        n_res = len(res)
        n_ev = len(events)
        etas: List[List[float]] = [[float("inf")] * n_ev for _ in range(n_res)]

        for i in range(n_res):
            rlat, rlon = resource_locs[i]
            for j in range(n_ev):
                elat, elon = event_locs[j]
                if rlat is None or elat is None:
                    continue
                # try OSRM
                eta_min = None
                if osrm_url and requests:
                    try:
                        url = f"{osrm_url.rstrip('/')}/route/v1/driving/{rlon},{rlat};{elon},{elat}?overview=false"
                        resp = requests.get(url, timeout=4)
                        if resp.status_code == 200:
                            routes = resp.json().get("routes")
                            if routes:
                                duration_s = safe_float(routes[0].get("duration", 0.0), 0.0)
                                eta_min = duration_s / 60.0
                    except Exception as e:
                        LOG.debug("OSRM call failed: %s", e)
                if eta_min is None:
                    eta_min = haversine_minutes(rlat, rlon, elat, elon, speed_kmph=avg_speed_kmph)
                etas[i][j] = max(0.0, float(eta_min))

        # Resource availability & capacity
        available_idx = []
        capacity = {}
        for i, r in enumerate(res):
            status = (r.get("status") or "").lower()
            cap = int(r.get("capacity") or max_assignments_per_resource)
            capacity[i] = cap
            if status in ("available", "idle", "ready", "") or cap > 0:
                available_idx.append(i)

        # Helper scoring (higher is better)
        def score_pair(i: int, j: int) -> float:
            sev = safe_float(events[j].get("severity", 0.0))
            pop = int(events[j].get("estimated_population") or 0)
            base = sev * (1.0 + math.log1p(pop))
            eta = etas[i][j] if (etas[i][j] is not None) else 99999.0
            eta_factor = 1.0 / (1.0 + eta / 30.0)  # 30-min scale
            return base * eta_factor

        assignments: List[Dict[str, Any]] = []
        diagnostic = {"raw_etas": etas, "available_resources": len(available_idx)}

        # ---------------------------
        # LP solver (pulp) - optional
        # ---------------------------
        if solver == "lp" and HAVE_PULP:
            LOG.info("Running pulp LP solver")
            try:
                prob = pulp.LpProblem("resource_assignment", pulp.LpMinimize)
                # binary vars x_i_j
                x = {}
                for i in range(n_res):
                    for j in range(n_ev):
                        x[(i, j)] = pulp.LpVariable(f"x_{i}_{j}", cat="Binary")
                # objective: minimize weighted ETA (weight = severity * (1+log(pop)))
                prob += pulp.lpSum([safe_float(events[j].get("severity", 0.0)) * (etas[i][j] or 99999.0) * x[(i, j)]
                                     for i in range(n_res) for j in range(n_ev)])
                # each event assigned at least required count (legacy uses required_resources)
                for j in range(n_ev):
                    required = int(events[j].get("required_resources") or 1)
                    prob += pulp.lpSum([x[(i, j)] for i in range(n_res)]) >= min(required, n_res)
                # resource capacity
                for i in range(n_res):
                    cap = int(res[i].get("capacity") or max_assignments_per_resource)
                    prob += pulp.lpSum([x[(i, j)] for j in range(n_ev)]) <= cap
                # travel limit constraints
                for i in range(n_res):
                    for j in range(n_ev):
                        if etas[i][j] is None or etas[i][j] > max_travel:
                            prob += x[(i, j)] == 0
                # Solve with time limit
                solver_cmd = pulp.PULP_CBC_CMD(msg=False, timeLimit=int(time_limit_s))
                prob.solve(solver_cmd)
                status = pulp.LpStatus.get(prob.status, str(prob.status))
                diagnostic["lp_status"] = status
                # parse assignments
                for i in range(n_res):
                    for j in range(n_ev):
                        val = pulp.value(x[(i, j)])
                        if val is not None and val > 0.5:
                            assignments.append({
                                "resource_index": i,
                                "event_index": j,
                                "resource_id": res[i].get("id") or f"res-{i}",
                                "event_id": events[j].get("event_id") or f"ev-{j}",
                                "eta_min": round(float(etas[i][j]), 2),
                                "score": round(score_pair(i, j), 3),
                            })
                meta = {"algorithm": "lp", "status": diagnostic.get("lp_status"), "pulp_available": True}
                elapsed = time.time() - t0
                return {"plans_recommended": assignments, "meta": meta, "diagnostic": diagnostic, "elapsed_s": round(elapsed, 3)}
            except Exception as e:
                LOG.warning("LP solver failed, falling back to greedy: %s", e)
                diagnostic["lp_error"] = str(e)

        # ---------------------------
        # Greedy solver (default)
        # ---------------------------
        LOG.info("Running greedy solver")
        used = {i: 0 for i in range(n_res)}
        event_assigned = {j: [] for j in range(n_ev)}

        # event priority order (high first)
        priorities = sorted([(events[j].get("priority", 0.0), j) for j in range(n_ev)], reverse=True)
        for _, j in priorities:
            # Determine required mapping for this event: type -> count
            etype = (events[j].get("detected_type") or events[j].get("type") or "").lower()
            if etype in canonical_mr:
                required_map = canonical_mr[etype]  # e.g., {"pump":2} or {"any":2}
            else:
                # fallback to per-event required_resources (generic)
                required_map = {"any": int(events[j].get("required_resources") or 1)}

            # For each required resource type, pick up to count best candidates
            for req_rtype, req_count in required_map.items():
                req_count = int(req_count or 1)
                assigned_for_this_type = 0
                # build candidates list for this requirement
                candidates = []
                for i in list(available_idx):
                    if used[i] >= capacity.get(i, max_assignments_per_resource):
                        continue
                    eta = etas[i][j]
                    if eta is None or eta > max_travel:
                        continue
                    # if req_rtype == 'any', allow any resource; else match resource.type
                    if req_rtype != "any":
                        rtype = (res[i].get("type") or "").lower()
                        if rtype != req_rtype and req_rtype not in [a.lower() for a in resource_type_map.get(etype, [])]:
                            continue
                    candidates.append((score_pair(i, j), i, eta))
                # sort and pick top req_count, but skip already assigned resources for this event
                candidates.sort(reverse=True, key=lambda x: x[0])
                for score_val, i, eta in candidates:
                    if assigned_for_this_type >= req_count:
                        break
                    # double check resource not already used up
                    if used[i] >= capacity.get(i, max_assignments_per_resource):
                        continue
                    # assign
                    used[i] += 1
                    event_assigned[j].append(i)
                    assigned_for_this_type += 1
                    assignments.append({
                        "resource_index": i,
                        "event_index": j,
                        "resource_id": res[i].get("id") or f"res-{i}",
                        "event_id": events[j].get("event_id") or f"ev-{j}",
                        "eta_min": round(float(eta), 2),
                        "score": round(float(score_val), 3),
                    })
                    # respect capacity: if used up, remove from available
                    if used[i] >= capacity.get(i, max_assignments_per_resource) and i in available_idx:
                        available_idx.remove(i)

        elapsed = time.time() - t0
        meta = {"algorithm": "greedy", "pulp_available": HAVE_PULP, "assignments": len(assignments)}
        print(f"Resource assignments completed. Results: \n1-plans_recommended: {assignments}\n2-meta: {meta}\ndiagnostic: {diagnostic}", )
        return {"plans_recommended": assignments, "meta": meta, "diagnostic": diagnostic, "elapsed_s": round(elapsed, 3)}


# ----------------------------
# Test harness
# ----------------------------
if __name__ == "__main__":
    # Synthetic events and resources for quick local testing
    sample_events = [
        {"event_id": "ev1", "detected_type": "flood", "severity": 0.92, "estimated_population": 1200,
         "location": {"latitude": 24.8607, "longitude": 67.0011}, "required_resources": 1},
        {"event_id": "ev2", "detected_type": "wildfire", "severity": 0.8, "estimated_population": 300,
         "location": {"latitude": 24.95, "longitude": 67.10}, "required_resources": 1},
        {"event_id": "ev3", "detected_type": "air_quality", "severity": 0.6, "estimated_population": 500,
         "location": {"latitude": 24.87, "longitude": 67.02}, "required_resources": 1},
    ]
    sample_resources = [
        {"id": "res1", "type": "pump", "status": "available", "capacity": 1, "location": {"latitude": 24.86, "longitude": 67.00}},
        {"id": "res2", "type": "fire_truck", "status": "available", "capacity": 1, "location": {"latitude": 24.96, "longitude": 67.11}},
        {"id": "res3", "type": "ambulance", "status": "available", "capacity": 1, "location": {"latitude": 24.865, "longitude": 67.02}},
    ]

    tool = ResourcePlannerTool()
    out = tool._run(
        assessed_events=sample_events,
        resources=sample_resources,
        osrm_url=None,
        solver="greedy",
        constraints={"max_travel_minutes": 120, "multi_resource_requirements": {"flood": ["pump", 1]}}
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
