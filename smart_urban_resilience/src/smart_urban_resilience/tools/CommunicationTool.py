# src/smart_urban_resilience/tools/CommunicationTool.py
"""
CommunicationTool — CrewAI BaseTool

Purpose:
- Format templated messages for events and resource dispatches.
- Deliver via Twilio (SMS/WhatsApp) or SMTP email (both guarded).
- Dry-run mode by default for reproducible demos.
- Returns per-message status and diagnostics.

Usage:
- Provide messages list (target, channel, text/template data).
- Provide twilio_config or smtp_config to actually send (otherwise dry-run).
"""

from __future__ import annotations
import logging
import time
import json
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Guarded external libs
try:
    from twilio.rest import Client as TwilioClient
    print("Twilio successfully imported. ")
except Exception:
    print("Failed to import Twilio")
    TwilioClient = None

try:
    import smtplib
    from email.message import EmailMessage
except Exception:
    smtplib = None
    EmailMessage = None

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("CommunicationTool")


# ---------- input schema
class MessageSpec(BaseModel):
    id: str = Field(..., description="Unique id for the message (for trace/idempotency).")
    channel: str = Field(..., description="one of: sms|whatsapp|email")
    to: str = Field(..., description="Recipient contact (phone e.g. +1..., or email).")
    body: Optional[str] = Field(None, description="Pre-rendered message body (optional).")
    template: Optional[str] = Field(None, description="Template string with python-format placeholders.")
    template_vars: Optional[Dict[str, Any]] = Field(None, description="Vars to format into template.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extra metadata returned in result.")


class TwilioConfig(BaseModel):
    account_sid: str
    auth_token: str
    from_number: str


class SMTPConfig(BaseModel):
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    from_address: str = "noreply@example.com"
    use_tls: bool = True


class CommunicationInput(BaseModel):
    messages: List[MessageSpec] = Field(..., description="List of messages to send.")
    twilio: Optional[TwilioConfig] = Field(None, description="Twilio config (optional).")
    smtp: Optional[SMTPConfig] = Field(None, description="SMTP config (optional).")
    dry_run: Optional[bool] = Field(True, description="If True, do not perform external sends.")
    max_retry: Optional[int] = Field(1, description="Retry attempts for network sends (exponential backoff).")
    retry_backoff_s: Optional[int] = Field(2, description="Base backoff seconds.")


# ---------- tool
class CommunicationTool(BaseTool):
    name: str = "Communication Tool"
    description: str = "Format and deliver messages via Twilio or SMTP. Dry-run by default."
    args_schema: Type[BaseModel] = CommunicationInput

    def _render_body(self, spec: MessageSpec) -> str:
        if spec.body:
            return spec.body
        if spec.template:
            try:
                return spec.template.format(**(spec.template_vars or {}))
            except Exception as e:
                LOG.debug("Template render failed for %s: %s", spec.id, e)
                return spec.template  # fallback to raw template
        return ""

    def _send_twilio(self, client: "TwilioClient", from_number: str, to: str, body: str, channel: str) -> Dict[str, Any]:
        # channel: sms or whatsapp
        try:
            if channel == "whatsapp":
                to_pref = f"whatsapp:{to}"
                from_pref = f"whatsapp:{from_number}"
            else:
                to_pref = to
                from_pref = from_number
            msg = client.messages.create(body=body, from_=from_pref, to=to_pref)
            return {"status": "ok", "sid": getattr(msg, "sid", None)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _send_smtp(self, cfg: SMTPConfig, to: str, subject: str, body: str) -> Dict[str, Any]:
        if smtplib is None or EmailMessage is None:
            return {"status": "error", "error": "smtplib not available"}
        try:
            msg = EmailMessage()
            msg["From"] = cfg.from_address
            msg["To"] = to
            msg["Subject"] = subject or "Notification"
            msg.set_content(body)
            if cfg.use_tls:
                with smtplib.SMTP(cfg.host, cfg.port, timeout=8) as s:
                    s.starttls()
                    if cfg.username and cfg.password:
                        s.login(cfg.username, cfg.password)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(cfg.host, cfg.port, timeout=8) as s:
                    if cfg.username and cfg.password:
                        s.login(cfg.username, cfg.password)
                    s.send_message(msg)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _run(
        self,
        messages: List[Any],
        twilio: Optional[TwilioConfig] = None,
        smtp: Optional[SMTPConfig] = None,
        dry_run: bool = True,
        max_retry: int = 1,
        retry_backoff_s: int = 2,
    ) -> Dict[str, Any]:
        t0 = time.time()
        results: List[Dict[str, Any]] = []
        diag = {"total": len(messages), "sent": 0, "failed": 0, "dry_run": bool(dry_run)}

        # 🩹 Fix: Normalize input to MessageSpec objects
        normalized_messages = []
        for m in messages:
            if isinstance(m, MessageSpec):
                normalized_messages.append(m)
            elif isinstance(m, dict):
                try:
                    normalized_messages.append(MessageSpec(**m))
                except Exception as e:
                    LOG.warning(f"Invalid message spec skipped: {e}")
            else:
                LOG.warning(f"Unsupported message type: {type(m)}")

        messages = normalized_messages

        # prepare twilio client (if provided and available)
        tw_client = None
        if twilio and TwilioClient:
            try:
                tw_client = TwilioClient(twilio.account_sid, twilio.auth_token)
            except Exception as e:
                LOG.warning("Twilio client init failed: %s", e)
                tw_client = None

        smtp_cfg = smtp if smtp else None

        for spec in messages:
            body = self._render_body(spec)
            attempt = 0
            last_err = None
            # dry-run short-circuit
            if dry_run:
                results.append({"id": spec.id, "status": "dry_run", "channel": spec.channel, "to": spec.to, "body": body, "metadata": spec.metadata})
                continue

            # actual send with retries
            while attempt <= max_retry:
                try:
                    if spec.channel in ("sms", "whatsapp"):
                        if not tw_client or not twilio:
                            last_err = "twilio_not_configured"
                            raise RuntimeError(last_err)
                        resp = self._send_twilio(tw_client, twilio.from_number, spec.to, body, spec.channel)
                    elif spec.channel == "email":
                        if not smtp_cfg:
                            last_err = "smtp_not_configured"
                            raise RuntimeError(last_err)
                        resp = self._send_smtp(smtp_cfg, spec.to, subject="Alert", body=body)
                    else:
                        resp = {"status": "error", "error": f"unsupported channel: {spec.channel}"}

                    if resp.get("status") == "ok":
                        results.append({"id": spec.id, "status": "ok", "channel": spec.channel, "to": spec.to, "response": resp, "metadata": spec.metadata})
                        diag["sent"] += 1
                        break
                    else:
                        last_err = resp.get("error") or str(resp)
                        attempt += 1
                        time.sleep(retry_backoff_s * (2 ** (attempt - 1)))
                except Exception as e:
                    last_err = str(e)
                    attempt += 1
                    time.sleep(retry_backoff_s * (2 ** (attempt - 1)))
            else:
                results.append({"id": spec.id, "status": "failed", "channel": spec.channel, "to": spec.to, "error": last_err, "metadata": spec.metadata})
                diag["failed"] += 1

        elapsed = time.time() - t0
        return {"results": results, "diagnostic": diag, "elapsed_s": round(elapsed, 3)}


# ---------- test harness
if __name__ == "__main__":
    test_messages = [
        MessageSpec(id="m1", channel="sms", to="+15550001111", template="Dispatch: {resource} → {place}", template_vars={"resource": "Ambulance A1", "place": "Ward 12"}),
        MessageSpec(id="m2", channel="email", to="ops@example.com", body="Human-in-the-loop: please approve plan #123", metadata={"plan_id": 123})
    ]
    tool = CommunicationTool()
    out = tool._run(messages=test_messages, dry_run=True)
    print(json.dumps(out, indent=2, ensure_ascii=False))
