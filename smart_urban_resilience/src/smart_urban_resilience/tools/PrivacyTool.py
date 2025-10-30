# src/smart_urban_resilience/tools/PrivacyTool.py
from __future__ import annotations
import re
import os
import json
import time
import logging
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Callable, Type, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("PrivacyTool")


# ----------------------------
# Pydantic input schema
# ----------------------------
class ConsentRecord(BaseModel):
    """Simple consent record representation used by the tool for lookups."""
    user_id: Optional[str] = None
    source_id: Optional[str] = None
    consent_given: bool = True
    expires_at: Optional[str] = None  # ISO timestamp or None


class PrivacyInput(BaseModel):
    """Arguments to PrivacyTool._run"""
    record: Dict[str, Any] = Field(..., description="Single event/record to sanitize (dict).")
    # optional consent records to check against; tool can check by user_id or source_id in record
    consent_records: Optional[List[Dict[str, Any]]] = Field(None, description="Optional list of consent records.")
    mode: Optional[str] = Field("mask", description="sanitization mode: 'mask' | 'pseudonymize'")
    mask_char: Optional[str] = Field("*", description="Character used when masking values")
    mask_keep_last: Optional[int] = Field(2, description="When masking, keep this many chars at end (if applicable)")
    pseudonym_salt: Optional[str] = Field("privacy_salt", description="Salt for pseudonymization hashing")
    persist_audit: Optional[bool] = Field(True, description="If True, append audit entry to output_dir/privacy_audit.jsonl")
    output_dir: Optional[str] = Field("privacy_outputs", description="Directory for audit files")
    retention_days: Optional[int] = Field(90, description="Retention hint in days (for audit metadata)")
    pii_keys: Optional[List[str]] = Field(None, description="Optional override list of keys to treat as PII (heuristic keys)")
    custom_value_patterns: Optional[List[str]] = Field(None, description="Extra regex patterns to treat as PII in values")


# ----------------------------
# Helper utils
# ----------------------------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", flags=re.I)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")
COORD_RE = re.compile(r"-?\d{1,3}\.\d+")  # simple float capture (used cautiously)
NID_RE = re.compile(r"\b(?:ssn|nid|cnic|nic|id)\b[:\s#-]*([0-9\-]{4,})", flags=re.I)

DEFAULT_PII_KEYS = [
    "name", "full_name", "first_name", "last_name",
    "phone", "phone_number", "mobile",
    "email", "address", "street", "city", "postcode", "zip",
    "ssn", "nid", "nic", "cnic", "id_number",
    "birthdate", "dob", "date_of_birth",
    "latitude", "longitude", "lat", "lon",
]


def _is_pii_key(key: str, override_keys: Optional[List[str]] = None) -> bool:
    key = (key or "").lower()
    keys = [k.lower() for k in (override_keys or DEFAULT_PII_KEYS)]
    return any(k in key for k in keys)


def _value_matches_pii(value: Any, extra_patterns: Optional[List[str]] = None) -> bool:
    if value is None:
        return False
    s = str(value)
    # quick checks
    if EMAIL_RE.search(s):
        return True
    if PHONE_RE.fullmatch(s.strip()):
        return True
    if NID_RE.search(s):
        return True
    # coordinates: only if the key is known to be geolocation; here used conservatively elsewhere
    # extra custom patterns
    if extra_patterns:
        for pat in extra_patterns:
            try:
                if re.search(pat, s):
                    return True
            except Exception:
                continue
    return False


def _mask_value(value: Any, mask_char: str = "*", keep_last: int = 2) -> str:
    s = str(value)
    if not s:
        return s
    visible = s[-keep_last:] if len(s) > keep_last else ""
    masked_len = max(0, len(s) - len(visible))
    return mask_char * masked_len + visible


def _pseudonymize_value(value: Any, salt: str = "privacy_salt") -> str:
    if value is None:
        return ""
    raw = (str(value) + "|" + salt).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


# ----------------------------
# Core tool
# ----------------------------
class PrivacyTool(BaseTool):
    name: str = "Privacy Tool"
    description: str = "Detects and redacts/pseudonymizes PII in records; emits an audit entry and optional persisted logs."
    args_schema: Type[BaseModel] = PrivacyInput

    def _sanitize_item(
        self,
        item: Any,
        key_hint: Optional[str],
        mode: str,
        mask_char: str,
        mask_keep_last: int,
        salt: str,
        extra_patterns: Optional[List[str]],
        pii_keys_override: Optional[List[str]],
    ) -> Tuple[Any, List[Tuple[str, Any]]]:
        """
        Recursively sanitize `item`. Returns (sanitized_item, list_of_detected_pii_pairs(key_path, original_value))
        """
        pii_found: List[Tuple[str, Any]] = []

        if isinstance(item, dict):
            out = {}
            for k, v in item.items():
                path = k if not key_hint else f"{key_hint}.{k}"
                sanitized_v, found = self._sanitize_item(v, path, mode, mask_char, mask_keep_last, salt, extra_patterns, pii_keys_override)
                out[k] = sanitized_v
                pii_found.extend(found)
            return out, pii_found

        if isinstance(item, list):
            out_list = []
            for idx, el in enumerate(item):
                path = f"{key_hint}[{idx}]" if key_hint else f"[{idx}]"
                sanitized_el, found = self._sanitize_item(el, path, mode, mask_char, mask_keep_last, salt, extra_patterns, pii_keys_override)
                out_list.append(sanitized_el)
                pii_found.extend(found)
            return out_list, pii_found

        # primitive value
        # decide using key hint or value patterns
        key_is_pii = False
        if key_hint:
            # look at final key part
            final_key = key_hint.split(".")[-1].split("[")[0]
            key_is_pii = _is_pii_key(final_key, override_keys=pii_keys_override)

        value_is_pii = _value_matches_pii(item, extra_patterns=extra_patterns)

        if key_is_pii or value_is_pii:
            # redact/pseudonymize
            original = item
            if mode == "pseudonymize":
                new_val = _pseudonymize_value(item, salt)
            else:
                new_val = _mask_value(item, mask_char, mask_keep_last)
            pii_found.append((key_hint or "<value>", original))
            return new_val, pii_found

        # otherwise return original unchanged
        return item, []

    def _check_consent_simple(self, record: Dict[str, Any], consent_list: Optional[List[Dict[str, Any]]]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Basic consent check:
        - If record contains 'user_id' or 'source_id', try to find matching consent in consent_list.
        - Returns (status, matching_record)
        status in: "valid" | "missing" | "expired"
        """
        if not consent_list:
            return "missing", None
        uid = record.get("user_id") or record.get("source_id") or record.get("operator_id")
        if not uid:
            # nothing to check
            return "missing", None
        for c in consent_list:
            # accept either user_id or source_id matching
            if str(c.get("user_id")) == str(uid) or str(c.get("source_id")) == str(uid):
                # check expiry if present
                expires = c.get("expires_at")
                try:
                    if expires:
                        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        if exp_dt < datetime.utcnow():
                            return "expired", c
                    return ("valid", c)
                except Exception:
                    return ("valid", c)
        return "missing", None

    def _run(
        self,
        record: Dict[str, Any],
        consent_records: Optional[List[Dict[str, Any]]] = None,
        mode: str = "mask",
        mask_char: str = "*",
        mask_keep_last: int = 2,
        pseudonym_salt: str = "privacy_salt",
        persist_audit: bool = True,
        output_dir: str = "privacy_outputs",
        retention_days: int = 90,
        pii_keys: Optional[List[str]] = None,
        custom_value_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Sanitize a record and emit an audit entry.
        """
        t0 = time.time()
        # normalize params
        mode = (mode or "mask").lower()
        mask_char = mask_char or "*"
        mask_keep_last = int(mask_keep_last or 2)
        pseudonym_salt = pseudonym_salt or "privacy_salt"
        retention_days = int(retention_days or 90)
        persist_audit = bool(persist_audit)

        # sanitize record (deep copy)
        try:
            rec_copy = json.loads(json.dumps(record))  # simple deep copy (keeps JSON-serializable)
        except Exception:
            rec_copy = dict(record) if isinstance(record, dict) else {}

        sanitized, pii_pairs = self._sanitize_item(
            rec_copy,
            key_hint="",
            mode=mode,
            mask_char=mask_char,
            mask_keep_last=mask_keep_last,
            salt=pseudonym_salt,
            extra_patterns=custom_value_patterns,
            pii_keys_override=pii_keys,
        )

        # consent check
        consent_status, consent_meta = self._check_consent_simple(record, consent_records)

        # audit entry
        audit = {
            "timestamp": _now_iso(),
            "record_id": record.get("event_id") or record.get("id") or None,
            "pii_detected_count": len(pii_pairs),
            "pii_fields": [p[0] for p in pii_pairs],
            "pii_samples": [ (p[0], str(p[1])) for p in pii_pairs[:5] ],  # small sample for debugging (avoid storing too much PII)
            "sanitization_mode": mode,
            "consent_status": consent_status,
            "consent_meta": consent_meta if consent_meta else None,
            "retention_days": retention_days,
        }

        persisted_path = None
        if persist_audit:
            try:
                _ensure_dir(output_dir)
                audit_path = os.path.join(output_dir, "privacy_audit.jsonl")
                with open(audit_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(audit, ensure_ascii=False) + "\n")
                persisted_path = audit_path
            except Exception as e:
                LOG.warning("Failed to persist audit: %s", e)

        elapsed = time.time() - t0
        return {
            "sanitized_record": sanitized,
            "audit": audit,
            "audit_path": persisted_path,
            "elapsed_s": round(elapsed, 3),
        }


# ----------------------------
# Test harness
# ----------------------------
if __name__ == "__main__":
    # Example record with several PII fields
    sample = {
        "event_id": "ev-123",
        "source": "citizen_report",
        "user_id": "user-42",
        "reporter": {"name": "Ali Khan", "phone": "+923001234567", "email": "ali.k@example.com"},
        "location": {"latitude": 24.8607, "longitude": 67.0011, "address": "Embankment Road, Karachi"},
        "notes": "Observed flood in basement near house #42",
        "payload": {"nested_email": "nested@example.com", "nonpi": "ok"}
    }
    consent_list = [
        {"user_id": "user-42", "consent_given": True, "expires_at": None},
        {"user_id": "user-99", "consent_given": False, "expires_at": "2025-01-01T00:00:00Z"},
    ]

    tool = PrivacyTool()
    out = tool._run(
        record=sample,
        consent_records=consent_list,
        mode="pseudonymize",
        persist_audit=True,
        output_dir="./.tmp_privacy",
        mask_keep_last=2,
        pseudonym_salt="my_salt_2025",
    )
    print(json.dumps(out, indent=2, ensure_ascii=False))
