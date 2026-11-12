"""Analytics Service: Aggregates persistent security telemetry across all historical scans."""

import hashlib
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session, joinedload
from app.models import Scan, Finding, ScanRecord, FindingRecord

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Computes all-time deduplicated security analytics from persisted database records."""

    @staticmethod
    def normalize_severity(severity_raw: str) -> str:
        """Normalize severity strings into standard buckets: critical, high, medium, low, informational."""
        s = (severity_raw or "").strip().lower()
        if "crit" in s:
            return "critical"
        if "high" in s:
            return "high"
        if "med" in s:
            return "medium"
        if "info" in s:
            return "informational"
        if "low" in s:
            return "low"
        return "low"

    @staticmethod
    def is_status_resolved(status_raw: str) -> bool:
        """Determine if a finding status represents verified resolution."""
        s = (status_raw or "").strip().lower()
        return s == "resolved"

    @staticmethod
    def compute_fingerprint(target_url: str, endpoint: str, vulnerability: str, category: str = "") -> str:
        """
        Generate a deterministic SHA-256 fingerprint for a vulnerability.
        Prevents duplicate counting of the same finding detected repeatedly across scans.
        """
        norm_target = (target_url or "").strip().rstrip("/").lower()
        norm_endpoint = (endpoint or "").strip().rstrip("/").lower()
        norm_vuln = (vulnerability or "").strip().lower()
        norm_cat = (category or "").strip().lower()
        raw = f"{norm_target}|{norm_endpoint}|{norm_vuln}|{norm_cat}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def get_all_time_analytics(cls, db: Session) -> Dict[str, Any]:
        """
        Calculates all-time cumulative analytics across all historical persisted scans.
        Deduplicates repeated detections using finding fingerprints while preserving occurrence totals.
        """
        total_scans = db.query(ScanRecord).count()

        # Query all findings across every historical scan (no recent-scan limits)
        findings: List[Finding] = (
            db.query(FindingRecord)
            .options(joinedload(FindingRecord.scan))
            .order_by(FindingRecord.created_at.asc())
            .all()
        )

        total_occurrences = len(findings)
        unique_findings_map: Dict[str, Dict[str, Any]] = {}

        severity_rank = {
            "informational": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
        }

        for f in findings:
            target_url = f.scan.target_url if f.scan else ""
            fp = cls.compute_fingerprint(
                target_url=target_url,
                endpoint=f.endpoint,
                vulnerability=f.vulnerability,
                category=f.category,
            )
            norm_sev = cls.normalize_severity(f.severity)
            norm_res = cls.is_status_resolved(f.status)

            if fp not in unique_findings_map:
                unique_findings_map[fp] = {
                    "fingerprint": fp,
                    "target_url": target_url,
                    "endpoint": f.endpoint,
                    "vulnerability": f.vulnerability,
                    "category": f.category,
                    "severity": norm_sev,
                    "is_resolved": norm_res,
                    "occurrences": 1,
                    "first_seen": f.created_at,
                    "last_seen": f.created_at,
                }
            else:
                entry = unique_findings_map[fp]
                entry["occurrences"] += 1
                entry["last_seen"] = f.created_at
                # Update resolution state based on the latest occurrence
                entry["is_resolved"] = norm_res
                # If severity was upgraded in any occurrence, reflect highest
                if severity_rank.get(norm_sev, 0) > severity_rank.get(entry["severity"], 0):
                    entry["severity"] = norm_sev

        total_unique = len(unique_findings_map)
        sev_dist = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        }
        resolved_count = 0
        unresolved_count = 0

        for entry in unique_findings_map.values():
            sev = entry["severity"]
            if sev in sev_dist:
                sev_dist[sev] += 1
            else:
                sev_dist["low"] += 1

            if entry["is_resolved"]:
                resolved_count += 1
            else:
                unresolved_count += 1

        percentages: Dict[str, float] = {}
        if total_unique > 0:
            for k, count in sev_dist.items():
                percentages[k] = round((count / total_unique) * 100, 1)
        else:
            for k in sev_dist:
                percentages[k] = 0.0

        return {
            "total_scans": total_scans,
            "total_unique_findings": total_unique,
            "total_occurrences": total_occurrences,
            "severity_distribution": sev_dist,
            "severity_percentages": percentages,
            "resolved_findings": resolved_count,
            "unresolved_findings": unresolved_count,
            "total_resolved": resolved_count,
            "total_unresolved": unresolved_count,
        }
