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
        
        print(f"Detected event: {event} for record: {record}")

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
