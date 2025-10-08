# tools/ValidationTool.py
import logging
import json
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# optional libs
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


class ValidationToolInput(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="List of normalized records to validate.")
    schema: Optional[Dict[str, Any]] = Field(None, description="Optional JSON Schema to validate records against.")
    outlier_method: str = Field("iqr", description="Outlier detection method: 'iqr' or 'zscore'.")
    z_thresh: float = Field(3.0, description="Z-score threshold (used when outlier_method == 'zscore').")
    iqr_k: float = Field(1.5, description="IQR multiplier (used when outlier_method == 'iqr').")
    impute: str = Field("median", description="Imputation: 'median' | 'mean' | 'none'.")
    impute_fields: Optional[List[str]] = Field(None, description="If provided, only impute these fields.")
    drop_on_missing_pct: float = Field(0.5, description="Drop record if fraction of missing fields > this value (0-1).")
    dedupe_on: Optional[List[str]] = Field(["event_id"], description="Fields to consider for duplicate detection.")


class ValidationTool(BaseTool):
    name: str = "Data Validation Tool"
    description: str = (
        "Validates normalized records: optional JSON Schema validation, missing-checks, duplicate detection, "
        "outlier detection (IQR or Z-score), optional imputation (median/mean). Returns cleaned records + report."
    )
    args_schema: Type[BaseModel] = ValidationToolInput

    def _run(
        self,
        records: List[Dict[str, Any]],
        schema: Optional[Dict[str, Any]] = None,
        outlier_method: str = "iqr",
        z_thresh: float = 3.0,
        iqr_k: float = 1.5,
        impute: str = "median",
        impute_fields: Optional[List[str]] = None,
        drop_on_missing_pct: float = 0.5,
        dedupe_on: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        LOG.info(f"[ValidationTool] Running validation on {len(records)} records")
        report = {
            "input_count": len(records),
            "schema_validations": [],
            "duplicate_ids": [],
            "missing_counts": {},
            "outliers": [],
            "imputations": {},
            "removed_by_missing": 0,
            "kept": 0,
        }

        # 1) JSON Schema validation (optional)
        schema_issues = []
        if schema and Draft7Validator:
            validator = Draft7Validator(schema)
            for i, rec in enumerate(records):
                errs = sorted(validator.iter_errors(rec), key=lambda e: e.path)
                if errs:
                    schema_issues.append({"index": i, "errors": [f"{'/'.join(map(str,e.path))}: {e.message}" for e in errs]})
        elif schema and not Draft7Validator:
            LOG.warning("[ValidationTool] jsonschema not installed; skipping schema validation.")
        report["schema_validations"] = schema_issues

        # 2) Work with pandas if available (preferred)
        if pd:
            df = pd.DataFrame(records)
            # duplicates
            dedupe_on = dedupe_on or ["event_id"]
            dup_mask = df.duplicated(subset=[c for c in dedupe_on if c in df.columns], keep="first")
            dup_indices = df[dup_mask].index.tolist()
            report["duplicate_ids"] = df.loc[dup_indices, dedupe_on].to_dict(orient="records") if dup_indices else []

            # missing counts per column
            missing_counts = df.isna().sum().to_dict()
            report["missing_counts"] = {k: int(v) for k, v in missing_counts.items()}

            # drop by missing threshold
            missing_frac = df.isna().mean(axis=1)
            drop_mask = missing_frac > float(drop_on_missing_pct)
            report["removed_by_missing"] = int(drop_mask.sum())
            df_clean = df[~drop_mask].copy()

            # outlier detection for numeric cols
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist() if np else []
            outliers = []
            if numeric_cols:
                if outlier_method == "zscore" and np:
                    means = df_clean[numeric_cols].mean()
                    stds = df_clean[numeric_cols].std(ddof=0).replace(0, np.nan)
                    z = (df_clean[numeric_cols] - means) / stds
                    mask = (z.abs() > float(z_thresh))
                    for idx, row in mask.iterrows():
                        cols = row[row].index.tolist()
                        if cols:
                            outliers.append({"index": int(idx), "columns": cols})
                else:  # iqr
                    for col in numeric_cols:
                        q1 = df_clean[col].quantile(0.25)
                        q3 = df_clean[col].quantile(0.75)
                        iqr = q3 - q1
                        lower = q1 - float(iqr_k) * iqr
                        upper = q3 + float(iqr_k) * iqr
                        mask = (df_clean[col] < lower) | (df_clean[col] > upper)
                        for idx in df_clean[mask].index.tolist():
                            outliers.append({"index": int(idx), "column": col, "value": float(df_clean.at[idx, col]), "lower": float(lower), "upper": float(upper)})
            report["outliers"] = outliers

            # imputation
            imputations = {}
            if impute and impute.lower() != "none" and numeric_cols:
                fields = impute_fields or numeric_cols
                for c in fields:
                    if c not in df_clean.columns:
                        continue
                    if impute.lower() == "median":
                        fill = float(df_clean[c].median(skipna=True))
                    elif impute.lower() == "mean":
                        fill = float(df_clean[c].mean(skipna=True))
                    else:
                        continue
                    n_before = int(df_clean[c].isna().sum())
                    df_clean[c].fillna(fill, inplace=True)
                    n_after = int(df_clean[c].isna().sum())
                    imputations[c] = {"method": impute, "filled": int(n_before - n_after), "value": fill}
                report["imputations"] = imputations

            # remove duplicate rows if any
            df_final = df_clean.drop_duplicates(subset=[c for c in dedupe_on if c in df_clean.columns], keep="first")

            # finalize cleaned records
            cleaned = df_final.reset_index(drop=True).to_dict(orient="records")
            # Ensure types are Python native
            def _to_native(obj):
                if isinstance(obj, (np.integer, np.int32, np.int64)):
                    return int(obj)
                if isinstance(obj, (np.floating, np.float32, np.float64)):
                    return float(obj)
                if isinstance(obj, np.bool_):
                    return bool(obj)
                return obj

            cleaned = [{k: _to_native(v) for k, v in rec.items()} for rec in cleaned]
            report["kept"] = len(cleaned)

            return {"cleaned": cleaned, "report": report}

        # 3) Fallback (no pandas): pure Python validation
        LOG.warning("[ValidationTool] pandas not available — using fallback validator (slower).")
        issues = []
        # compute missing per field & numeric detection
        all_keys = set().union(*(r.keys() for r in records)) if records else set()
        missing_counts = {k: 0 for k in all_keys}
        for r in records:
            for k in all_keys:
                if r.get(k) is None:
                    missing_counts[k] += 1
        report["missing_counts"] = missing_counts

        # simple numeric detection and outlier via IQR implemented per-field
        numeric_fields = []
        for k in all_keys:
            vals = []
            for r in records:
                v = r.get(k)
                try:
                    f = float(v)
                    vals.append(f)
                except Exception:
                    pass
            if len(vals) >= 3:
                numeric_fields.append(k)

        outliers = []
        for k in numeric_fields:
            vals = sorted([float(r[k]) for r in records if k in r and r[k] is not None])
            q1 = vals[len(vals) // 4]
            q3 = vals[(len(vals) * 3) // 4]
            iqr = q3 - q1
            lower = q1 - iqr_k * iqr
            upper = q3 + iqr_k * iqr
            for idx, r in enumerate(records):
                try:
                    v = float(r.get(k))
                    if v < lower or v > upper:
                        outliers.append({"index": idx, "column": k, "value": v, "lower": lower, "upper": upper})
                except Exception:
                    continue
        report["outliers"] = outliers

        # simple imputation (median)
        cleaned = []
        imputations = {}
        for k in (impute_fields or numeric_fields):
            vals = [float(r[k]) for r in records if k in r and r[k] is not None]
            if not vals:
                continue
            fill = float(sorted(vals)[len(vals) // 2])
            cnt = 0
            for r in records:
                if r.get(k) is None:
                    r[k] = fill
                    cnt += 1
            imputations[k] = {"method": "median", "filled": cnt, "value": fill}
        report["imputations"] = imputations

        # drop by missing
        for r in records:
            miss = sum(1 for k in all_keys if r.get(k) is None)
            frac = miss / max(1, len(all_keys))
            if frac > drop_on_missing_pct:
                report["removed_by_missing"] += 1
                continue
            cleaned.append(r)
        report["kept"] = len(cleaned)
        return {"cleaned": cleaned, "report": report}
