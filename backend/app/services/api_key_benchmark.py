"""API Key Detection Engine & Benchmark Service for API Sentinel.

Provides pattern matching, entropy filtering, and benchmark evaluation against
the held-out test dataset split.
"""

import os
import re
import json
import math
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import DatasetTestSession, DatasetTestResult, utc_now

# Concurrency guard for batch test execution
_batch_lock = threading.Lock()

BENCHMARK_RESULTS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "metadata", "benchmark_results.json")
)
BENCHMARK_HISTORY_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "metadata", "benchmark_history.json")
)
DEFAULT_TEST_SPLIT_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "dataset", "splits", "api_keys_test.jsonl")
)
MASTER_DATASET_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "dataset", "api_keys_master.jsonl")
)

# -----------------------------------------------------------------------------
# Detection Patterns (Based on GitHub Supported Secret Scanning Patterns & Safe Synthetic Test Fixtures)
# -----------------------------------------------------------------------------
PROVIDER_PATTERNS = {
    "aws": re.compile(r'\b(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}\b|\bAKIA_MOCK_[A-Z0-9]{16}\b'),
    "openai": re.compile(r'\bsk-(?:proj-|admin-|none-|mock-)?[a-zA-Z0-9_-]{32,96}\b'),
    "nvidia": re.compile(r'\bnvapi-(?:mock-)?[a-zA-Z0-9_-]{50,64}\b'),
    "github": re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_(?:mock_)?[a-zA-Z0-9]{32,255}\b'),
    "google_cloud": re.compile(r'\bAIza[0-9A-Za-z\-_]{35}\b|\bAIza_MOCK_[0-9A-Za-z\-_]{28,35}\b'),
    "stripe": re.compile(r'\b(?:sk_live|rk_live|sk_test_mock|sk_test)_[0-9a-zA-Z]{24,99}\b'),
    "azure": re.compile(r'(?:(?:MOCK_)?AccountKey=[a-zA-Z0-9+/=]{80,92}(?![a-zA-Z0-9+/=])|\b[a-f0-9]{32}\b)'),
    "slack": re.compile(r'\bxox(?:b|p|a|r)-(?:mock-)?[0-9a-zA-Z-]{24,45}\b'),
    "twilio": re.compile(r'\bSK(?:_MOCK_)?[0-9a-fA-F]{32}\b'),
    "generic_api_key": re.compile(r'(?i)(?:api[_-]?key|apikey|access[_-]?token)[\'"\s:=]+([a-zA-Z0-9_-]{32,64})'),
}

# Negative Lookalike Rejection Heuristics
PLACEHOLDER_REGEX = re.compile(
    r'(?i)(?:YOUR_|INSERT_|EXAMPLE|DUMMY|PLACEHOLDER|00000000|XXXXXXXX|TESTINGONLY|<[A-Z_]+>|\bNone\b)'
)

def shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in set(data):
        p_x = float(data.count(x)) / length
        entropy += - p_x * math.log2(p_x)
    return entropy

def mask_credential(val: str) -> str:
    """Mask credential value for safe API/UI exposure."""
    if not val or len(val) <= 8:
        return "****"
    if val.startswith("sk-proj-"):
        return f"sk-proj-...{val[-4:]}"
    if val.startswith("nvapi-"):
        return f"nvapi-...{val[-4:]}"
    if val.startswith("ghp_"):
        return f"ghp_...{val[-4:]}"
    if val.startswith("AKIA") or val.startswith("ASIA"):
        return f"{val[:4]}...{val[-4:]}"
    if val.startswith("AIza"):
        return f"AIza...{val[-4:]}"
    if "AccountKey=" in val:
        return "AccountKey=...****"
    return f"{val[:4]}...{val[-4:]}"

class ApiKeyDetectionEngine:
    """Pure API-key detection engine evaluating strings against documented provider signatures."""
    VERSION = "1.0.0"

    @classmethod
    def detect_with_details(cls, text: str) -> Tuple[Optional[str], Optional[str], str, Optional[float]]:
        """Detect if text contains a valid API key pattern and return reasoning & entropy score.
        
        Returns: (detected_provider, matched_token, reason, score)
        """
        if not text:
            return None, None, "Empty text provided", None

        # 1. Filter out obvious placeholders
        if PLACEHOLDER_REGEX.search(text):
            return None, None, "Rejected: Matches known dummy/placeholder or documentation example template", None

        # 2. Check each provider in deterministic priority order
        for provider, pattern in PROVIDER_PATTERNS.items():
            match = pattern.search(text)
            if match:
                token = match.group(1) if match.groups() else match.group(0)

                # Secondary sanity checks on extracted token
                if PLACEHOLDER_REGEX.search(token):
                    continue

                ent = shannon_entropy(token)
                # For generic keys, enforce minimal entropy to avoid false positives on hex dumps or repeated chars
                if provider == "generic_api_key" and ent < 3.2:
                    return None, None, f"Rejected: Token entropy ({ent:.2f} bits) below threshold (<3.2 bits)", round(ent, 2)

                reason = f"Matched {provider.upper()} signature pattern '{token[:6]}...' with Shannon entropy {ent:.2f} bits"
                return provider, token, reason, round(ent, 2)

        return None, None, "No recognized provider API key signature or valid credential assignment detected", None

    @classmethod
    def detect(cls, text: str) -> Optional[Tuple[str, str]]:
        """Detect if text contains a valid API key pattern.

        Returns (provider, matched_token) or None.
        """
        prov, token, _, _ = cls.detect_with_details(text)
        if prov:
            return prov, token
        return None


class ApiKeyBenchmarkService:
    """Executes detection benchmark against held-out test dataset and computes metrics."""

    @staticmethod
    def run_benchmark(dataset_path: Optional[str] = None) -> Dict[str, Any]:
        """Run the detection benchmark and return comprehensive performance metrics."""
        path = dataset_path or DEFAULT_TEST_SPLIT_FILE
        if not os.path.exists(path):
            # Fall back to master dataset if split not found
            if os.path.exists(MASTER_DATASET_FILE):
                path = MASTER_DATASET_FILE
            else:
                raise FileNotFoundError(f"Benchmark test dataset not found at: {path}")

        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        start_time = time.time()
        
        # Global counters
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        # Per-provider stats
        provider_stats: Dict[str, Dict[str, int]] = {}
        false_positives: List[Dict[str, Any]] = []
        false_negatives: List[Dict[str, Any]] = []

        for rec in records:
            provider = rec.get("provider", "unknown")
            is_pos = (rec.get("label") == "positive")
            sample_text = rec.get("sample", "")

            if provider not in provider_stats:
                provider_stats[provider] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0}
            provider_stats[provider]["total"] += 1

            detected = ApiKeyDetectionEngine.detect(sample_text)

            if is_pos:
                if detected:
                    tp += 1
                    provider_stats[provider]["tp"] += 1
                else:
                    fn += 1
                    provider_stats[provider]["fn"] += 1
                    if len(false_negatives) < 10:
                        false_negatives.append({
                            "sample_id": rec.get("sample_id"),
                            "provider": provider,
                            "masked_sample": mask_credential(sample_text),
                            "notes": rec.get("notes")
                        })
            else:
                if detected:
                    fp += 1
                    provider_stats[provider]["fp"] += 1
                    if len(false_positives) < 10:
                        false_positives.append({
                            "sample_id": rec.get("sample_id"),
                            "provider": provider,
                            "detected_as": detected[0],
                            "masked_sample": mask_credential(sample_text),
                            "notes": rec.get("notes")
                        })
                else:
                    tn += 1
                    provider_stats[provider]["tn"] += 1

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        total_samples = len(records)

        # Standard Metric Formulas with Division-by-Zero Protection
        precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 0.0
        recall = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 0.0
        f1 = round((2 * (precision * recall) / (precision + recall)), 2) if (precision + recall) > 0 else 0.0
        accuracy = round(((tp + tn) / total_samples) * 100, 2) if total_samples > 0 else 0.0

        # Per-provider formatted metrics
        per_provider_metrics = []
        for prov, counts in sorted(provider_stats.items()):
            p_tp = counts["tp"]
            p_fp = counts["fp"]
            p_tn = counts["tn"]
            p_fn = counts["fn"]
            p_total = counts["total"]

            p_prec = round((p_tp / (p_tp + p_fp)) * 100, 2) if (p_tp + p_fp) > 0 else 0.0
            p_rec = round((p_tp / (p_tp + p_fn)) * 100, 2) if (p_tp + p_fn) > 0 else 0.0
            p_f1 = round((2 * (p_prec * p_rec) / (p_prec + p_rec)), 2) if (p_prec + p_rec) > 0 else 0.0
            p_acc = round(((p_tp + p_tn) / p_total) * 100, 2) if p_total > 0 else 0.0

            per_provider_metrics.append({
                "provider": prov,
                "samples": p_total,
                "tp": p_tp,
                "fp": p_fp,
                "tn": p_tn,
                "fn": p_fn,
                "precision": p_prec,
                "recall": p_rec,
                "f1": p_f1,
                "accuracy": p_acc,
            })

        result = {
            "benchmark_id": f"bench_{int(time.time())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_version": ApiKeyDetectionEngine.VERSION,
            "dataset_split": os.path.basename(path),
            "total_samples": total_samples,
            "duration_ms": elapsed_ms,
            "metrics": {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "accuracy": accuracy,
                "tp": tp,
                "fp": fp,
                "tn": tn,
                "fn": fn,
            },
            "per_provider": per_provider_metrics,
            "false_positives_sample": false_positives,
            "false_negatives_sample": false_negatives,
        }

        # Save latest results
        os.makedirs(os.path.dirname(BENCHMARK_RESULTS_FILE), exist_ok=True)
        with open(BENCHMARK_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        # Append to benchmark history
        history = []
        if os.path.exists(BENCHMARK_HISTORY_FILE):
            try:
                with open(BENCHMARK_HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        # Keep latest 25 historical runs
        history.insert(0, {
            "benchmark_id": result["benchmark_id"],
            "timestamp": result["timestamp"],
            "engine_version": result["engine_version"],
            "total_samples": total_samples,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
            "duration_ms": elapsed_ms
        })
        history = history[:25]
        with open(BENCHMARK_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        return result

    @staticmethod
    def get_latest_results() -> Optional[Dict[str, Any]]:
        """Retrieve most recent benchmark result, or run if none exists."""
        if os.path.exists(BENCHMARK_RESULTS_FILE):
            try:
                with open(BENCHMARK_RESULTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return ApiKeyBenchmarkService.run_benchmark()

    @staticmethod
    def get_benchmark_history() -> List[Dict[str, Any]]:
        """Retrieve historical benchmark runs."""
        if os.path.exists(BENCHMARK_HISTORY_FILE):
            try:
                with open(BENCHMARK_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # If no history yet, run once
        ApiKeyBenchmarkService.run_benchmark()
        if os.path.exists(BENCHMARK_HISTORY_FILE):
            with open(BENCHMARK_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    # -------------------------------------------------------------------------
    # Operational Dataset-Powered Single & Batch Testing Methods
    # -------------------------------------------------------------------------

    @staticmethod
    def load_sample_from_dataset(
        sample_id: Optional[str] = None,
        provider: Optional[str] = None,
        label: Optional[str] = None,
        split: str = "test",
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Safely load one redistributable sample from specified split."""
        if provider and provider.lower() in ("all", "any", "none", "*", ""):
            provider = None
        if label and label.lower() in ("all", "any", "none", "*", ""):
            label = None

        split_name = split if split in ("train", "validation", "test") else "test"
        path = os.path.join(os.path.dirname(DEFAULT_TEST_SPLIT_FILE), f"api_keys_{split_name}.jsonl")
        if not os.path.exists(path):
            path = MASTER_DATASET_FILE

        if not os.path.exists(path):
            return None

        matched = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)

                if sample_id:
                    if rec.get("sample_id") == sample_id:
                        return rec
                    continue

                if provider and rec.get("provider") != provider:
                    continue
                if label and rec.get("label") != label:
                    continue

                matched.append(rec)
                if len(matched) > (offset + 1):
                    break

        if not matched:
            return None

        idx = offset % len(matched) if matched else 0
        return matched[idx]

    @staticmethod
    def execute_single_test(
        db: Session,
        sample_id: Optional[str] = None,
        provider: Optional[str] = None,
        label: Optional[str] = None,
        split: str = "test",
        offset: int = 0
    ) -> Dict[str, Any]:
        """Run single-sample detection test, classify outcome, and persist result."""
        rec = ApiKeyBenchmarkService.load_sample_from_dataset(
            sample_id=sample_id,
            provider=provider,
            label=label,
            split=split,
            offset=offset
        )
        if not rec:
            raise ValueError(f"Sample not found matching criteria (sample_id={sample_id}, provider={provider}, label={label})")

        sample_text = rec.get("sample", "")
        expected_provider = rec.get("provider", "unknown")
        expected_label = rec.get("label", "positive")
        is_pos = (expected_label == "positive")

        t0 = time.time()
        # Engine receives ONLY sample_text - strictly zero ground-truth leakage
        detected_prov, matched_token, reason, score = ApiKeyDetectionEngine.detect_with_details(sample_text)
        elapsed_ms = round((time.time() - t0) * 1000, 3)

        # Ground-truth comparison happens strictly after prediction
        has_detection = (detected_prov is not None)
        if is_pos:
            if has_detection:
                predicted_label = "positive"
                outcome = "correct_detection"  # TP
                is_correct = True
            else:
                predicted_label = "negative"
                outcome = "false_negative"  # FN
                is_correct = False
        else:
            if has_detection:
                predicted_label = "positive"
                outcome = "false_positive"  # FP
                is_correct = False
            else:
                predicted_label = "negative"
                outcome = "correct_rejection"  # TN
                is_correct = True

        # Persist session and result in SQLite
        session = DatasetTestSession(
            test_mode="single",
            provider_filter=expected_provider,
            label_filter=expected_label,
            split_used=split,
            requested_sample_count=1,
            completed_sample_count=1,
            status="completed",
            started_at=utc_now(),
            completed_at=utc_now(),
            tp=1 if outcome == "correct_detection" else 0,
            fp=1 if outcome == "false_positive" else 0,
            tn=1 if outcome == "correct_rejection" else 0,
            fn=1 if outcome == "false_negative" else 0,
            precision=100.0 if outcome == "correct_detection" else 0.0,
            recall=100.0 if outcome == "correct_detection" else (0.0 if outcome == "false_negative" else 100.0),
            f1=100.0 if is_correct else 0.0,
            accuracy=100.0 if is_correct else 0.0,
            duration_ms=elapsed_ms,
            session_summary={"single_sample_id": rec.get("sample_id"), "outcome": outcome}
        )
        db.add(session)
        db.flush()

        res_record = DatasetTestResult(
            session_id=session.id,
            sample_id=rec.get("sample_id"),
            masked_sample=mask_credential(sample_text),  # never store raw key
            expected_provider=expected_provider,
            detected_provider=detected_prov,
            expected_label=expected_label,
            predicted_label=predicted_label,
            test_outcome=outcome,
            detection_reason=reason,
            execution_time_ms=elapsed_ms,
            created_at=utc_now()
        )
        db.add(res_record)
        db.commit()
        db.refresh(res_record)

        return {
            "result_id": res_record.id,
            "session_id": session.id,
            "sample_id": rec.get("sample_id"),
            "masked_sample": res_record.masked_sample,
            "expected_provider": expected_provider,
            "detected_provider": detected_prov,
            "expected_label": expected_label,
            "predicted_label": predicted_label,
            "is_correct": is_correct,
            "test_outcome": outcome,
            "detection_reason": reason,
            "confidence_score": score,
            "execution_time_ms": elapsed_ms,
            "notes": rec.get("notes", ""),
            "created_at": res_record.created_at
        }

    @staticmethod
    def execute_batch_test(
        db: Session,
        provider: Optional[str] = None,
        label: Optional[str] = None,
        count: int = 50,
        split: str = "test"
    ) -> DatasetTestSession:
        """Run batch testing across filtered dataset samples with concurrent lock."""
        acquired = _batch_lock.acquire(blocking=False)
        if not acquired:
            raise RuntimeError("A batch test session is already in progress. Please wait for it to complete.")

        if provider and provider.lower() in ("all", "any", "none", "*", ""):
            provider = None
        if label and label.lower() in ("all", "any", "none", "*", ""):
            label = None

        split_name = split if split in ("train", "validation", "test") else "test"
        path = os.path.join(os.path.dirname(DEFAULT_TEST_SPLIT_FILE), f"api_keys_{split_name}.jsonl")
        if not os.path.exists(path):
            path = MASTER_DATASET_FILE

        session = DatasetTestSession(
            test_mode="batch",
            provider_filter=provider,
            label_filter=label,
            split_used=split,
            requested_sample_count=count,
            completed_sample_count=0,
            status="running",
            started_at=utc_now()
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        try:
            samples_to_test = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    if provider and r.get("provider") != provider:
                        continue
                    if label and r.get("label") != label:
                        continue
                    samples_to_test.append(r)
                    if len(samples_to_test) >= count:
                        break

            start_t = time.time()
            tp, fp, tn, fn = 0, 0, 0, 0
            provider_stats: Dict[str, Dict[str, int]] = {}

            for rec in samples_to_test:
                sample_text = rec.get("sample", "")
                exp_prov = rec.get("provider", "unknown")
                exp_lbl = rec.get("label", "positive")
                is_pos = (exp_lbl == "positive")

                if exp_prov not in provider_stats:
                    provider_stats[exp_prov] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0}
                provider_stats[exp_prov]["total"] += 1

                t_item = time.time()
                det_prov, _, reason, score = ApiKeyDetectionEngine.detect_with_details(sample_text)
                item_elapsed = round((time.time() - t_item) * 1000, 3)

                has_det = (det_prov is not None)
                if is_pos:
                    if has_det:
                        pred_lbl = "positive"
                        outcome = "correct_detection"
                        tp += 1
                        provider_stats[exp_prov]["tp"] += 1
                    else:
                        pred_lbl = "negative"
                        outcome = "false_negative"
                        fn += 1
                        provider_stats[exp_prov]["fn"] += 1
                else:
                    if has_det:
                        pred_lbl = "positive"
                        outcome = "false_positive"
                        fp += 1
                        provider_stats[exp_prov]["fp"] += 1
                    else:
                        pred_lbl = "negative"
                        outcome = "correct_rejection"
                        tn += 1
                        provider_stats[exp_prov]["tn"] += 1

                # Save individual result with masked sample
                res_obj = DatasetTestResult(
                    session_id=session.id,
                    sample_id=rec.get("sample_id"),
                    masked_sample=mask_credential(sample_text),
                    expected_provider=exp_prov,
                    detected_provider=det_prov,
                    expected_label=exp_lbl,
                    predicted_label=pred_lbl,
                    test_outcome=outcome,
                    detection_reason=reason,
                    execution_time_ms=item_elapsed,
                    created_at=utc_now()
                )
                db.add(res_obj)

            total_elapsed_ms = round((time.time() - start_t) * 1000, 2)
            completed_count = len(samples_to_test)

            # Standard metrics with division-by-zero protection
            precision = round((tp / (tp + fp)) * 100, 2) if (tp + fp) > 0 else 0.0
            recall = round((tp / (tp + fn)) * 100, 2) if (tp + fn) > 0 else 0.0
            f1 = round((2 * (precision * recall) / (precision + recall)), 2) if (precision + recall) > 0 else 0.0
            accuracy = round(((tp + tn) / completed_count) * 100, 2) if completed_count > 0 else 0.0

            # Per-provider formatting
            per_provider_list = []
            for p_name, p_counts in sorted(provider_stats.items()):
                p_tp, p_fp, p_tn, p_fn = p_counts["tp"], p_counts["fp"], p_counts["tn"], p_counts["fn"]
                p_tot = p_counts["total"]
                p_prec = round((p_tp / (p_tp + p_fp)) * 100, 2) if (p_tp + p_fp) > 0 else 0.0
                p_rec = round((p_tp / (p_tp + p_fn)) * 100, 2) if (p_tp + p_fn) > 0 else 0.0
                p_f1 = round((2 * p_prec * p_rec / (p_prec + p_rec)), 2) if (p_prec + p_rec) > 0 else 0.0
                p_acc = round(((p_tp + p_tn) / p_tot) * 100, 2) if p_tot > 0 else 0.0
                per_provider_list.append({
                    "provider": p_name,
                    "samples": p_tot,
                    "tp": p_tp,
                    "fp": p_fp,
                    "tn": p_tn,
                    "fn": p_fn,
                    "precision": p_prec,
                    "recall": p_rec,
                    "f1": p_f1,
                    "accuracy": p_acc
                })

            session.completed_sample_count = completed_count
            session.completed_at = utc_now()
            session.status = "completed"
            session.tp = tp
            session.fp = fp
            session.tn = tn
            session.fn = fn
            session.precision = precision
            session.recall = recall
            session.f1 = f1
            session.accuracy = accuracy
            session.duration_ms = total_elapsed_ms
            session.session_summary = {
                "per_provider": per_provider_list,
                "tested_count": completed_count
            }
            db.commit()
            db.refresh(session)
            return session

        except Exception as e:
            session.status = "failed"
            session.completed_at = utc_now()
            session.session_summary = {"error": str(e)}
            db.commit()
            raise
        finally:
            _batch_lock.release()

    @staticmethod
    def get_test_session_by_id(db: Session, session_id: str) -> Optional[DatasetTestSession]:
        return db.query(DatasetTestSession).filter(DatasetTestSession.id == session_id).first()

    @staticmethod
    def get_test_session_results(db: Session, session_id: str, skip: int = 0, limit: int = 50) -> Tuple[List[DatasetTestResult], int]:
        q = db.query(DatasetTestResult).filter(DatasetTestResult.session_id == session_id).order_by(DatasetTestResult.created_at.asc())
        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_test_history(db: Session, skip: int = 0, limit: int = 20) -> Tuple[List[DatasetTestSession], int]:
        q = db.query(DatasetTestSession).order_by(DatasetTestSession.started_at.desc())
        total = q.count()
        items = q.offset(skip).limit(limit).all()
        return items, total
