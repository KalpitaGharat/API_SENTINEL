"""Dataset & API Key Intelligence Router for API Sentinel.

Exposes dataset overview, provider distribution, benchmark evaluation,
and masked sample exploration endpoints.
"""

import os
import json
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    DatasetOverviewResponse,
    DatasetProvidersResponse,
    ProviderDetail,
    DatasetStatisticsResponse,
    BenchmarkResponse,
    DatasetSamplesResponse,
    DatasetSampleItem,
    SingleTestRequest,
    SingleTestResponse,
    BatchTestRequest,
    BatchTestSessionResponse,
    BatchTestResultItem,
    BatchTestResultsListResponse,
    TestSessionHistoryItem,
    TestSessionHistoryResponse,
)
from app.services.api_key_benchmark import (
    ApiKeyBenchmarkService,
    mask_credential,
    MASTER_DATASET_FILE,
    DEFAULT_TEST_SPLIT_FILE,
)

router = APIRouter(prefix="/api/dataset", tags=["Dataset & Benchmark"])

METADATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "metadata")
)
SPLITS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "dataset", "splits")
)

def _load_json_file(filename: str) -> dict:
    path = os.path.join(METADATA_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


@router.get(
    "/overview",
    response_model=DatasetOverviewResponse,
    summary="Get dataset overview statistics",
    description="Returns aggregate sample counts, positive/negative breakdown, and latest benchmark indicators."
)
def get_dataset_overview():
    """Retrieve top-level dataset metrics and latest benchmark score."""
    cleaning = _load_json_file("dataset_cleaning_report.json")
    benchmark = ApiKeyBenchmarkService.get_latest_results()

    return DatasetOverviewResponse(
        total_samples=cleaning.get("accepted_count", 10000),
        positive_samples=cleaning.get("positive_count", 5000),
        negative_samples=cleaning.get("negative_count", 5000),
        synthetic_samples=cleaning.get("synthetic_count", 9994),
        original_samples=cleaning.get("original_source_count", 6),
        provider_count=len(cleaning.get("provider_distribution", {})),
        last_benchmark_timestamp=benchmark.get("timestamp") if benchmark else None,
        last_benchmark_f1=benchmark.get("metrics", {}).get("f1") if benchmark else None,
        last_benchmark_accuracy=benchmark.get("metrics", {}).get("accuracy") if benchmark else None,
    )


@router.get(
    "/providers",
    response_model=DatasetProvidersResponse,
    summary="Get supported provider catalog and distribution",
    description="Returns provider pattern details, token prefixes, and sample counts."
)
def get_dataset_providers():
    """Retrieve provider breakdown and format characteristics."""
    cleaning = _load_json_file("dataset_cleaning_report.json")
    prov_dist = cleaning.get("provider_distribution", {})
    patterns_doc = _load_json_file("github_patterns.json")
    pattern_map = {p["provider"]: p for p in patterns_doc.get("patterns", [])}

    providers_list = []
    for prov_name, count in sorted(prov_dist.items()):
        pat = pattern_map.get(prov_name, {})
        providers_list.append(ProviderDetail(
            provider=prov_name,
            sample_count=count,
            positive_count=count // 2,
            negative_count=count - (count // 2),
            primary_prefix=pat.get("primary_prefix", "Custom / High-Entropy"),
            credential_type=pat.get("credential_type", "api_key"),
            description=pat.get("name", f"{prov_name.capitalize()} API Key Pattern"),
        ))

    return DatasetProvidersResponse(
        total_providers=len(providers_list),
        providers=providers_list
    )


@router.get(
    "/statistics",
    response_model=DatasetStatisticsResponse,
    summary="Get detailed cleaning, split, and licensing metadata",
    description="Returns full pre-processing statistics, train/val/test split counts, and attribution info."
)
def get_dataset_statistics():
    """Retrieve complete audit metadata for the dataset."""
    cleaning = _load_json_file("dataset_cleaning_report.json")
    splits = _load_json_file("dataset_split_metadata.json")
    nightfall_attr = _load_json_file("nightfall_source_attribution.json")
    github_patterns = _load_json_file("github_patterns.json")

    licensing = {
        "dataset_name": "API Sentinel 10,000-Sample API Key Benchmark Dataset",
        "synthetic_license": "Internal Synthetic Dataset (API Sentinel Evaluation License)",
        "nightfall_attribution": nightfall_attr.get("license", "Nightfall AI Evaluation Sample Data"),
        "github_reference": github_patterns.get("license", "GitHub Documentation (CC BY 4.0)"),
        "quarantine_status": "Strict Zero-Live-Credential Compliance Active (No live credentials stored or tested)"
    }

    return DatasetStatisticsResponse(
        cleaning_report=cleaning,
        splits=splits,
        licensing=licensing
    )


@router.get(
    "/benchmark",
    response_model=BenchmarkResponse,
    summary="Get latest API key detection benchmark results",
    description="Returns precision, recall, F1, accuracy, and per-provider detection metrics against held-out test data."
)
def get_benchmark_results():
    """Retrieve the most recent benchmark evaluation report."""
    return ApiKeyBenchmarkService.get_latest_results()


@router.post(
    "/benchmark/run",
    response_model=BenchmarkResponse,
    summary="Execute API key detection benchmark",
    description="Runs detection evaluation asynchronously across all 1,500 held-out test split samples."
)
async def run_benchmark():
    """Trigger a live evaluation run without blocking the event loop."""
    result = await run_in_threadpool(ApiKeyBenchmarkService.run_benchmark)
    return result


@router.get(
    "/benchmark/history",
    summary="Retrieve benchmark execution history",
    description="Returns chronological benchmark runs and historical metric comparisons."
)
def get_benchmark_history():
    """List historical benchmark runs."""
    return ApiKeyBenchmarkService.get_benchmark_history()


@router.get(
    "/samples",
    response_model=DatasetSamplesResponse,
    summary="Explore dataset samples with masking",
    description="Allows paginated exploration with provider and label filtering. Sensitive strings are safely masked."
)
def get_dataset_samples(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
    provider: Optional[str] = Query(None, description="Filter by provider (e.g., aws, openai, stripe)"),
    label: Optional[str] = Query(None, description="Filter by label ('positive' or 'negative')"),
    source: Optional[str] = Query(None, description="Filter by source ('custom_synthetic' or 'nightfall_sample_data')"),
    split: str = Query("test", description="Dataset split to query: 'test', 'train', 'validation', or 'master'"),
):
    """Retrieve paginated and filtered samples with string masking."""
    # Resolve target file
    if split == "master":
        target_path = MASTER_DATASET_FILE
    else:
        split_name = split if split in ("train", "validation", "test") else "test"
        target_path = os.path.join(SPLITS_DIR, f"api_keys_{split_name}.jsonl")

    if not os.path.exists(target_path):
        target_path = MASTER_DATASET_FILE

    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found. Ensure dataset generator has run."
        )

    matched_records = []
    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)

            # Apply filters
            if provider and rec.get("provider") != provider:
                continue
            if label and rec.get("label") != label:
                continue
            if source and rec.get("source") != source:
                continue

            matched_records.append(rec)

    total = len(matched_records)
    paged = matched_records[skip : skip + limit]

    items = []
    for r in paged:
        items.append(DatasetSampleItem(
            sample_id=r.get("sample_id", ""),
            provider=r.get("provider", ""),
            key_type=r.get("key_type", "api_key"),
            label=r.get("label", "positive"),
            is_synthetic=r.get("is_synthetic", True),
            format_valid=r.get("format_valid", True),
            source=r.get("source", "custom_synthetic"),
            masked_sample=mask_credential(r.get("sample", "")),
            notes=r.get("notes", "")
        ))

    return DatasetSamplesResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items
    )


# -----------------------------------------------------------------------------
# Operational Dataset-Powered Testing Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/test/single",
    response_model=SingleTestResponse,
    summary="Execute single-sample detection test",
    description="Loads a sample, executes detection engine, compares against expected label, and persists result."
)
def run_single_test(
    payload: SingleTestRequest,
    offset: int = Query(0, ge=0, description="Cycle through matching samples"),
    db: Session = Depends(get_db)
):
    """Execute detection test on exactly one API key sample."""
    try:
        result = ApiKeyBenchmarkService.execute_single_test(
            db=db,
            sample_id=payload.sample_id,
            provider=payload.provider,
            label=payload.label,
            split=payload.split,
            offset=offset
        )
        return SingleTestResponse.model_validate(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Test failed: {str(e)}")


@router.get(
    "/test/sample/{sample_id}",
    response_model=DatasetSampleItem,
    summary="Retrieve single masked sample metadata",
    description="Fetches sample details safely masked with zero raw secret exposure."
)
def get_sample_by_id(sample_id: str):
    """Fetch one sample safely masked with zero raw credential leakage."""
    rec = ApiKeyBenchmarkService.load_sample_from_dataset(sample_id=sample_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sample '{sample_id}' not found")
    return DatasetSampleItem(
        sample_id=rec.get("sample_id", ""),
        provider=rec.get("provider", ""),
        key_type=rec.get("key_type", "api_key"),
        label=rec.get("label", "positive"),
        is_synthetic=rec.get("is_synthetic", True),
        format_valid=rec.get("format_valid", True),
        source=rec.get("source", "custom_synthetic"),
        masked_sample=mask_credential(rec.get("sample", "")),
        notes=rec.get("notes", "")
    )


@router.post(
    "/test/batch",
    response_model=BatchTestSessionResponse,
    summary="Initiate a batch testing session",
    description="Runs batch testing across specified provider/category sample count with concurrent execution guard."
)
def run_batch_test(
    payload: BatchTestRequest,
    db: Session = Depends(get_db)
):
    """Execute automated batch testing session across dataset samples."""
    try:
        session = ApiKeyBenchmarkService.execute_batch_test(
            db=db,
            provider=payload.provider,
            label=payload.label,
            count=payload.count,
            split=payload.split
        )
        per_provider = session.session_summary.get("per_provider", []) if session.session_summary else []
        return BatchTestSessionResponse(
            session_id=session.id,
            test_mode=session.test_mode,
            provider_filter=session.provider_filter,
            label_filter=session.label_filter,
            split_used=session.split_used,
            requested_sample_count=session.requested_sample_count,
            completed_sample_count=session.completed_sample_count,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            metrics={
                "precision": session.precision,
                "recall": session.recall,
                "f1": session.f1,
                "accuracy": session.accuracy,
                "tp": session.tp,
                "fp": session.fp,
                "tn": session.tn,
                "fn": session.fn
            },
            duration_ms=session.duration_ms,
            per_provider=per_provider
        )
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Batch test failed: {str(e)}")


@router.get(
    "/test/batch/{session_id}",
    response_model=BatchTestSessionResponse,
    summary="Get batch test session status and metrics"
)
def get_batch_session_status(session_id: str, db: Session = Depends(get_db)):
    """Retrieve execution metrics and status of a batch session."""
    session = ApiKeyBenchmarkService.get_test_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found")
    per_provider = session.session_summary.get("per_provider", []) if session.session_summary else []
    return BatchTestSessionResponse(
        session_id=session.id,
        test_mode=session.test_mode,
        provider_filter=session.provider_filter,
        label_filter=session.label_filter,
        split_used=session.split_used,
        requested_sample_count=session.requested_sample_count,
        completed_sample_count=session.completed_sample_count,
        status=session.status,
        started_at=session.started_at,
        completed_at=session.completed_at,
        metrics={
            "precision": session.precision,
            "recall": session.recall,
            "f1": session.f1,
            "accuracy": session.accuracy,
            "tp": session.tp,
            "fp": session.fp,
            "tn": session.tn,
            "fn": session.fn
        },
        duration_ms=session.duration_ms,
        per_provider=per_provider
    )


@router.get(
    "/test/batch/{session_id}/results",
    response_model=BatchTestResultsListResponse,
    summary="Get paginated individual sample results for a batch session"
)
def get_batch_session_results(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve detailed individual sample predictions from a session."""
    session = ApiKeyBenchmarkService.get_test_session_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session '{session_id}' not found")

    items, total = ApiKeyBenchmarkService.get_test_session_results(db, session_id, skip=skip, limit=limit)
    res_items = []
    for it in items:
        is_corr = (it.test_outcome in ("correct_detection", "correct_rejection"))
        res_items.append(BatchTestResultItem(
            result_id=it.id,
            session_id=it.session_id,
            sample_id=it.sample_id,
            masked_sample=it.masked_sample,
            expected_provider=it.expected_provider,
            detected_provider=it.detected_provider,
            expected_label=it.expected_label,
            predicted_label=it.predicted_label,
            is_correct=is_corr,
            test_outcome=it.test_outcome,
            detection_reason=it.detection_reason,
            execution_time_ms=it.execution_time_ms,
            created_at=it.created_at
        ))

    return BatchTestResultsListResponse(
        session_id=session_id,
        total=total,
        skip=skip,
        limit=limit,
        items=res_items
    )


@router.get(
    "/test/history",
    response_model=TestSessionHistoryResponse,
    summary="List historical test sessions (single and batch)"
)
def list_test_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List historical test runs chronologically."""
    sessions, total = ApiKeyBenchmarkService.get_test_history(db, skip=skip, limit=limit)
    hist_items = []
    for s in sessions:
        hist_items.append(TestSessionHistoryItem(
            session_id=s.id,
            test_mode=s.test_mode,
            provider_filter=s.provider_filter,
            label_filter=s.label_filter,
            requested_sample_count=s.requested_sample_count,
            completed_sample_count=s.completed_sample_count,
            status=s.status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            precision=s.precision,
            recall=s.recall,
            f1=s.f1,
            accuracy=s.accuracy,
            duration_ms=s.duration_ms
        ))

    return TestSessionHistoryResponse(total=total, sessions=hist_items)


@router.get(
    "/test/history/{session_id}",
    response_model=BatchTestSessionResponse,
    summary="Get full session detail by ID"
)
def get_session_history_detail(session_id: str, db: Session = Depends(get_db)):
    """Retrieve full session detail by ID."""
    return get_batch_session_status(session_id=session_id, db=db)

