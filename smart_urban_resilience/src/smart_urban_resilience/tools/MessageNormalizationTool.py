from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import uuid

class MessageNormalizationInput(BaseModel):
    incident_output: dict = Field(..., description="Raw output from Incident Commander Agent.")

class MessageNormalizationTool(BaseTool):
    name: str = "Message Normalization Tool"
    description: str = "Normalize approved messages from Incident Command output into CommunicationTool-compatible format."

    def _run(self, incident_output: dict) -> dict:
        approved = incident_output.get("approval", "").lower() == "approve"
        if not approved:
            return {"messages": [], "note": "Incident not approved, skipping send."}

        normalized = []
        for msg in incident_output.get("approved_messages", []):
            for r in msg.get("recipients", []):
                normalized.append({
                    "id": str(uuid.uuid4()),
                    "channel": msg.get("channel", "sms"),
                    "to": r,
                    "body": msg.get("text") or msg.get("body", ""),
                    "metadata": {"source": "incident_command"}
                })
        return {"messages": normalized, "dry_run": True}
