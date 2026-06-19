"""
Credit Risk Analysis AI Agent - Main Streamlit Application
"""

import streamlit as st
import json
import time
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator_agent import OrchestratorAgent
from observability.tracer import Tracer
from observability.metrics import MetricsCollector
from governance.policy_engine import PolicyEngine
from hooks.pre_analysis_hook import PreAnalysisHook
from hooks.post_analysis_hook import PostAnalysisHook
from data.sample_profiles import SAMPLE_PROFILES

st.set_page_config(
    page_title="CreditIQ — AI Risk Agent",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.block-container { padding: 1.5rem 2rem 3rem 2rem; }

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ═══════════════════════════════════════
   HERO HEADER
════════════════════════════════════════ */
.hero {
    background: linear-gradient(135deg, #0f2744 0%, #1a3f6f 50%, #0f2744 100%);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    text-align: center;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: rgba(99,179,237,0.08);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -80px; left: -40px;
    width: 300px; height: 300px;
    background: rgba(99,179,237,0.05);
    border-radius: 50%;
}
.hero-tag {
    display: inline-block;
    background: rgba(99,179,237,0.2);
    color: #90cdf4;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 4px 14px;
    border-radius: 20px;
    border: 1px solid rgba(99,179,237,0.3);
    margin-bottom: 1rem;
}
.hero h1 {
    color: #ffffff;
    font-size: 2.6rem;
    font-weight: 800;
    margin: 0 0 0.6rem 0;
    line-height: 1.2;
    letter-spacing: -0.5px;
}
.hero h1 span { color: #63b3ed; }
.hero p {
    color: rgba(255,255,255,0.65);
    font-size: 1rem;
    margin: 0;
    max-width: 540px;
    margin-inline: auto;
}

/* ═══════════════════════════════════════
   SECTION TITLES
════════════════════════════════════════ */
.section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e2e8f0;
}

/* ═══════════════════════════════════════
   INPUT CARD
════════════════════════════════════════ */
.input-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 1.8rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
    border: 1px solid #f1f5f9;
    height: 100%;
}
.input-card-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #1e293b;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 2px solid #f1f5f9;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Override Streamlit input styles inside cards ── */
.stTextInput input,
.stNumberInput input {
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
    font-size: 0.92rem !important;
    padding: 0.5rem 0.75rem !important;
    transition: border-color 0.2s;
}
.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
}
.stSlider .st-bf { background: #e2e8f0; }
.stSlider [data-baseweb="slider"] { padding: 0; }

/* ═══════════════════════════════════════
   SCORING BUTTON
════════════════════════════════════════ */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 14px rgba(26,86,219,0.35) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(26,86,219,0.45) !important;
}
.stButton > button[kind="primary"]:active {
    transform: translateY(0) !important;
}

/* ═══════════════════════════════════════
   RESULT BANNER
════════════════════════════════════════ */
.result-banner {
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 1.5rem;
}
.result-banner.low {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 100%);
    border: 1px solid #059669;
}
.result-banner.medium {
    background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
    border: 1px solid #d97706;
}
.result-banner.high {
    background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
    border: 1px solid #dc2626;
}
.banner-left { display: flex; align-items: center; gap: 1.2rem; }
.banner-icon {
    width: 56px; height: 56px;
    background: rgba(255,255,255,0.15);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem;
}
.banner-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.65);
    margin-bottom: 2px;
}
.banner-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
}
.banner-right { text-align: right; }
.banner-score-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.5);
    margin-bottom: 2px;
}
.banner-score {
    font-size: 3rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1;
}
.banner-score span {
    font-size: 1.2rem;
    font-weight: 400;
    color: rgba(255,255,255,0.55);
}

/* ═══════════════════════════════════════
   GAUGE BAR
════════════════════════════════════════ */
.gauge-wrap {
    background: #fff;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
    border: 1px solid #f1f5f9;
    margin-bottom: 1.5rem;
}
.gauge-track {
    height: 14px;
    border-radius: 7px;
    background: linear-gradient(90deg, #10b981 0%, #f59e0b 50%, #ef4444 100%);
    position: relative;
    margin: 0.8rem 0 0.4rem;
}
.gauge-thumb {
    position: absolute;
    top: 50%;
    width: 22px; height: 22px;
    background: #fff;
    border: 3px solid #1e293b;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}
.gauge-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.73rem;
    color: #94a3b8;
    font-weight: 500;
    margin-top: 0.3rem;
}

/* ═══════════════════════════════════════
   STAT CARDS (key metrics row)
════════════════════════════════════════ */
.stat-card {
    background: #ffffff;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
    border: 1px solid #f1f5f9;
    border-top: 3px solid var(--accent);
    text-align: center;
}
.stat-card .stat-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.4rem;
}
.stat-card .stat-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.1;
}
.stat-card .stat-badge {
    display: inline-block;
    margin-top: 0.4rem;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
}
.badge-green  { background: #dcfce7; color: #166534; }
.badge-red    { background: #fee2e2; color: #991b1b; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-blue   { background: #dbeafe; color: #1e40af; }

/* ═══════════════════════════════════════
   EXPLANATION BOX
════════════════════════════════════════ */
.explanation-box {
    background: #f8fafc;
    border-left: 4px solid #3b82f6;
    border-radius: 0 12px 12px 0;
    padding: 1.2rem 1.4rem;
    font-size: 0.92rem;
    color: #334155;
    line-height: 1.7;
    margin-bottom: 1.5rem;
}

/* ═══════════════════════════════════════
   FACTOR ROWS
════════════════════════════════════════ */
.factor-row {
    display: flex;
    align-items: flex-start;
    gap: 0.8rem;
    padding: 0.9rem 1.1rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    border: 1px solid transparent;
}
.factor-row.positive { background: #f0fdf4; border-color: #bbf7d0; }
.factor-row.neutral  { background: #fefce8; border-color: #fef08a; }
.factor-row.negative { background: #fff1f2; border-color: #fecdd3; }
.factor-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
}
.factor-dot.positive { background: #22c55e; }
.factor-dot.neutral  { background: #eab308; }
.factor-dot.negative { background: #ef4444; }
.factor-name { font-weight: 700; font-size: 0.88rem; color: #1e293b; }
.factor-detail { font-size: 0.84rem; color: #64748b; margin-top: 1px; line-height: 1.5; }

/* ═══════════════════════════════════════
   DECISION + RATE CARDS
════════════════════════════════════════ */
.decision-card {
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    border: 1.5px solid;
}
.decision-card.approve { background: #f0fdf4; border-color: #86efac; }
.decision-card.review  { background: #fffbeb; border-color: #fde68a; }
.decision-card.reject  { background: #fff1f2; border-color: #fca5a5; }
.decision-card .dc-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.decision-card.approve .dc-label { color: #15803d; }
.decision-card.review  .dc-label { color: #b45309; }
.decision-card.reject  .dc-label { color: #b91c1c; }
.decision-card .dc-value {
    font-size: 1.6rem;
    font-weight: 800;
}
.decision-card.approve .dc-value { color: #166534; }
.decision-card.review  .dc-value { color: #92400e; }
.decision-card.reject  .dc-value { color: #991b1b; }

.rate-card {
    background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    text-align: center;
    color: #fff;
}
.rate-card .dc-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.6);
    margin-bottom: 0.5rem;
}
.rate-card .dc-value {
    font-size: 1.4rem;
    font-weight: 800;
    color: #fff;
}

/* ═══════════════════════════════════════
   GOVERNANCE PILLS
════════════════════════════════════════ */
.gov-row {
    display: flex; gap: 0.7rem; flex-wrap: wrap; margin-bottom: 1rem;
}
.gov-pill {
    display: flex; align-items: center; gap: 6px;
    padding: 0.45rem 1rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
}
.gov-pill.pass { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.gov-pill.fail { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
.gov-pill.warn { background: #fef9c3; color: #854d0e; border: 1px solid #fde68a; }
.gov-pill .dot { width: 7px; height: 7px; border-radius: 50%; }
.gov-pill.pass .dot { background: #22c55e; }
.gov-pill.fail .dot { background: #ef4444; }
.gov-pill.warn .dot { background: #eab308; }

/* ═══════════════════════════════════════
   TRACE TERMINAL
════════════════════════════════════════ */
.terminal {
    background: #0d1117;
    border-radius: 12px;
    overflow: hidden;
    font-family: 'Courier New', monospace;
}
.terminal-bar {
    background: #161b22;
    padding: 0.5rem 0.9rem;
    display: flex; align-items: center; gap: 6px;
    border-bottom: 1px solid #30363d;
}
.terminal-dot {
    width: 11px; height: 11px; border-radius: 50%;
}
.terminal-title {
    margin-left: 4px;
    font-size: 0.73rem;
    color: #8b949e;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}
.terminal-body {
    padding: 0.9rem 1.1rem;
    font-size: 0.78rem;
    line-height: 1.8;
    color: #e6edf3;
    max-height: 240px;
    overflow-y: auto;
}
.trace-agent { color: #79c0ff; }
.trace-time  { color: #6e7681; }
.trace-msg   { color: #aff5b4; }

/* ═══════════════════════════════════════
   SIDEBAR
════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #0f172a !important;
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 0.82rem !important;
    text-align: left !important;
    justify-content: flex-start !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,179,237,0.15) !important;
    border-color: rgba(99,179,237,0.35) !important;
}
.sidebar-section {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #475569 !important;
    padding: 0.5rem 0 0.3rem;
    margin-top: 0.3rem;
}
.agent-pill {
    display: flex; align-items: center; gap: 8px;
    padding: 0.45rem 0.7rem;
    border-radius: 8px;
    background: rgba(255,255,255,0.05);
    margin-bottom: 0.35rem;
    font-size: 0.79rem;
}
.agent-pill .ap-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #22c55e; flex-shrink: 0;
}
.ap-name { font-weight: 600; }
.ap-role { font-size: 0.7rem; color: #94a3b8 !important; }

/* ── Sidebar metrics ── */
.sb-metric {
    background: rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    margin-bottom: 0.5rem;
    display: flex; justify-content: space-between; align-items: center;
}
.sb-metric-label { font-size: 0.75rem; color: #94a3b8 !important; }
.sb-metric-value { font-size: 1rem; font-weight: 700; color: #e2e8f0 !important; }

/* ═══════════════════════════════════════
   FOOTER
════════════════════════════════════════ */
.footer {
    text-align: center;
    padding: 1.5rem 0;
    color: #94a3b8;
    font-size: 0.78rem;
    border-top: 1px solid #f1f5f9;
    margin-top: 2rem;
}

/* ── Streamlit expander tweak ── */
.streamlit-expanderHeader {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    background: #f8fafc !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Init ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def initialize_components():
    tracer        = Tracer()
    metrics       = MetricsCollector()
    policy_engine = PolicyEngine()
    orchestrator  = OrchestratorAgent(tracer=tracer, metrics=metrics, policy_engine=policy_engine)
    pre_hook      = PreAnalysisHook()
    post_hook     = PostAnalysisHook()
    return orchestrator, tracer, metrics, policy_engine, pre_hook, post_hook

orchestrator, tracer, metrics, policy_engine, pre_hook, post_hook = initialize_components()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 0.5rem; text-align:center;'>
        <div style='font-size:2rem;'>🏦</div>
        <div style='font-size:1rem; font-weight:800; color:#e2e8f0; letter-spacing:-0.3px;'>CreditIQ</div>
        <div style='font-size:0.72rem; color:#64748b; letter-spacing:1.5px; text-transform:uppercase;'>AI Risk Agent</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Sample Profiles</div>', unsafe_allow_html=True)

    risk_icons = {
        "Low Risk":    "🟢",
        "Medium Risk": "🟡",
        "High Risk":   "🔴",
    }
    for profile_name, profile_data in SAMPLE_PROFILES.items():
        tag = "🟢" if "Low" in profile_name else ("🟡" if "Medium" in profile_name else "🔴")
        short = profile_name.split(" (")[0]
        if st.button(f"{tag}  {short}", use_container_width=True, key=f"btn_{profile_name}"):
            st.session_state["sample_profile"] = profile_data

    st.markdown('<div class="sidebar-section" style="margin-top:1rem;">Active Agents</div>', unsafe_allow_html=True)
    agents = [
        ("Orchestrator", "Pipeline coordinator"),
        ("Risk Scoring", "Computes 0–100 score"),
        ("Explanation", "Generates reasoning"),
        ("Audit", "Immutable log"),
    ]
    for name, role in agents:
        st.markdown(f"""
        <div class="agent-pill">
            <div class="ap-dot"></div>
            <div>
                <div class="ap-name">{name}</div>
                <div class="ap-role">{role}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section" style="margin-top:1rem;">Session Stats</div>', unsafe_allow_html=True)
    dist = metrics.get_risk_distribution()
    stats = [
        ("Analyses Run",    metrics.get_total_analyses()),
        ("Low Risk",        dist.get("Low Risk", 0)),
        ("Medium Risk",     dist.get("Medium Risk", 0)),
        ("High Risk",       dist.get("High Risk", 0)),
    ]
    for label, val in stats:
        st.markdown(f"""
        <div class="sb-metric">
            <span class="sb-metric-label">{label}</span>
            <span class="sb-metric-value">{val}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section" style="margin-top:1rem;">MCP Integrations</div>', unsafe_allow_html=True)
    for mcp in ["Credit Bureau (CIBIL)", "Banking Data Warehouse"]:
        st.markdown(f"""
        <div class="agent-pill">
            <div class="ap-dot" style="background:#60a5fa;"></div>
            <div class="ap-name">{mcp}</div>
        </div>""", unsafe_allow_html=True)

# ─── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-tag">AI-Powered · Rule-Based · Governed</div>
    <h1>Credit<span>IQ</span> Risk Agent</h1>
    <p>Consistent, transparent, and auditable credit risk assessment for every customer — powered by a 4-agent AI pipeline.</p>
</div>
""", unsafe_allow_html=True)

# ─── INPUT FORM ───────────────────────────────────────────────────────────────
sample = st.session_state.get("sample_profile", {})

col_l, col_r = st.columns(2, gap="large")

with col_l:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="input-card-title">👤 Personal Information</div>', unsafe_allow_html=True)

    customer_name = st.text_input(
        "Customer Full Name",
        value=sample.get("name", ""),
        placeholder="e.g. Priya Mehta",
    )
    c1, c2 = st.columns(2)
    with c1:
        age = st.number_input("Age", min_value=18, max_value=80,
                              value=int(sample.get("age", 30)))
    with c2:
        employment_type = st.selectbox(
            "Employment Type",
            ["Salaried", "Self-Employed", "Business Owner", "Unemployed", "Retired"],
            index=["Salaried", "Self-Employed", "Business Owner", "Unemployed", "Retired"].index(
                sample.get("employment_type", "Salaried")
            )
        )
    monthly_income = st.number_input(
        "Monthly Income (₹)",
        min_value=0, max_value=10_000_000,
        value=int(sample.get("monthly_income", 50_000)),
        step=1000,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="input-card-title">💳 Financial Profile</div>', unsafe_allow_html=True)

    existing_loan = st.number_input(
        "Existing Loan Balance (₹)",
        min_value=0, max_value=100_000_000,
        value=int(sample.get("existing_loan", 0)),
        step=10_000,
    )
    credit_score = st.slider(
        "CIBIL Credit Score",
        min_value=300, max_value=900,
        value=int(sample.get("credit_score", 650)),
    )

    # Inline score badge
    if credit_score >= 800:
        badge, bc = "Excellent", "badge-green"
    elif credit_score >= 740:
        badge, bc = "Very Good", "badge-green"
    elif credit_score >= 670:
        badge, bc = "Good", "badge-blue"
    elif credit_score >= 580:
        badge, bc = "Fair", "badge-yellow"
    else:
        badge, bc = "Poor", "badge-red"
    st.markdown(f'<span class="stat-badge {bc}" style="font-size:0.8rem;padding:3px 12px;">{credit_score} — {badge}</span>', unsafe_allow_html=True)

    missed_payments = st.number_input(
        "Missed Payments (last 12 months)",
        min_value=0, max_value=24,
        value=int(sample.get("missed_payments", 0)),
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ─── ANALYSE BUTTON ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
_, c, _ = st.columns([1, 1.4, 1])
with c:
    run = st.button("⚡  Run Credit Risk Analysis", type="primary", use_container_width=True)

# ─── ANALYSIS ─────────────────────────────────────────────────────────────────
if run:
    if not customer_name.strip():
        st.error("Please enter a customer name first.")
        st.stop()

    profile = {
        "name": customer_name.strip(),
        "age": age,
        "monthly_income": monthly_income,
        "existing_loan": existing_loan,
        "credit_score": credit_score,
        "missed_payments": missed_payments,
        "employment_type": employment_type,
        "analysis_timestamp": datetime.datetime.now().isoformat()
    }

    with st.spinner("Running agent pipeline…"):
        hook_result = pre_hook.execute(profile)
        if not hook_result["valid"]:
            st.error(f"Validation error: {hook_result['reason']}")
            st.stop()
        t0     = time.time()
        result = orchestrator.analyse(profile)
        elapsed = time.time() - t0

    post_hook.execute(profile, result)
    metrics.record_analysis(result["risk_level"], elapsed)

    # ── store for display
    risk_level = result["risk_level"]
    risk_score = result["risk_score"]
    decision   = result.get("decision", "")
    gov        = result.get("governance", {})

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Analysis Results</div>', unsafe_allow_html=True)

    # ── RESULT BANNER ──────────────────────────────────────────────────────
    cls  = {"Low Risk": "low", "Medium Risk": "medium", "High Risk": "high"}[risk_level]
    icon = {"Low Risk": "✅", "Medium Risk": "⚠️", "High Risk": "🚨"}[risk_level]
    st.markdown(f"""
    <div class="result-banner {cls}">
        <div class="banner-left">
            <div class="banner-icon">{icon}</div>
            <div>
                <div class="banner-label">Risk Classification</div>
                <div class="banner-title">{risk_level}</div>
            </div>
        </div>
        <div class="banner-right">
            <div class="banner-score-label">Risk Score</div>
            <div class="banner-score">{risk_score}<span>/100</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── GAUGE ──────────────────────────────────────────────────────────────
    pct = risk_score / 100 * 100
    st.markdown(f"""
    <div class="gauge-wrap">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:0.78rem;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1px;">Risk Score Gauge</span>
            <span style="font-size:0.78rem;color:#94a3b8;">{elapsed*1000:.0f} ms · Audit {gov.get('audit_id','–')}</span>
        </div>
        <div class="gauge-track">
            <div class="gauge-thumb" style="left:{pct}%;"></div>
        </div>
        <div class="gauge-labels">
            <span>0 · Low</span><span>50 · Medium</span><span>100 · High</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── STAT CARDS ─────────────────────────────────────────────────────────
    dti   = (existing_loan / (monthly_income * 12) * 100) if monthly_income > 0 else 0
    cs_b  = "badge-green" if credit_score >= 700 else ("badge-yellow" if credit_score >= 580 else "badge-red")
    dti_b = "badge-green" if dti < 40 else ("badge-yellow" if dti < 70 else "badge-red")
    mp_b  = "badge-green" if missed_payments == 0 else ("badge-yellow" if missed_payments <= 2 else "badge-red")
    rs_b  = "badge-green" if risk_score <= 35 else ("badge-yellow" if risk_score <= 65 else "badge-red")

    s1, s2, s3, s4 = st.columns(4)
    stats_data = [
        (s1, "#3b82f6", "CIBIL Score",    str(credit_score),     badge,          cs_b),
        (s2, "#8b5cf6", "Debt-to-Income", f"{dti:.1f}%",         "Healthy" if dti < 40 else "High", dti_b),
        (s3, "#f59e0b", "Missed EMIs",    str(missed_payments),  "None" if missed_payments == 0 else "Flagged", mp_b),
        (s4, "#ef4444" if risk_score > 65 else ("#f59e0b" if risk_score > 35 else "#10b981"),
             "Risk Score", f"{risk_score}/100", risk_level, rs_b),
    ]
    for col, accent, label, value, badge_label, badge_cls in stats_data:
        with col:
            st.markdown(f"""
            <div class="stat-card" style="--accent:{accent}">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
                <span class="stat-badge {badge_cls}">{badge_label}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TWO COLUMN: explanation + factors ──────────────────────────────────
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.markdown('<div class="section-title">AI Explanation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="explanation-box">{result["explanation"]}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">Risk Factor Breakdown</div>', unsafe_allow_html=True)
        for f in result.get("factors", []):
            st.markdown(f"""
            <div class="factor-row {f['impact']}">
                <div class="factor-dot {f['impact']}"></div>
                <div>
                    <div class="factor-name">{f['name']}</div>
                    <div class="factor-detail">{f['detail']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-title">Banking Decision</div>', unsafe_allow_html=True)
        dc = "approve" if decision == "Approve" else ("review" if decision == "Review" else "reject")
        d_icon = {"Approve": "✅", "Review": "⚠️", "Reject": "❌"}.get(decision, "–")
        st.markdown(f"""
        <div class="decision-card {dc}" style="margin-bottom:0.8rem;">
            <div class="dc-label">Decision</div>
            <div class="dc-value">{d_icon} {decision}</div>
        </div>
        """, unsafe_allow_html=True)

        rate = result.get("interest_rate_band", "–")
        st.markdown(f"""
        <div class="rate-card" style="margin-bottom:1.3rem;">
            <div class="dc-label">Recommended Rate Band</div>
            <div class="dc-value">💰 {rate}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Governance</div>', unsafe_allow_html=True)
        p_ok   = gov.get("policy_compliant", True)
        b_ok   = gov.get("bias_check_passed", True)
        flags  = gov.get("flags", [])

        pills = [
            ("pass" if p_ok   else "fail", "●" , "Policy Compliant"   if p_ok  else "Policy Violation"),
            ("pass" if b_ok   else "warn", "●" , "Bias Check Passed"  if b_ok  else "Bias Flag Raised"),
            ("pass",                        "●" , f"Audit: {gov.get('audit_id','–')}"),
        ]
        pills_html = "".join(f'<div class="gov-pill {cls}"><div class="dot"></div>{label}</div>' for cls, dot, label in pills)
        st.markdown(f'<div class="gov-row">{pills_html}</div>', unsafe_allow_html=True)

        if flags:
            with st.expander(f"⚑  {len(flags)} Policy Flag(s)", expanded=False):
                for flag in flags:
                    severity_color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#3b82f6"}.get(flag.get("severity"), "#94a3b8")
                    st.markdown(f"""
                    <div style='padding:0.6rem 0.8rem;border-radius:8px;background:#f8fafc;border-left:3px solid {severity_color};margin-bottom:0.4rem;font-size:0.82rem;color:#334155;'>
                        <strong style='color:{severity_color};'>[{flag.get('policy')}]</strong> {flag.get('message')}
                    </div>""", unsafe_allow_html=True)

    # ── TRACE + DOWNLOAD ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    tc, dc2 = st.columns([3, 1], gap="large")

    with tc:
        with st.expander("🖥  Agent Execution Trace", expanded=False):
            trace_rows = "".join(
                f'<div><span class="trace-time">{t["timestamp"][11:19]}</span>  '
                f'<span class="trace-agent">[{t["agent"]}]</span>  '
                f'<span class="trace-msg">{t["message"]}</span></div>'
                for t in result.get("trace", [])
            )
            st.markdown(f"""
            <div class="terminal">
                <div class="terminal-bar">
                    <div class="terminal-dot" style="background:#ff5f57;"></div>
                    <div class="terminal-dot" style="background:#febc2e;"></div>
                    <div class="terminal-dot" style="background:#28c840;"></div>
                    <span class="terminal-title">Agent Pipeline Trace</span>
                </div>
                <div class="terminal-body">{trace_rows}</div>
            </div>
            """, unsafe_allow_html=True)

    with dc2:
        st.markdown("<br>", unsafe_allow_html=True)
        report = {
            "customer": profile,
            "analysis": {
                "risk_level":   risk_level,
                "risk_score":   risk_score,
                "decision":     decision,
                "explanation":  result["explanation"],
                "factors":      result.get("factors", []),
                "governance":   gov,
                "latency_ms":   round(elapsed * 1000, 1)
            }
        }
        st.download_button(
            label="📥  Download Report",
            data=json.dumps(report, indent=2),
            file_name=f"credit_risk_{customer_name.replace(' ','_')}_{datetime.date.today()}.json",
            mime="application/json",
            use_container_width=True,
        )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    CreditIQ AI Agent &nbsp;·&nbsp; 4-Agent Pipeline &nbsp;·&nbsp; 2 MCP Servers &nbsp;·&nbsp; 6 Governance Policies<br>
    <span style="color:#cbd5e1;">This tool supports, but does not replace, qualified banking professional judgment.</span>
</div>
""", unsafe_allow_html=True)
