# # tools/ValidationTool.py
# import logging
# from typing import Any, Dict, List, Optional, Type
# from pydantic import BaseModel, Field
# from crewai.tools import BaseTool

# # optional libs
# try:
#     import pandas as pd
#     import numpy as np
# except Exception:
#     pd = None
#     np = None

# try:
#     import jsonschema
#     from jsonschema import Draft7Validator
# except Exception:
#     jsonschema = None
#     Draft7Validator = None

# LOG = logging.getLogger("ValidationTool")
# logging.basicConfig(level=logging.INFO)


# class ValidationToolInput(BaseModel):
#     records: List[Dict[str, Any]] = Field(..., description="List of normalized records to validate.")
#     schema: Optional[Dict[str, Any]] = Field(None, description="Optional JSON Schema to validate records against.")
#     outlier_method: Optional[str] = Field("iqr", description="Outlier detection method: 'iqr' or 'zscore'. (Optional)")
#     z_thresh: Optional[float] = Field(3.0, description="Z-score threshold (used when outlier_method == 'zscore').")
#     iqr_k: Optional[float] = Field(1.5, description="IQR multiplier (used when outlier_method == 'iqr').")
#     impute: Optional[str] = Field("median", description="Imputation: 'median' | 'mean' | 'none'.")
#     impute_fields: Optional[List[str]] = Field(None, description="If provided, only impute these fields.")
#     drop_on_missing_pct: Optional[float] = Field(0.5, description="Drop record if fraction of missing fields > this value (0-1).")
#     dedupe_on: Optional[List[str]] = Field(None, description="Fields to consider for duplicate detection.")


# class ValidationTool(BaseTool):
#     name: str = "Data Validation Tool"
#     description: str = (
#         "Validates normalized records: optional JSON Schema validation, missing-checks, duplicate detection, "
#         "outlier detection (IQR or Z-score), optional imputation (median/mean). Returns cleaned records + report."
#     )
#     args_schema: Type[BaseModel] = ValidationToolInput

#     def _run(
#         self,
#         records: List[Dict[str, Any]],
#         schema: Optional[Dict[str, Any]] = None,
#         outlier_method: Optional[str] = "iqr",
#         z_thresh: Optional[float] = 3.0,
#         iqr_k: Optional[float] = 1.5,
#         impute: Optional[str] = "median",
#         impute_fields: Optional[List[str]] = None,
#         drop_on_missing_pct: Optional[float] = 0.5,
#         dedupe_on: Optional[List[str]] = None,
#     ) -> Dict[str, Any]:

#         # Normalize the optional parameters (handle incoming nulls)
#         outlier_method = (outlier_method or "iqr").lower()
#         z_thresh = float(z_thresh or 3.0)
#         iqr_k = float(iqr_k or 1.5)
#         impute = (impute or "median").lower()
#         drop_on_missing_pct = float(drop_on_missing_pct or 0.5)
#         dedupe_on = dedupe_on or ["event_id"]

#         LOG.info(f"[ValidationTool] Running validation on {len(records)} records (outlier={outlier_method}, impute={impute})")

#         report = {
#             "input_count": len(records),
#             "schema_validations": [],
#             "duplicate_ids": [],
#             "missing_counts": {},
#             "outliers": [],
#             "imputations": {},
#             "removed_by_missing": 0,
#             "kept": 0,
#         }

#         # 1) JSON Schema validation (optional)
#         if schema and Draft7Validator:
#             validator = Draft7Validator(schema)
#             schema_issues = []
#             for i, rec in enumerate(records):
#                 errs = sorted(validator.iter_errors(rec), key=lambda e: e.path)
#                 if errs:
#                     schema_issues.append({"index": i, "errors": [f"{'/'.join(map(str, e.path))}: {e.message}" for e in errs]})
#             report["schema_validations"] = schema_issues
#         elif schema and not Draft7Validator:
#             LOG.warning("[ValidationTool] jsonschema not installed; skipping schema validation.")

#         # 2) Preferred path: pandas available
#         if pd:
#             df = pd.DataFrame(records)
#             # Ensure consistent dtype handling: coerce likely-numeric columns safely
#             # First compute missing counts
#             report["missing_counts"] = {k: int(v) for k, v in df.isna().sum().to_dict().items()}

#             # Dedup detection
#             dedupe_cols = [c for c in dedupe_on if c in df.columns]
#             if dedupe_cols:
#                 dup_mask = df.duplicated(subset=dedupe_cols, keep="first")
#                 dup_rows = df[dup_mask]
#                 report["duplicate_ids"] = dup_rows[dedupe_cols].to_dict(orient="records") if not dup_rows.empty else []

#             # Drop rows with too many missing values
#             missing_frac = df.isna().mean(axis=1)
#             drop_mask = missing_frac > drop_on_missing_pct
#             report["removed_by_missing"] = int(drop_mask.sum())
#             df_clean = df[~drop_mask].copy()

#             # Identify numeric columns robustly by coercing object cols
#             numeric_cols = list(df_clean.select_dtypes(include=[np.number]).columns) if np else []
#             if np:
#                 for col in df_clean.columns:
#                     if col in numeric_cols:
#                         continue
#                     coerced = pd.to_numeric(df_clean[col], errors="coerce")
#                     # treat as numeric if a reasonable fraction converts
#                     if coerced.notna().sum() >= 1:
#                         df_clean[col] = coerced
#                         numeric_cols.append(col)

#             # Outlier detection
#             outliers = []
#             if numeric_cols:
#                 if outlier_method == "zscore" and np:
#                     means = df_clean[numeric_cols].mean()
#                     stds = df_clean[numeric_cols].std(ddof=0).replace(0, np.nan)
#                     z = (df_clean[numeric_cols] - means) / stds
#                     mask = (z.abs() > z_thresh).any(axis=1)
#                     for idx in df_clean[mask].index.tolist():
#                         cols = z.loc[idx][z.loc[idx].abs() > z_thresh].index.tolist()
#                         outliers.append({"index": int(idx), "columns": cols})
#                 else:  # IQR method
#                     for col in numeric_cols:
#                         col_series = df_clean[col].dropna()
#                         if col_series.empty:
#                             continue
#                         q1 = col_series.quantile(0.25)
#                         q3 = col_series.quantile(0.75)
#                         iqr = q3 - q1
#                         lower = q1 - iqr_k * iqr
#                         upper = q3 + iqr_k * iqr
#                         mask = (df_clean[col] < lower) | (df_clean[col] > upper)
#                         for idx in df_clean[mask].index.tolist():
#                             outliers.append({
#                                 "index": int(idx),
#                                 "column": col,
#                                 "value": float(df_clean.at[idx, col]),
#                                 "lower": float(lower),
#                                 "upper": float(upper),
#                             })
#             report["outliers"] = outliers

#             # Imputation
#             imputations = {}
#             if impute and impute != "none" and numeric_cols:
#                 fields = impute_fields or numeric_cols
#                 for c in fields:
#                     if c not in df_clean.columns:
#                         continue
#                     # ensure numeric
#                     if np:
#                         df_clean[c] = pd.to_numeric(df_clean[c], errors="coerce")
#                     if impute == "median":
#                         fill = float(df_clean[c].median(skipna=True))
#                     elif impute == "mean":
#                         fill = float(df_clean[c].mean(skipna=True))
#                     else:
#                         continue
#                     n_before = int(df_clean[c].isna().sum())
#                     df_clean[c].fillna(fill, inplace=True)
#                     n_after = int(df_clean[c].isna().sum())
#                     imputations[c] = {"method": impute, "filled": int(n_before - n_after), "value": fill}
#                 report["imputations"] = imputations

#             # Remove duplicates
#             if dedupe_cols:
#                 df_final = df_clean.drop_duplicates(subset=dedupe_cols, keep="first")
#             else:
#                 df_final = df_clean

#             cleaned = df_final.reset_index(drop=True).to_dict(orient="records")
#             # convert numpy types to native python
#             def _to_native(val):
#                 if np and isinstance(val, (np.integer, np.int32, np.int64)):
#                     return int(val)
#                 if np and isinstance(val, (np.floating, np.float32, np.float64)):
#                     return float(val)
#                 if np and isinstance(val, np.bool_):
#                     return bool(val)
#                 return val

#             cleaned_native = [{k: _to_native(v) for k, v in rec.items()} for rec in cleaned]
#             report["kept"] = len(cleaned_native)
#             return {"cleaned": cleaned_native, "report": report}

#         # 3) Fallback (no pandas)
#         LOG.warning("[ValidationTool] pandas not available — running fallback validator.")
#         def to_float_safe(v):
#             if v is None:
#                 return None
#             if isinstance(v, str):
#                 s = v.strip()
#                 if s == "" or s.lower() in ("none", "nan", "null"):
#                     return None
#             try:
#                 return float(v)
#             except Exception:
#                 return None

#         # missing counts
#         all_keys = set().union(*(r.keys() for r in records)) if records else set()
#         missing_counts = {k: 0 for k in all_keys}
#         for r in records:
#             for k in all_keys:
#                 if r.get(k) is None:
#                     missing_counts[k] += 1
#         report["missing_counts"] = missing_counts

#         # numeric fields detection
#         numeric_fields = []
#         for k in all_keys:
#             vals = [to_float_safe(r.get(k)) for r in records]
#             vals = [v for v in vals if v is not None]
#             if len(vals) >= 3:
#                 numeric_fields.append(k)

#         # outliers by IQR
#         outliers = []
#         for k in numeric_fields:
#             vals = sorted([to_float_safe(r.get(k)) for r in records if to_float_safe(r.get(k)) is not None])
#             if len(vals) < 3:
#                 continue
#             # compute quartiles
#             n = len(vals)
#             q1 = vals[int(0.25 * (n - 1))]
#             q3 = vals[int(0.75 * (n - 1))]
#             iqr = q3 - q1
#             lower = q1 - iqr_k * iqr
#             upper = q3 + iqr_k * iqr
#             for idx, r in enumerate(records):
#                 fv = to_float_safe(r.get(k))
#                 if fv is None:
#                     continue
#                 if fv < lower or fv > upper:
#                     outliers.append({"index": idx, "column": k, "value": fv, "lower": lower, "upper": upper})
#         report["outliers"] = outliers

#         # simple imputation (median)
#         imputations = {}
#         cleaned = []
#         for k in (impute_fields or numeric_fields):
#             vals = sorted([to_float_safe(r.get(k)) for r in records if to_float_safe(r.get(k)) is not None])
#             if not vals:
#                 continue
#             fill = vals[len(vals) // 2]
#             cnt = 0
#             for r in records:
#                 if r.get(k) is None:
#                     r[k] = fill
#                     cnt += 1
#             imputations[k] = {"method": "median", "filled": cnt, "value": fill}
#         report["imputations"] = imputations

#         for r in records:
#             miss = sum(1 for k in all_keys if r.get(k) is None)
#             frac = miss / max(1, len(all_keys))
#             if frac > drop_on_missing_pct:
#                 report["removed_by_missing"] += 1
#                 continue
#             cleaned.append(r)
#         report["kept"] = len(cleaned)
#         return {"cleaned": cleaned, "report": report}

# src/smart_urban_resilience/tools/ValidationTool.py
import logging
import uuid
import hashlib
import statistics
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import datetime, timezone

# optional dependencies
try:
    import pandas as pd
    import numpy as np
except Exception:
    pd = None
    np = None

try:
    import jsonschema
    from jsonschema import Draft7Validator
except Exception:
    jsonschema = None
    Draft7Validator = None

LOG = logging.getLogger("ValidationTool")
logging.basicConfig(level=logging.INFO)


# ----------------------------- Input schema -----------------------------
class ValidationToolInput(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="List of normalized records to validate.")
    schema: Optional[Dict[str, Any]] = Field(None, description="Optional JSON Schema (applied AFTER ID recovery).")
    outlier_method: Optional[str] = Field("iqr", description="Outlier method: 'iqr' or 'zscore' (optional).")
    z_thresh: Optional[float] = Field(3.0, description="Z-score threshold for outliers.")
    iqr_k: Optional[float] = Field(1.5, description="IQR multiplier for outliers.")
    impute: Optional[str] = Field("median", description="Imputation: 'median' | 'mean' | 'none'.")
    impute_fields: Optional[List[str]] = Field(None, description="If provided, only impute these numeric fields.")
    drop_on_missing_pct: Optional[float] = Field(0.5, description="Drop record if fraction of missing fields > value.")
    dedupe_on: Optional[List[str]] = Field(None, description="Fields to consider for duplicate detection.")


# ----------------------------- Validation tool -----------------------------
class ValidationTool(BaseTool):
    name: str = "Data Validation Tool"
    description: str = (
        "Validates normalized records. Auto-fixes missing identifiers (deterministic inference or uuid), "
        "applies optional JSON Schema, detects duplicates, outliers (IQR/zscore), performs optional imputation, "
        "and emits a detailed data-quality report."
    )
    args_schema: Type[BaseModel] = ValidationToolInput

    # ----- helper: default schema applied after id recovery -----
    _DEFAULT_SCHEMA = {
        "type": "object",
        "properties": {
            "event_id": {"type": "string"},
            "id": {"type": "string"},
            "timestamp": {"type": "string"},
            "location": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                },
                "required": ["latitude", "longitude"],
            },
        },
        # event_id or id may be missing at ingest; we recover them before applying schema.
    }

    # ------------------------- main runner -------------------------
    def _run(
        self,
        records: List[Dict[str, Any]],
        schema: Optional[Dict[str, Any]] = None,
        outlier_method: Optional[str] = "iqr",
        z_thresh: Optional[float] = 3.0,
        iqr_k: Optional[float] = 1.5,
        impute: Optional[str] = "median",
        impute_fields: Optional[List[str]] = None,
        drop_on_missing_pct: Optional[float] = 0.5,
        dedupe_on: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate `records` and return {'cleaned': [...], 'report': {...}}"""
        # normalize incoming optional args (crew may pass None)
        outlier_method = (outlier_method or "iqr").lower()
        z_thresh = float(z_thresh or 3.0)
        iqr_k = float(iqr_k or 1.5)
        impute = (impute or "median").lower()
        drop_on_missing_pct = float(drop_on_missing_pct or 0.5)
        dedupe_on = dedupe_on or ["event_id", "id"]

        LOG.info(f"[ValidationTool] Start validation: records={len(records)}, outlier={outlier_method}, impute={impute}")

        # shallow copy of records to avoid mutating caller list
        recs = [dict(r) for r in records]

        # ---------- 0) ID recovery (deterministic inference or uuid) ----------
        auto_id_count = 0
        inferred_examples: List[Dict[str, Any]] = []
        for r in recs:
            id_src = None
            # prefer existing event_id or id if valid string
            if self._is_valid_id(r.get("event_id")):
                r["event_id"] = str(r["event_id"])
                id_src = "original"
            elif self._is_valid_id(r.get("id")):
                # if only id exists, promote to event_id (for canonicalization)
                r["event_id"] = str(r["id"])
                id_src = "original"
            else:
                # try deterministic inference using lat+lon+timestamp
                lat, lon = self._extract_latlon(r)
                ts = self._extract_timestamp_for_hash(r)
                if lat is not None and lon is not None and ts:
                    deduced = self._deterministic_id(lat, lon, ts)
                    r["event_id"] = deduced
                    id_src = "inferred"
                    inferred_examples.append({"event_id": deduced, "lat": lat, "lon": lon, "timestamp": ts})
                else:
                    # fallback to uuid4
                    generated = "evt-" + uuid.uuid4().hex[:12]
                    r["event_id"] = generated
                    id_src = "generated"
                auto_id_count += 1 if id_src in ("inferred", "generated") else 0
            # record id source for debugging/audit
            r.setdefault("_meta", {})["id_source"] = id_src

        LOG.info(f"[ValidationTool] Auto-generated/inferred IDs: {auto_id_count}")

        # ---------- 1) JSON Schema validation (after ID recovery) ----------
        validator_issues: List[Dict[str, Any]] = []
        effective_schema = schema or self._DEFAULT_SCHEMA
        if effective_schema and Draft7Validator:
            try:
                validator = Draft7Validator(effective_schema)
                for i, r in enumerate(recs):
                    errs = sorted(validator.iter_errors(r), key=lambda e: e.path)
                    if errs:
                        validator_issues.append({"index": i, "errors": [f"{'/'.join(map(str, e.path))}: {e.message}" for e in errs]})
            except Exception as e:
                LOG.warning("[ValidationTool] jsonschema validation failed to compile: %s", e)
        elif effective_schema and not Draft7Validator:
            LOG.warning("[ValidationTool] jsonschema not installed; skipping schema validation (but default schema exists).")

        # ---------- 2) Convert and clean values, branch by pandas availability ----------
        report = {
            "input_count": len(records),
            "auto_id_count": int(auto_id_count),
            "inferred_examples": inferred_examples[:5],
            "validator_issues": validator_issues,
            "missing_counts": {},
            "duplicate_examples": [],
            "outliers": [],
            "imputations": {},
            "removed_by_missing": 0,
            "kept": 0,
            "recommendations": [],
        }

        # Helper: normalize common 'null' string values to None
        def _normalize_null_strings(obj: Any) -> Any:
            if isinstance(obj, str):
                s = obj.strip().lower()
                if s in ("none", "null", "nan", ""):
                    return None
                return obj
            return obj

        # apply normalization to recs
        for r in recs:
            for k, v in list(r.items()):
                if isinstance(v, str):
                    r[k] = _normalize_null_strings(v)

        # ---- Pandas path (preferred) ----
        if pd:
            df = pd.DataFrame(recs)
            # normalize common string nulls across DataFrame
            df = df.replace({"None": pd.NA, "none": pd.NA, "null": pd.NA, "": pd.NA})

            # missing counts
            missing_counts = df.isna().sum().to_dict()
            report["missing_counts"] = {k: int(v) for k, v in missing_counts.items()}

            # drop rows with too many missing fields
            missing_frac = df.isna().mean(axis=1)
            drop_mask = missing_frac > drop_on_missing_pct
            report["removed_by_missing"] = int(drop_mask.sum())
            df_clean = df[~drop_mask].copy()

            # dedupe detection (before we drop duplicates)
            dedupe_cols = [c for c in dedupe_on if c in df_clean.columns]
            if dedupe_cols:
                dup_mask = df_clean.duplicated(subset=dedupe_cols, keep="first")
                dup_rows = df_clean[dup_mask]
                report["duplicate_examples"] = dup_rows[dedupe_cols].head(5).to_dict(orient="records") if not dup_rows.empty else []
            else:
                report["duplicate_examples"] = []

            # coerce potential numeric columns: try converting object dtypes and mark numeric_cols
            numeric_cols = list(df_clean.select_dtypes(include=[np.number]).columns) if np else []
            if np:
                for col in df_clean.columns:
                    if col in numeric_cols:
                        continue
                    coerced = pd.to_numeric(df_clean[col], errors="coerce")
                    # if at least one non-null after coercion, treat column as numeric
                    if coerced.notna().sum() >= 1:
                        df_clean[col] = coerced
                        numeric_cols.append(col)

            # Outlier detection
            outliers = []
            if numeric_cols:
                if outlier_method == "zscore" and np:
                    means = df_clean[numeric_cols].mean()
                    stds = df_clean[numeric_cols].std(ddof=0).replace(0, np.nan)
                    z = (df_clean[numeric_cols] - means) / stds
                    mask = z.abs() > z_thresh
                    for idx in mask.any(axis=1)[mask.any(axis=1)].index:
                        cols = list(mask.loc[idx][mask.loc[idx]].index)
                        outliers.append({"index": int(idx), "columns": cols})
                else:
                    # IQR method
                    for col in numeric_cols:
                        col_s = df_clean[col].dropna()
                        if col_s.empty:
                            continue
                        q1 = col_s.quantile(0.25)
                        q3 = col_s.quantile(0.75)
                        iqr = q3 - q1
                        lower = q1 - iqr_k * iqr
                        upper = q3 + iqr_k * iqr
                        mask = (df_clean[col] < lower) | (df_clean[col] > upper)
                        for idx in df_clean[mask].index.tolist():
                            outliers.append({
                                "index": int(idx),
                                "column": col,
                                "value": float(df_clean.at[idx, col]),
                                "lower": float(lower),
                                "upper": float(upper),
                            })
            report["outliers"] = outliers

            # Imputation (numeric)
            imputations = {}
            if impute and impute != "none" and numeric_cols:
                fields = impute_fields or numeric_cols
                for c in fields:
                    if c not in df_clean.columns:
                        continue
                    df_clean[c] = pd.to_numeric(df_clean[c], errors="coerce")
                    if impute == "median":
                        try:
                            fill = float(df_clean[c].median(skipna=True))
                        except Exception:
                            continue
                    elif impute == "mean":
                        try:
                            fill = float(df_clean[c].mean(skipna=True))
                        except Exception:
                            continue
                    else:
                        continue
                    n_before = int(df_clean[c].isna().sum())
                    df_clean[c].fillna(fill, inplace=True)
                    n_after = int(df_clean[c].isna().sum())
                    imputations[c] = {"method": impute, "filled": int(n_before - n_after), "value": fill}
            report["imputations"] = imputations

            # final dedupe (drop duplicates keeping first)
            if dedupe_cols:
                df_final = df_clean.drop_duplicates(subset=dedupe_cols, keep="first")
            else:
                df_final = df_clean

            # ensure python-native types
            def _to_native(v):
                if np:
                    if isinstance(v, (np.integer, np.int32, np.int64)):
                        return int(v)
                    if isinstance(v, (np.floating, np.float32, np.float64)):
                        return float(v)
                    if isinstance(v, np.bool_):
                        return bool(v)
                return v

            cleaned = df_final.reset_index(drop=True).to_dict(orient="records")
            cleaned_native = [{k: _to_native(v) for k, v in rec.items()} for rec in cleaned]

            report["kept"] = len(cleaned_native)
            report["recommendations"].append("Add sensor registration metadata when possible to reduce inference reliance.")
            return {"cleaned": cleaned_native, "report": report}

        # ---- fallback path without pandas ----
        LOG.warning("[ValidationTool] pandas not available, using pure-Python fallback (slower).")

        # normalize numeric-like strings to floats or None
        def to_float_safe(x: Any) -> Optional[float]:
            if x is None:
                return None
            if isinstance(x, str):
                s = x.strip().lower()
                if s in ("", "none", "null", "nan"):
                    return None
            try:
                return float(x)
            except Exception:
                return None

        all_keys = set().union(*(r.keys() for r in recs)) if recs else set()
        missing_counts = {k: 0 for k in all_keys}
        for r in recs:
            for k in all_keys:
                if r.get(k) is None:
                    missing_counts[k] += 1
        report["missing_counts"] = missing_counts

        # numeric fields detection
        numeric_fields = []
        for k in all_keys:
            vals = [to_float_safe(r.get(k)) for r in recs]
            vals = [v for v in vals if v is not None]
            if len(vals) >= 3:
                numeric_fields.append(k)

        # outliers (IQR fallback)
        outliers = []
        for k in numeric_fields:
            vals = sorted([to_float_safe(r.get(k)) for r in recs if to_float_safe(r.get(k)) is not None])
            if len(vals) < 3:
                continue
            n = len(vals)
            q1 = vals[int(0.25 * (n - 1))]
            q3 = vals[int(0.75 * (n - 1))]
            iqr = q3 - q1
            lower = q1 - iqr_k * iqr
            upper = q3 + iqr_k * iqr
            for idx, r in enumerate(recs):
                v = to_float_safe(r.get(k))
                if v is None:
                    continue
                if v < lower or v > upper:
                    outliers.append({"index": idx, "column": k, "value": v, "lower": lower, "upper": upper})
        report["outliers"] = outliers

        # impute (median)
        imputations = {}
        for k in (impute_fields or numeric_fields):
            vals = sorted([to_float_safe(r.get(k)) for r in recs if to_float_safe(r.get(k)) is not None])
            if not vals:
                continue
            fill = vals[len(vals) // 2]
            cnt = 0
            for r in recs:
                if r.get(k) is None:
                    r[k] = fill
                    cnt += 1
            imputations[k] = {"method": "median", "filled": cnt, "value": fill}
        report["imputations"] = imputations

        # drop by missing fraction
        cleaned = []
        for r in recs:
            miss = sum(1 for k in all_keys if r.get(k) is None)
            frac = miss / max(1, len(all_keys))
            if frac > drop_on_missing_pct:
                report["removed_by_missing"] += 1
                continue
            cleaned.append(r)

        report["kept"] = len(cleaned)
        report["recommendations"].append("Install pandas for faster & richer validation pipelines.")
        return {"cleaned": cleaned, "report": report}

    # ------------------------- helper utils -------------------------
    @staticmethod
    def _is_valid_id(val: Any) -> bool:
        if val is None:
            return False
        if isinstance(val, str) and val.strip() == "":
            return False
        return True

    @staticmethod
    def _extract_latlon(rec: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """Return (lat, lon) or (None, None) — try common fields and nested location.*"""
        candidates = [
            ("latitude", "longitude"),
            ("lat", "lon"),
            ("lat", "lng"),
            ("location.latitude", "location.longitude"),
            ("location.lat", "location.lon"),
        ]
        def lookup(path: str):
            parts = path.split(".")
            cur = rec
            for p in parts:
                if isinstance(cur, dict) and p in cur:
                    cur = cur[p]
                else:
                    return None
            return cur
        for latk, lonk in candidates:
            latv = lookup(latk)
            lonv = lookup(lonk)
            try:
                latf = float(latv) if latv is not None else None
                lonf = float(lonv) if lonv is not None else None
                if latf is not None and lonf is not None:
                    return latf, lonf
            except Exception:
                continue
        return None, None

    @staticmethod
    def _extract_timestamp_for_hash(rec: Dict[str, Any]) -> Optional[str]:
        ts = rec.get("timestamp") or rec.get("time") or rec.get("ingest_timestamp")
        if isinstance(ts, (int, float)):
            try:
                return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
            except Exception:
                return None
        if isinstance(ts, str):
            return ts
        return None

    @staticmethod
    def _deterministic_id(lat: float, lon: float, ts_iso: str) -> str:
        payload = f"{lat:.6f}:{lon:.6f}:{ts_iso}"
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return "inf-" + h[:12]


# ----------------------------- end of tool -----------------------------
