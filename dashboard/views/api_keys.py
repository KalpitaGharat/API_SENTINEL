"""
API Sentinel - Streamlit API Key Intelligence & Benchmark View
Queries FastAPI backend dataset endpoints as single source of truth.
Features Mode A (Single Sample), Mode B (Batch Testing), and Session History.
"""

import streamlit as st
import requests
import pandas as pd
from config import BACKEND_BASE_URL, ACCENT_CYAN, TEXT_MUTED

DATASET_API_BASE = f"{BACKEND_BASE_URL}/api/dataset"

PROVIDER_CHOICES = [
    "All",
    "aws",
    "openai",
    "nvidia",
    "github",
    "google_cloud",
    "stripe",
    "azure",
    "slack",
    "twilio",
    "generic_api_key"
]

def render_api_keys():
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="color: #E8F1FF; font-size: 1.8rem; font-weight: 800; margin: 0 0 6px 0;">
                API Key Intelligence &amp; Testing Engine
            </h1>
            <p style="color: {TEXT_MUTED}; font-size: 0.92rem; margin: 0;">
                Active detection engine testing against 10,000 realistic API key patterns across 10 major providers.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch Overview
    try:
        ov_res = requests.get(f"{DATASET_API_BASE}/overview", timeout=4).json()
    except Exception as e:
        st.error(f"Failed to connect to FastAPI backend: {e}")
        return

    # Top KPI Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Dataset Samples", f"{ov_res.get('total_samples', 10000):,}", "10 Providers")
    with col2:
        st.metric("Positive Keys", f"{ov_res.get('positive_samples', 5000):,}", "Real format")
    with col3:
        st.metric("Negative Lookalikes", f"{ov_res.get('negative_samples', 5000):,}", "Dummy/short/invalid")
    with col4:
        st.metric("Benchmark Accuracy", f"{ov_res.get('last_benchmark_accuracy', 0)}%", f"F1: {ov_res.get('last_benchmark_f1', 0)}")

    st.markdown("---")

    tab_single, tab_batch, tab_history, tab_benchmark, tab_samples = st.tabs([
        "🛡️ Single Test (Mode A)",
        "⚡ Batch Testing (Mode B)",
        "📜 Test History",
        "📊 Benchmark Suite",
        "🔍 Dataset Explorer"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: MODE A - SINGLE SAMPLE TESTING
    # -------------------------------------------------------------------------
    with tab_single:
        st.subheader("Mode A: Single Key Detection & Explainability")
        st.caption("Select provider & label criteria, execute the detection engine against exactly one sample, and inspect regex & entropy explanations.")

        if "single_offset" not in st.session_state:
            st.session_state.single_offset = 0

        c_prov, c_lbl, c_split = st.columns(3)
        with c_prov:
            s_prov = st.selectbox("Provider Target", PROVIDER_CHOICES, key="single_prov")
        with c_lbl:
            s_lbl = st.selectbox("Label Filter", ["positive", "negative", "Any"], key="single_lbl")
        with c_split:
            s_split = st.selectbox("Split", ["test", "validation", "train"], key="single_split")

        c_run, c_next, c_idx = st.columns([1, 1, 2])
        run_single = c_run.button("▶️ Run Detection Test", type="primary", use_container_width=True)
        if c_next.button("⏭️ Next Sample", use_container_width=True):
            st.session_state.single_offset += 1
            run_single = True

        c_idx.markdown(f"**Current Sample Offset:** `#{st.session_state.single_offset}`")

        if run_single:
            payload = {
                "split": s_split,
                "offset": st.session_state.single_offset
            }
            if s_prov != "All":
                payload["provider"] = s_prov
            if s_lbl != "Any":
                payload["label"] = s_lbl

            with st.spinner("Executing detection engine..."):
                try:
                    resp = requests.post(f"{DATASET_API_BASE}/test/single", json=payload, timeout=6)
                    if resp.status_code == 200:
                        res = resp.json()
                        st.session_state.last_single_result = res
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as ex:
                    st.error(f"Failed to test sample: {ex}")

        if "last_single_result" in st.session_state:
            res = st.session_state.last_single_result
            outcome = res.get("test_outcome")
            is_correct = res.get("is_correct")

            if outcome in ("correct_detection", "correct_rejection"):
                st.success(f"**TEST OUTCOME:** `{outcome.upper()}` (Accurate Prediction)")
            else:
                st.error(f"**TEST OUTCOME:** `{outcome.upper()}` (Prediction Mismatch)")

            st.code(res.get("masked_sample"), language="text")

            c_gt, c_pred, c_perf = st.columns(3)
            with c_gt:
                st.markdown("**Ground Truth**")
                st.markdown(f"- Provider: `{res.get('expected_provider')}`")
                st.markdown(f"- Label: `{res.get('expected_label')}`")
            with c_pred:
                st.markdown("**Engine Prediction**")
                st.markdown(f"- Detected: `{res.get('detected_provider') or 'None'}`")
                st.markdown(f"- Predicted: `{res.get('predicted_label')}`")
            with c_perf:
                st.markdown("**Performance & Entropy**")
                st.markdown(f"- Execution Time: `{res.get('execution_time_ms')} ms`")
                st.markdown(f"- Entropy Score: `{res.get('confidence_score') or 'N/A'} bits`")

            st.info(f"**Explanation:** {res.get('detection_reason')}")

    # -------------------------------------------------------------------------
    # TAB 2: MODE B - BATCH TESTING
    # -------------------------------------------------------------------------
    with tab_batch:
        st.subheader("Mode B: Batch Security Testing & Concurrency Guard")
        st.caption("Execute detection across custom batch slices with atomic lock protection.")

        bc_prov, bc_lbl, bc_cnt, bc_split = st.columns(4)
        with bc_prov:
            b_prov = st.selectbox("Provider Target", PROVIDER_CHOICES, key="batch_prov")
        with bc_lbl:
            b_lbl = st.selectbox("Category Filter", ["All", "positive", "negative"], key="batch_lbl")
        with bc_cnt:
            b_count = st.select_slider("Sample Count", options=[10, 50, 100, 250, 500], value=50, key="batch_count")
        with bc_split:
            b_split = st.selectbox("Split", ["test", "validation", "train"], key="batch_split")

        if st.button("🚀 Start Batch Test", type="primary"):
            b_payload = {
                "count": b_count,
                "split": b_split
            }
            if b_prov != "All":
                b_payload["provider"] = b_prov
            if b_lbl != "All":
                b_payload["label"] = b_lbl

            with st.spinner(f"Running detection on {b_count} samples..."):
                try:
                    b_resp = requests.post(f"{DATASET_API_BASE}/test/batch", json=b_payload, timeout=30)
                    if b_resp.status_code == 200:
                        b_data = b_resp.json()
                        st.session_state.last_batch_result = b_data
                        st.success(f"Batch completed in {b_data.get('duration_ms')} ms!")
                    elif b_resp.status_code == 409:
                        st.warning("A batch test session is currently in progress. Please wait.")
                    else:
                        st.error(f"Batch failed: {b_resp.text}")
                except Exception as ex:
                    st.error(f"Request error: {ex}")

        if "last_batch_result" in st.session_state:
            b_data = st.session_state.last_batch_result
            m = b_data.get("metrics", {})

            bm1, bm2, bm3, bm4, bm5 = st.columns(5)
            bm1.metric("Accuracy", f"{m.get('accuracy', 0)}%")
            bm2.metric("Precision", f"{m.get('precision', 0)}%")
            bm3.metric("Recall", f"{m.get('recall', 0)}%")
            bm4.metric("F1 Score", f"{m.get('f1', 0)}")
            bm5.metric("Duration", f"{b_data.get('duration_ms')} ms")

            st.write(f"**Confusion Matrix:** TP: `{m.get('tp')}` | FP: `{m.get('fp')}` | TN: `{m.get('tn')}` | FN: `{m.get('fn')}`")

            # Per provider table
            p_list = b_data.get("per_provider", [])
            if p_list:
                st.dataframe(pd.DataFrame(p_list), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 3: TEST RUN HISTORY
    # -------------------------------------------------------------------------
    with tab_history:
        st.subheader("Test Run History & SQLite Audit Log")
        try:
            h_resp = requests.get(f"{DATASET_API_BASE}/test/history?limit=30", timeout=4).json()
            sessions = h_resp.get("sessions", [])
            if sessions:
                hdf = pd.DataFrame(sessions)
                st.dataframe(
                    hdf[["session_id", "test_mode", "provider_filter", "requested_sample_count", "completed_sample_count", "accuracy", "f1", "status", "started_at"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No test history recorded yet.")
        except Exception as e:
            st.warning(f"Failed to fetch history: {e}")

    # -------------------------------------------------------------------------
    # TAB 4: BENCHMARK SUITE
    # -------------------------------------------------------------------------
    with tab_benchmark:
        st.subheader("Benchmark Evaluation Suite")
        try:
            bm_res = requests.get(f"{DATASET_API_BASE}/benchmark", timeout=4).json()
            b_metrics = bm_res.get("metrics", {})
            st.write(f"**Benchmark ID:** `{bm_res.get('benchmark_id')}` | **Held-out Split:** `{bm_res.get('dataset_split')}`")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Precision", f"{b_metrics.get('precision')}%")
            c2.metric("Recall", f"{b_metrics.get('recall')}%")
            c3.metric("F1 Score", f"{b_metrics.get('f1')}")
            c4.metric("Accuracy", f"{b_metrics.get('accuracy')}%")

            if st.button("🚀 Re-Run Full Benchmark (1,500 samples)"):
                with st.spinner("Evaluating 1,500 test split samples..."):
                    run_res = requests.post(f"{DATASET_API_BASE}/benchmark/run", timeout=15).json()
                    st.success(f"Benchmark completed in {run_res.get('duration_ms')} ms! F1: {run_res.get('metrics', {}).get('f1')}")
                    st.rerun()

            providers_data = bm_res.get("per_provider", [])
            if providers_data:
                st.dataframe(pd.DataFrame(providers_data), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Failed to fetch benchmark: {e}")

    # -------------------------------------------------------------------------
    # TAB 5: DATASET EXPLORER
    # -------------------------------------------------------------------------
    with tab_samples:
        st.subheader("Dataset Explorer (Masked Strings)")
        col_prov, col_lbl = st.columns(2)
        with col_prov:
            prov_choice = st.selectbox("Filter Provider", PROVIDER_CHOICES, key="exp_prov")
        with col_lbl:
            lbl_choice = st.selectbox("Filter Label", ["All", "positive", "negative"], key="exp_lbl")

        params = {"skip": 0, "limit": 20, "split": "test"}
        if prov_choice != "All":
            params["provider"] = prov_choice
        if lbl_choice != "All":
            params["label"] = lbl_choice

        try:
            sample_res = requests.get(f"{DATASET_API_BASE}/samples", params=params, timeout=4).json()
            samples = sample_res.get("items", [])
            if samples:
                sdf = pd.DataFrame(samples)
                st.dataframe(
                    sdf[["sample_id", "provider", "label", "masked_sample", "source", "notes"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No matching samples found.")
        except Exception as err:
            st.warning(f"Could not load samples: {err}")
