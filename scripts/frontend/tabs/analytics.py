import streamlit as st
import pandas as pd
from scripts.backend.db import DatabaseManager

def render_analytics():
    st.markdown("## 📊 Analytics Dashboard")
    
    # --- Global Stats (Persistent) ---
    st.markdown("### 🌍 Global Overview")
    try:
        db = DatabaseManager()
        stats = db.get_stats()
        
        g1, g2, g3 = st.columns(3)
        g1.metric("Total Dubbing Tasks", stats.get("total_dubs", 0), help="All time dubbing tasks")
        g2.metric("Total Chat Messages", stats.get("total_messages", 0), help="All time remote meeting messages")
        g3.metric("Database Status", "Connected 🟢")
    except Exception as e:
        st.error(f"Could not load global stats: {e}")

    st.divider()

    # --- Live Session Stats (Transient) ---
    st.markdown("### ⚡ Live Session Performance")
    st.caption("Metrics from the current/most recent live translation session.")
    
    if 'orchestrator' not in st.session_state or not st.session_state.orchestrator.latencies:
        st.info("Start a live session in the 'Live Stream' tab to generate real-time performance data.")
    else:
        orch = st.session_state.orchestrator
        p95, p99, bleu, pgram = orch.get_stats()

        # Key Performance Indicators
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Quality Est.", f"{bleu:.1f}", delta=f"{len(orch.confidence_scores)} Segments")
        kpi2.metric("Confidence", f"{pgram:.1f}%", delta="System Confidence")
        kpi3.metric("Latency (P95)", f"{p95:.0f} ms", delta_color="inverse")
        kpi4.metric("Latency (P99)", f"{p99:.0f} ms", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts
        tab_latency, tab_quality = st.tabs(["⏱️ Latency Analysis", "✨ Quality Analysis"])
        
        with tab_latency:
            if orch.latencies:
                latency_data = pd.DataFrame({"Segment": range(len(orch.latencies)), "Latency (ms)": orch.latencies})
                st.line_chart(latency_data, x="Segment", y="Latency (ms)", color="#FF4B4B", width='stretch')
                st.caption("Processing time per speech segment.")
        
        with tab_quality:
            chart_data = {}
            if orch.confidence_scores:
                chart_data["Quality Est."] = orch.confidence_scores
                
            if chart_data:
                df_quality = pd.DataFrame(chart_data)
                st.line_chart(df_quality, color=["#4B4BFF"], width='stretch')
                st.caption("Translation quality metrics over time.")
