# src/smart_urban_resilience/tools/LogisticsRoutingTool.py
"""
LogisticsRoutingTool — CrewAI BaseTool

Responsibilities:
- Accept recommended plans (from ResourcePlannerTool) and produce dispatch commands.
- Resolve routing info (OSRM preferred; haversine fallback).
- Enforce idempotency tokens for safe retries.
- Dry-run mode for judge demos and reproducible tests.
- Return per-command status + diagnostics.
"""
from __future__ import annotations
import time
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

try:
    import requests
except Exception:
    requests = None

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("LogisticsRoutingTool")


# ---------- schema
class DispatchCommand(BaseModel):
    resource_id: str
    event_id: str
    eta_min: Optional[float] = None
    route: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    idempotency_token: Optional[str] = None


class LogisticsRoutingInput(BaseModel):
    plans_recommended: List[Dict[str, Any]] = Field(..., description="Assignments from ResourcePlannerTool (list of {resource_id,event_id,eta_min,...}).")
    resources: List[Dict[str, Any]] = Field(..., description="Resource registry entries (id,type,location,contact,capacity).")
    events: Optional[List[Dict[str, Any]]] = Field(None, description="Event details to include in message.")
    osrm_url: Optional[str] = Field(None, description="OSRM base URL (optional).")
    webhook_url: Optional[str] = Field(None, description="Optional dispatch webhook to POST commands to.")
    dry_run: Optional[bool] = Field(True, description="If True, do not POST to external webhooks; return simulated responses.")
    max_retry: Optional[int] = Field(2, description="Retry count for webhook POSTs.")
    retry_backoff_s: Optional[int] = Field(2, description="Base backoff seconds (exponential).")
    idempotency_namespace: Optional[str] = Field("logistics_dispatch", description="Namespace used when creating idempotency tokens.")


# ---------- utilities
def make_idempotency_token(namespace: str, resource_id: str, event_id: str, trace: Optional[str] = None) -> str:
    base = f"{namespace}|{resource_id}|{event_id}|{trace or ''}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def haversine_minutes(lat1: float, lon1: float, lat2: float, lon2: float, speed_kmph: float = 40.0) -> float:
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    km = R * c
    hours = km / max(0.1, speed_kmph)
    return hours * 60.0


def find_resource(res_list: List[Dict[str, Any]], resource_id: str) -> Optional[Dict[str, Any]]:
    for r in res_list:
        if r.get("id") == resource_id or r.get("resource_id") == resource_id:
            return r
    return None


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


# ---------- tool
class LogisticsRoutingTool(BaseTool):
    name: str = "Logistics & Routing Tool"
    description: str = "Turn recommended plans into idempotent dispatch commands with routing & dry-run support."
    args_schema: Type[BaseModel] = LogisticsRoutingInput

    def _run(
        self,
        plans_recommended: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        events: Optional[List[Dict[str, Any]]] = None,
        osrm_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
        dry_run: bool = True,
        max_retry: int = 2,
        retry_backoff_s: int = 2,
        idempotency_namespace: str = "logistics_dispatch",
    ) -> Dict[str, Any]:
        t0 = time.time()
        results: List[Dict[str, Any]] = []
        diag = {"commands": 0, "sent": 0, "failed": 0, "dry_run": bool(dry_run)}

        # simple mapping for quick event lookup
        event_map = {e.get("event_id"): e for e in (events or [])}

        for assignment in plans_recommended:
            res_id = assignment.get("resource_id") or assignment.get("resource_index")
            ev_id = assignment.get("event_id") or assignment.get("event_index")
            # generate idempotency token
            trace = assignment.get("trace_id") or assignment.get("plan_trace") or ""
            token = make_idempotency_token(idempotency_namespace, str(res_id), str(ev_id), trace)
            # locate resource and event
            resource = find_resource(resources, res_id) or {}
            event = event_map.get(ev_id) or {}

            # compute route/eta: use assignment.eta_min if present, else compute from locations
            eta = assignment.get("eta_min")
            route_info: Dict[str, Any] = {}
            rlat, rlon = extract_latlon(resource.get("location") or {})
            elat, elon = extract_latlon(event.get("location") or event.get("affected") or assignment.get("event_location") or {})
            if (eta is None or eta == 0.0) and rlat is not None and elat is not None:
                if osrm_url and requests:
                    try:
                        url = f"{osrm_url.rstrip('/')}/route/v1/driving/{rlon},{rlat};{elon},{elat}?overview=false"
                        resp = requests.get(url, timeout=4)
                        if resp.status_code == 200:
                            routes = resp.json().get("routes")
                            if routes:
                                duration_s = float(routes[0].get("duration", 0.0))
                                eta = duration_s / 60.0
                                route_info["osrm_used"] = True
                                route_info["duration_s"] = duration_s
                    except Exception as e:
                        LOG.debug("OSRM failed: %s", e)
                if eta is None:
                    eta = haversine_minutes(rlat, rlon, elat, elon)

            cmd = DispatchCommand(
                resource_id=str(res_id),
                event_id=str(ev_id),
                eta_min=float(eta) if eta is not None else None,
                route=route_info or None,
                metadata={
                    "resource_type": resource.get("type"),
                    "resource_contact": resource.get("contact"),
                    "event_summary": event.get("summary") or event.get("type"),
                    "raw_assignment": assignment
                },
                idempotency_token=token
            )

            # Build payload for webhook
            payload = {"command": cmd.dict(), "timestamp": time.time()}

            # Dry run handling
            if dry_run or not webhook_url or not requests:
                results.append({"command": cmd.dict(), "status": "dry_run", "response": None})
                diag["commands"] += 1
                diag["sent"] += 0
                continue

            # POST to webhook with retries + exponential backoff + idempotency header
            sent = False
            last_err = None
            for attempt in range(0, max_retry + 1):
                try:
                    headers = {"Idempotency-Token": token, "Content-Type": "application/json"}
                    resp = requests.post(webhook_url, json=payload, headers=headers, timeout=8)
                    if 200 <= resp.status_code < 300:
                        results.append({"command": cmd.dict(), "status": "ok", "response": resp.json() if resp.content else {"status_code": resp.status_code}})
                        diag["commands"] += 1
                        diag["sent"] += 1
                        sent = True
                        break
                    else:
                        last_err = f"bad_status:{resp.status_code}"
                except Exception as e:
                    last_err = str(e)
                time.sleep(retry_backoff_s * (2 ** attempt))
            if not sent:
                results.append({"command": cmd.dict(), "status": "failed", "response": last_err})
                diag["commands"] += 1
                diag["failed"] += 1

        elapsed = time.time() - t0
        return {"dispatch_results": results, "diagnostic": diag, "elapsed_s": round(elapsed, 3)}


# ---------- test harness
if __name__ == "__main__":
    sample_plans = [
        {"resource_id": "res1", "event_id": "ev1", "eta_min": 12.5},
        {"resource_id": "res2", "event_id": "ev2", "eta_min": 25.0},
    ]
    sample_resources = [
        {"id": "res1", "type": "pump", "location": {"latitude": 24.86, "longitude": 67.00}, "contact": "+10000000001"},
        {"id": "res2", "type": "fire_truck", "location": {"latitude": 24.96, "longitude": 67.11}, "contact": "+10000000002"},
    ]
    sample_events = [
        {"event_id": "ev1", "type": "flood", "location": {"latitude": 24.8607, "longitude": 67.0011}, "summary": "Flood in Ward 12"},
        {"event_id": "ev2", "type": "wildfire", "location": {"latitude": 24.95, "longitude": 67.10}, "summary": "Wildfire near industrial area"},
    ]

    tool = LogisticsRoutingTool()
    out = tool._run(plans_recommended=sample_plans, resources=sample_resources, events=sample_events, dry_run=True)
    print(json.dumps(out, indent=2, ensure_ascii=False))
