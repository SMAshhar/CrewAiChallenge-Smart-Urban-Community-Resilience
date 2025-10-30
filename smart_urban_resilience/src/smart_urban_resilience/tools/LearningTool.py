# # src/smart_urban_resilience/tools/LearningTool.py
# """
# LearningTool — CrewAI BaseTool

# Responsibilities:
# - Accept post-execution logs, human feedback, outcome metrics.
# - Produce labeled training rows (JSONL/CSV) suitable for retraining models or auditing.
# - Compute simple eval metrics (success rate, avg latency).
# - Optionally persist artifacts to disk (output_dir) and optionally log to MLflow (guarded).
# - Dry-run by default for safe demos.

# Usage:
# - Call _run with `runs` (list of execution records) and optional `output_dir`, `mlflow_tracking_uri`.
# """

# from __future__ import annotations
# import json
# import os
# import time
# import logging
# from typing import Any, Dict, List, Optional, Type
# from pydantic import BaseModel, Field
# from crewai.tools import BaseTool

# # Optional MLflow
# try:
#     import mlflow
#     HAVE_MLFLOW = True
# except Exception:
#     mlflow = None
#     HAVE_MLFLOW = False

# logging.basicConfig(level=logging.INFO)
# LOG = logging.getLogger("LearningTool")


# class RunRecord(BaseModel):
#     """Single execution record / outcome (one line for training data)."""
#     run_id: str
#     agent_id: Optional[str] = None
#     trace_id: Optional[str] = None
#     timestamp: Optional[str] = None  # ISO format
#     task: Optional[str] = None
#     input_summary: Optional[Dict[str, Any]] = None
#     output_summary: Optional[Dict[str, Any]] = None
#     human_feedback: Optional[Dict[str, Any]] = None  # e.g. {"label":"correct"/"incorrect","notes": "..."}
#     metrics: Optional[Dict[str, float]] = None  # e.g. {"latency_s": 12.3, "confidence": 0.91}
#     tags: Optional[Dict[str, Any]] = None


# class LearningInput(BaseModel):
#     runs: List[RunRecord] = Field(..., description="List of run records (outcomes and feedback).")
#     output_dir: Optional[str] = Field("learning_outputs", description="Directory where artifacts will be stored.")
#     persist_jsonl: Optional[bool] = Field(True, description="Write JSONL training rows to disk.")
#     persist_csv: Optional[bool] = Field(False, description="Also write CSV (best-effort).")
#     mlflow_tracking_uri: Optional[str] = Field(None, description="If set and mlflow available, log artifact to MLflow.")
#     dry_run: Optional[bool] = Field(True, description="If True, do not call MLflow or modify external systems.")


# class LearningTool(BaseTool):
#     name: str = "Learning Tool"
#     description: str = "Collects run outcomes & human feedback, emits labeled datasets and simple eval metrics."
#     args_schema: Type[BaseModel] = LearningInput

#     def _ensure_dir(self, p: str) -> None:
#         os.makedirs(p, exist_ok=True)

#     def _to_csv_row(self, r: RunRecord) -> Dict[str, Any]:
#         # Flatten a few commonly-relevant fields for lightweight CSV (not exhaustive)
#         return {
#             "run_id": r.run_id,
#             "agent_id": r.agent_id or "",
#             "task": r.task or "",
#             "ts": r.timestamp or "",
#             "label": (r.human_feedback or {}).get("label") if r.human_feedback else "",
#             "latency_s": (r.metrics or {}).get("latency_s", ""),
#             "confidence": (r.metrics or {}).get("confidence", ""),
#             "notes": (r.human_feedback or {}).get("notes", ""),
#         }

#     def _run(self, runs: List[RunRecord],
#              output_dir: str = "learning_outputs",
#              persist_jsonl: bool = True,
#              persist_csv: bool = False,
#              mlflow_tracking_uri: Optional[str] = None,
#              dry_run: bool = True) -> Dict[str, Any]:
#         t0 = time.time()
#         total = len(runs)
#         # Basic aggregated metrics
#         success_count = 0
#         latency_vals: List[float] = []
#         confidence_vals: List[float] = []
#         labels_counter: Dict[str, int] = {}

#         # Prepare output
#         if persist_jsonl or persist_csv:
#             self._ensure_dir(output_dir)

#         jsonl_path = os.path.join(output_dir, f"learning_{int(t0)}.jsonl")
#         csv_path = os.path.join(output_dir, f"learning_{int(t0)}.csv")

#         # Write JSONL and collect stats
#         if persist_jsonl:
#             f_jsonl = open(jsonl_path, "w", encoding="utf-8")
#         else:
#             f_jsonl = None

#         csv_rows: List[Dict[str, Any]] = []

#         for r in runs:
#             # normalize timestamp
#             rec = r.dict()
#             if f_jsonl:
#                 f_jsonl.write(json.dumps(rec, ensure_ascii=False) + "\n")

#             # stats
#             lbl = (r.human_feedback or {}).get("label") if r.human_feedback else None
#             if lbl:
#                 labels_counter[str(lbl)] = labels_counter.get(str(lbl), 0) + 1
#                 if str(lbl).lower() in ("correct", "true", "ok", "success", "1"):
#                     success_count += 1
#             lat = (r.metrics or {}).get("latency_s")
#             if isinstance(lat, (int, float)):
#                 latency_vals.append(float(lat))
#             conf = (r.metrics or {}).get("confidence")
#             if isinstance(conf, (int, float)):
#                 confidence_vals.append(float(conf))

#             if persist_csv:
#                 csv_rows.append(self._to_csv_row(r))

#         if f_jsonl:
#             f_jsonl.close()

#         # write CSV if requested (best-effort)
#         if persist_csv and csv_rows:
#             try:
#                 import csv
#                 keys = list(csv_rows[0].keys())
#                 with open(csv_path, "w", newline="", encoding="utf-8") as cf:
#                     writer = csv.DictWriter(cf, fieldnames=keys)
#                     writer.writeheader()
#                     for row in csv_rows:
#                         writer.writerow(row)
#             except Exception as e:
#                 LOG.warning("CSV write failed: %s", e)

#         # compute aggregates
#         success_rate = (success_count / total) if total > 0 else None
#         avg_latency = (sum(latency_vals) / len(latency_vals)) if latency_vals else None
#         avg_confidence = (sum(confidence_vals) / len(confidence_vals)) if confidence_vals else None

#         elapsed = time.time() - t0
#         result = {
#             "total_runs": total,
#             "success_count": success_count,
#             "labels": labels_counter,
#             "avg_latency_s": avg_latency,
#             "avg_confidence": avg_confidence,
#             "jsonl_path": jsonl_path if persist_jsonl else None,
#             "csv_path": csv_path if persist_csv else None,
#             "elapsed_s": round(elapsed, 3)
#         }

#         # Optionally log artifact to MLflow
#         if mlflow_tracking_uri and HAVE_MLFLOW and not dry_run:
#             try:
#                 mlflow.set_tracking_uri(mlflow_tracking_uri)
#                 with mlflow.start_run(run_name="learning-aggregate"):
#                     # log basic metrics
#                     if avg_latency is not None:
#                         mlflow.log_metric("avg_latency_s", avg_latency)
#                     if avg_confidence is not None:
#                         mlflow.log_metric("avg_confidence", avg_confidence)
#                     mlflow.log_metric("total_runs", total)
#                     # log files as artifacts
#                     if persist_jsonl and os.path.exists(jsonl_path):
#                         mlflow.log_artifact(jsonl_path, artifact_path="learning")
#                     if persist_csv and os.path.exists(csv_path):
#                         mlflow.log_artifact(csv_path, artifact_path="learning")
#                     result["mlflow_run"] = mlflow.active_run().info.run_id
#             except Exception as e:
#                 LOG.warning("MLflow logging failed: %s", e)
#                 result["mlflow_error"] = str(e)

#         # return summary
#         return {"result": result}

# # ----------------------------
# # Test harness
# # ----------------------------
# if __name__ == "__main__":
#     # Create a few synthetic run records
#     sample_runs = [
#         RunRecord(
#             run_id="r1",
#             agent_id="event_detector_v1",
#             timestamp="2025-10-05T12:00:00Z",
#             task="detection_task",
#             input_summary={"n_feed_items": 3},
#             output_summary={"detected_type": "flood", "confidence": 0.92},
#             human_feedback={"label": "correct", "notes": "clear flood cluster"},
#             metrics={"latency_s": 1.2, "confidence": 0.92}
#         ),
#         RunRecord(
#             run_id="r2",
#             agent_id="resource_recommender_v1",
#             timestamp="2025-10-05T12:01:00Z",
#             task="recommend_task",
#             input_summary={"event_id": "ev1"},
#             output_summary={"plans": [{"resource_id": "res1", "eta_min": 12}]},
#             human_feedback={"label": "incorrect", "notes": "resource not available"},
#             metrics={"latency_s": 2.8, "confidence": 0.55}
#         )
#     ]

#     tool = LearningTool()
#     out = tool._run(runs=sample_runs, output_dir="./data/tmp_learning", persist_jsonl=True, persist_csv=True, dry_run=True)
#     print(json.dumps(out, indent=2, ensure_ascii=False))

# src/smart_urban_resilience/tools/LearningTool.py
"""
LearningTool — CrewAI BaseTool (robust, flexible input normalization)

Changes vs original:
- Accepts flexible run dicts (no pydantic validation failure).
- Normalizes dict -> RunRecord inside _run, auto-generates run_id/timestamp when missing.
- Safe file handling and guarded MLflow logging.
"""
from __future__ import annotations
import json
import os
import time
import logging
import uuid
from typing import Any, Dict, List, Optional, Type
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Optional MLflow
try:
    import mlflow
    print("MLFLOW successfully imported.")
    HAVE_MLFLOW = True
except Exception:
    mlflow = None
    print("FAILED to import MLFLOW")
    HAVE_MLFLOW = False

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("LearningTool")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunRecord(BaseModel):
    """Single execution record / outcome (one line for training data)."""
    run_id: str
    agent_id: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: Optional[str] = None  # ISO format
    task: Optional[str] = None
    input_summary: Optional[Dict[str, Any]] = None
    output_summary: Optional[Dict[str, Any]] = None
    human_feedback: Optional[Dict[str, Any]] = None  # e.g. {"label":"correct"/"incorrect","notes": "..."}
    metrics: Optional[Dict[str, float]] = None  # e.g. {"latency_s": 12.3, "confidence": 0.91}
    tags: Optional[Dict[str, Any]] = None


class LearningInput(BaseModel):
    # Accept loose run dicts to avoid pre-validation failures from upstream agents
    runs: List[Dict[str, Any]] = Field(..., description="List of run dicts (outcomes and feedback).")
    output_dir: Optional[str] = Field("learning_outputs", description="Directory where artifacts will be stored.")
    persist_jsonl: Optional[bool] = Field(True, description="Write JSONL training rows to disk.")
    persist_csv: Optional[bool] = Field(False, description="Also write CSV (best-effort).")
    mlflow_tracking_uri: Optional[str] = Field(None, description="If set and mlflow available, log artifact to MLflow.")
    dry_run: Optional[bool] = Field(True, description="If True, do not call MLflow or modify external systems.")


class LearningTool(BaseTool):
    name: str = "Learning Tool"
    description: str = "Collects run outcomes & human feedback, emits labeled datasets and simple eval metrics."
    args_schema: Type[BaseModel] = LearningInput

    def _ensure_dir(self, p: str) -> None:
        os.makedirs(p, exist_ok=True)

    def _to_csv_row(self, r: RunRecord) -> Dict[str, Any]:
        # Flatten a few commonly-relevant fields for lightweight CSV (not exhaustive)
        return {
            "run_id": r.run_id,
            "agent_id": r.agent_id or "",
            "task": r.task or "",
            "ts": r.timestamp or "",
            "label": (r.human_feedback or {}).get("label") if r.human_feedback else "",
            "latency_s": (r.metrics or {}).get("latency_s", ""),
            "confidence": (r.metrics or {}).get("confidence", ""),
            "notes": (r.human_feedback or {}).get("notes", ""),
        }

    def _normalize_run(self, raw: Dict[str, Any]) -> RunRecord:
        """
        Convert a flexible dict into a validated RunRecord.
        Auto-generate run_id and timestamp if missing.
        """
        if not isinstance(raw, dict):
            raw = {"run_id": str(uuid.uuid4()), "output_summary": {"raw": str(raw)}}

        run_id = raw.get("run_id") or raw.get("id") or str(uuid.uuid4())
        ts = raw.get("timestamp") or raw.get("ts") or now_iso()

        # Defensive conversions for nested fields
        rr = {
            "run_id": str(run_id),
            "agent_id": raw.get("agent_id") or raw.get("agent") or None,
            "trace_id": raw.get("trace_id") or raw.get("trace") or None,
            "timestamp": ts,
            "task": raw.get("task") or raw.get("phase") or None,
            "input_summary": raw.get("input_summary") or raw.get("input") or None,
            "output_summary": raw.get("output_summary") or raw.get("output") or None,
            "human_feedback": raw.get("human_feedback") or raw.get("feedback") or None,
            "metrics": raw.get("metrics") or raw.get("meta") or None,
            "tags": raw.get("tags") or None,
        }
        # Validate / coerce using RunRecord model
        try:
            return RunRecord(**rr)
        except Exception as e:
            # Last-resort: ensure at least run_id and timestamp present
            LOG.warning("RunRecord validation warning for run_id=%s: %s", rr.get("run_id"), e)
            rr["run_id"] = rr.get("run_id") or str(uuid.uuid4())
            rr["timestamp"] = rr.get("timestamp") or now_iso()
            return RunRecord(**rr)

    def _run(self, runs: List[Dict[str, Any]],
             output_dir: str = "learning_outputs",
             persist_jsonl: bool = True,
             persist_csv: bool = False,
             mlflow_tracking_uri: Optional[str] = None,
             dry_run: bool = True) -> Dict[str, Any]:
        t0 = time.time()

        normalized_runs: List[RunRecord] = []
        for raw in runs:
            try:
                rr = self._normalize_run(raw)
                normalized_runs.append(rr)
            except Exception as e:
                LOG.warning("Skipping invalid run entry: %s (error: %s)", raw, e)
                continue

        total = len(normalized_runs)
        # Basic aggregated metrics
        success_count = 0
        latency_vals: List[float] = []
        confidence_vals: List[float] = []
        labels_counter: Dict[str, int] = {}

        # Prepare output
        if persist_jsonl or persist_csv:
            self._ensure_dir(output_dir)

        jsonl_path = os.path.join(output_dir, f"learning_{int(t0)}.jsonl")
        csv_path = os.path.join(output_dir, f"learning_{int(t0)}.csv")

        f_jsonl = None
        try:
            if persist_jsonl:
                f_jsonl = open(jsonl_path, "w", encoding="utf-8")
        except Exception as e:
            LOG.warning("Could not open JSONL file for writing: %s", e)
            f_jsonl = None

        csv_rows: List[Dict[str, Any]] = []

        for r in normalized_runs:
            rec = r.dict()
            # write JSONL line
            if f_jsonl:
                try:
                    f_jsonl.write(json.dumps(rec, ensure_ascii=False) + "\n")
                except Exception as e:
                    LOG.warning("Failed to write JSONL line for run %s: %s", r.run_id, e)

            # stats
            lbl = (r.human_feedback or {}).get("label") if r.human_feedback else None
            if lbl:
                labels_counter[str(lbl)] = labels_counter.get(str(lbl), 0) + 1
                if str(lbl).lower() in ("correct", "true", "ok", "success", "1"):
                    success_count += 1
            lat = (r.metrics or {}).get("latency_s")
            if isinstance(lat, (int, float)):
                latency_vals.append(float(lat))
            conf = (r.metrics or {}).get("confidence")
            if isinstance(conf, (int, float)):
                confidence_vals.append(float(conf))

            if persist_csv:
                csv_rows.append(self._to_csv_row(r))

        if f_jsonl:
            try:
                f_jsonl.close()
            except Exception:
                pass

        # write CSV if requested (best-effort)
        if persist_csv and csv_rows:
            try:
                import csv
                keys = list(csv_rows[0].keys())
                with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                    writer = csv.DictWriter(cf, fieldnames=keys)
                    writer.writeheader()
                    for row in csv_rows:
                        writer.writerow(row)
            except Exception as e:
                LOG.warning("CSV write failed: %s", e)

        # compute aggregates
        success_rate = (success_count / total) if total > 0 else None
        avg_latency = (sum(latency_vals) / len(latency_vals)) if latency_vals else None
        avg_confidence = (sum(confidence_vals) / len(confidence_vals)) if confidence_vals else None

        elapsed = time.time() - t0
        result = {
            "total_runs": total,
            "success_count": success_count,
            "labels": labels_counter,
            "avg_latency_s": avg_latency,
            "avg_confidence": avg_confidence,
            "success_rate": success_rate,
            "jsonl_path": jsonl_path if persist_jsonl else None,
            "csv_path": csv_path if persist_csv else None,
            "elapsed_s": round(elapsed, 3)
        }

        # Optionally log artifact to MLflow
        if mlflow_tracking_uri and HAVE_MLFLOW and not dry_run:
            try:
                mlflow.set_tracking_uri(mlflow_tracking_uri)
                with mlflow.start_run(run_name="learning-aggregate"):
                    if avg_latency is not None:
                        mlflow.log_metric("avg_latency_s", avg_latency)
                    if avg_confidence is not None:
                        mlflow.log_metric("avg_confidence", avg_confidence)
                    mlflow.log_metric("total_runs", total)
                    if persist_jsonl and os.path.exists(jsonl_path):
                        mlflow.log_artifact(jsonl_path, artifact_path="learning")
                    if persist_csv and os.path.exists(csv_path):
                        mlflow.log_artifact(csv_path, artifact_path="learning")
                    result["mlflow_run"] = mlflow.active_run().info.run_id
            except Exception as e:
                LOG.warning("MLflow logging failed: %s", e)
                result["mlflow_error"] = str(e)

        return {"result": result}


# ----------------------------
# Test harness
if __name__ == "__main__":
    # Create a few synthetic run dicts (note one without run_id to test auto-generation)
    sample_runs = [
        {
            "agent_id": "event_detector_v1",
            "timestamp": "2025-10-05T12:00:00Z",
            "task": "detection_task",
            "input_summary": {"n_feed_items": 3},
            "output_summary": {"detected_type": "flood", "confidence": 0.92},
            "human_feedback": {"label": "correct", "notes": "clear flood cluster"},
            "metrics": {"latency_s": 1.2, "confidence": 0.92}
        },
        {
            "run_id": "r2",
            "agent_id": "resource_recommender_v1",
            "timestamp": "2025-10-05T12:01:00Z",
            "task": "recommend_task",
            "input_summary": {"event_id": "ev1"},
            "output_summary": {"plans": [{"resource_id": "res1", "eta_min": 12}]},
            "human_feedback": {"label": "incorrect", "notes": "resource not available"},
            "metrics": {"latency_s": 2.8, "confidence": 0.55}
        }
    ]

    tool = LearningTool()
    out = tool._run(runs=sample_runs, output_dir="./data/tmp_learning", persist_jsonl=True, persist_csv=True, dry_run=True)
    print(json.dumps(out, indent=2, ensure_ascii=False))
