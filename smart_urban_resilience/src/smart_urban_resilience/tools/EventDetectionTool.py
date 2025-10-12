# import json
# import logging
# import uuid
# from datetime import datetime, timezone
# from typing import List, Dict, Any
# from pydantic import BaseModel, Field, ValidationError

# import numpy as np

# # Optional ML imports
# try:
#     from sklearn.ensemble import IsolationForest
#     print("sklearn is available for ML-based event detection.")
#     HAVE_SKLEARN = True
# except ImportError:
#     print("sklearn not available; ML-based event detection will be disabled.")
#     HAVE_SKLEARN = False


# # -----------------------------------------------------------------------------
# # Logger setup
# # -----------------------------------------------------------------------------
# logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
# logger = logging.getLogger("EventDetector")


# # -----------------------------------------------------------------------------
# # Input Schema
# # -----------------------------------------------------------------------------
# class EventDetectionInput(BaseModel):
#     records: List[Dict[str, Any]] = Field(..., description="List of normalized sensor or feed records.")
#     threshold: float = Field(0.85, description="Confidence threshold for flagging events.")
#     method: str = Field("rule", description="Detection method: 'rule' or 'ml'.")


# # -----------------------------------------------------------------------------
# # Event Detection Tool
# # -----------------------------------------------------------------------------
# class EventDetectionTool:
#     """
#     Detects anomalies, events, or significant changes in environmental data
#     such as pollution spikes, temperature surges, or sudden humidity drops.
#     """

#     def __init__(self, threshold: float = 0.85, method: str = "rule"):
#         self.threshold = threshold
#         self.method = method.lower().strip()
#         if self.method == "ml" and not HAVE_SKLEARN:
#             logger.warning("[EventDetectionTool] ML mode requested but sklearn not installed. Falling back to rule mode.")
#             self.method = "rule"

#     def detect(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
#         events = []
#         errors = []

#         for record in records:
#             try:
#                 event = self._process_record(record)
#                 if event:
#                     events.append(event)
#             except Exception as e:
#                 logger.error(f"Error processing record {record.get('id', 'unknown')}: {e}")
#                 errors.append({"record": record, "error": str(e)})

#         return {
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "events_detected": events,
#             "stats": {
#                 "input_count": len(records),
#                 "events_found": len(events),
#                 "errors": len(errors)
#             },
#             "errors": errors
#         }

#     def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Detect an event based on rule or ML logic.
#         Example input record should have keys like temperature_c, humidity, aqi, etc.
#         """
#         if self.method == "rule":
#             return self._rule_based_detection(record)
#         elif self.method == "ml":
#             return self._ml_based_detection(record)
#         else:
#             raise ValueError(f"Unknown detection method: {self.method}")

#     # -------------------------------------------------------------------------
#     # RULE-BASED DETECTION
#     # -------------------------------------------------------------------------
#     def _rule_based_detection(self, record: Dict[str, Any]) -> Dict[str, Any]:
#         temperature = record.get("temperature_c")
#         aqi = record.get("aqi")
#         uv_index = record.get("uv_index")
#         pollen = record.get("pollen_index")

#         event = None
#         if aqi and aqi > 150:
#             event = "High Air Pollution"
#         elif uv_index and uv_index > 8:
#             event = "Extreme UV Alert"
#         elif pollen and pollen > 9:
#             event = "High Pollen Alert"
#         elif temperature and temperature > 45:
#             event = "Extreme Heat Alert"

#         if event:
#             logger.info(f"[EventDetectionTool] {event} detected at {record.get('location', {}).get('city', 'unknown')}")
#             return {
#                 "event_id": str(uuid.uuid4()),
#                 "type": event,
#                 "severity": self._calculate_severity(record),
#                 "detected_at": datetime.now(timezone.utc).isoformat(),
#                 "source_record": record.get("id", "unknown")
#             }
#         return None

#     # -------------------------------------------------------------------------
#     # ML-BASED DETECTION (IsolationForest)
#     # -------------------------------------------------------------------------
#     def _ml_based_detection(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
#         if not HAVE_SKLEARN:
#             raise RuntimeError("ML-based detection requires scikit-learn to be installed.")

#         features = []
#         ids = []
#         for r in records:
#             if "temperature_c" in r and "aqi" in r:
#                 features.append([r["temperature_c"], r["aqi"]])
#                 ids.append(r.get("id", str(uuid.uuid4())))

#         if not features:
#             logger.warning("No valid records for ML-based detection.")
#             return []

#         X = np.array(features)
#         model = IsolationForest(contamination=0.05, random_state=42)
#         preds = model.fit_predict(X)

#         events = []
#         for i, pred in enumerate(preds):
#             if pred == -1:
#                 events.append({
#                     "event_id": str(uuid.uuid4()),
#                     "type": "Anomalous Environment Reading",
#                     "severity": 0.9,
#                     "detected_at": datetime.now(timezone.utc).isoformat(),
#                     "source_record": ids[i]
#                 })

#         return events

#     # -------------------------------------------------------------------------
#     # HELPER METHODS
#     # -------------------------------------------------------------------------
#     def _calculate_severity(self, record: Dict[str, Any]) -> float:
#         """
#         Derive a severity score between 0 and 1 based on thresholds.
#         """
#         score = 0.0
#         if record.get("aqi"):
#             score += min(record["aqi"] / 500, 1.0)
#         if record.get("uv_index"):
#             score += min(record["uv_index"] / 11, 1.0)
#         if record.get("temperature_c"):
#             score += min(record["temperature_c"] / 50, 1.0)
#         if record.get("pollen_index"):
#             score += min(record["pollen_index"] / 12, 1.0)
#         return round(min(score / 4, 1.0), 2)


# # -----------------------------------------------------------------------------
# # JSON Schema (for task.yaml integration)
# # -----------------------------------------------------------------------------
# EVENT_DETECTION_TOOL_SCHEMA = {
#     "title": "EventDetectionToolInput",
#     "type": "object",
#     "properties": {
#         "records": {
#             "type": "array",
#             "items": {"type": "object"},
#             "description": "List of normalized sensor data records."
#         },
#         "threshold": {
#             "type": "number",
#             "default": 0.85,
#             "description": "Confidence threshold for flagging events."
#         },
#         "method": {
#             "type": "string",
#             "enum": ["rule", "ml"],
#             "default": "rule",
#             "description": "Detection method."
#         }
#     },
#     "required": ["records"]
# }


# # -----------------------------------------------------------------------------
# # TEST HARNESS
# # -----------------------------------------------------------------------------
# if __name__ == "__main__":
#     sample_input = {
#         "records": [
#             {
#                 "id": "rec1",
#                 "temperature_c": 48,
#                 "aqi": 130,
#                 "uv_index": 9,
#                 "pollen_index": 10,
#                 "location": {"city": "Karachi"}
#             },
#             {
#                 "id": "rec2",
#                 "temperature_c": 29,
#                 "aqi": 180,
#                 "uv_index": 6,
#                 "pollen_index": 4,
#                 "location": {"city": "Lahore"}
#             },
#             {
#                 "id": "rec3",
#                 "temperature_c": 22,
#                 "aqi": 80,
#                 "uv_index": 5,
#                 "pollen_index": 3,
#                 "location": {"city": "Islamabad"}
#             }
#         ],
#         "method": "rule"
#     }

#     try:
#         validated = EventDetectionInput(**sample_input)
#         tool = EventDetectionTool(threshold=validated.threshold, method=validated.method)
#         output = tool.detect(validated.records)
#         print(json.dumps(output, indent=2))
#         print("\nJSON Schema:\n")
#         print(json.dumps(EVENT_DETECTION_TOOL_SCHEMA, indent=2))
#     except ValidationError as e:
#         logger.error(f"Schema validation failed: {e}")

from crewai.tools import BaseTool
from pydantic import Field
from typing import List, Dict, Any
import json
from datetime import datetime, timezone
import uuid
import logging


class EventDetectionTool(BaseTool):
    name: str = "Event Detection Tool"
    description: str = "Detects environmental anomalies such as high pollution, UV index, or pollen spikes."
    threshold: float = Field(0.85, description="Confidence threshold for flagging events.")
    method: str = Field("rule", description="Detection method: 'rule' or 'ml'.")

    def _run(self, records: List[Dict[str, Any]]) -> str:
        """Required method for CrewAI BaseTool"""
        events = []

        for record in records:
            event = self._rule_based_detection(record)
            if event:
                events.append(event)

        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "events_detected": events,
            "stats": {
                "input_count": len(records),
                "events_found": len(events)
            }
        }

        return json.dumps(output, indent=2)

    def _rule_based_detection(self, record: Dict[str, Any]) -> Dict[str, Any]:
        aqi = record.get("aqi")
        uv_index = record.get("uv_index")
        pollen = record.get("pollen_index")

        if aqi and aqi > 150:
            event = "High Air Pollution"
        elif uv_index and uv_index > 8:
            event = "Extreme UV Alert"
        elif pollen and pollen > 9:
            event = "High Pollen Alert"
        else:
            return None

        return {
            "event_id": str(uuid.uuid4()),
            "type": event,
            "severity": 0.9,
            "location": record.get("location", {}),
            "detected_at": datetime.now(timezone.utc).isoformat()
        }


# Test harness
if __name__ == "__main__":
    sample_records = [
        {"aqi": 190, "uv_index": 6, "pollen_index": 5, "location": {"city": "Lahore"}},
        {"aqi": 80, "uv_index": 9, "pollen_index": 3, "location": {"city": "Karachi"}}
    ]
    tool = EventDetectionTool()
    print(tool._run(sample_records))
