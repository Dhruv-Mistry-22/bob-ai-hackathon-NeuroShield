import streamlit as st
import pandas as pd
import numpy as np
import dateutil.parser
from datetime import timedelta
import os
import sys
import subprocess
import time
import plotly.graph_objects as go

# Add src to path so we can import from PATH 10
sys.path.append(os.path.abspath('src'))
from operator_brief import get_latest_valid_timestamp, build_operator_context, render_deterministic_brief

# -----------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------
st.set_page_config(
    page_title="GridPulse — Grid Operations Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------
# GLOBAL CSS — PROFESSIONAL CONTROL-ROOM AESTHETIC
# -----------------------------------------
st.markdown("""

<style>
/* ── Corporate Light Mode Base & Reset ────────────────────────────── */
html, body, [class*="css"] {
font-family: "Inter", -apple-system, "Segoe UI", system-ui, sans-serif;
font-size: 14px;
line-height: 1.6;
color: #1F2937;
}
.stApp { background-color: #F8FAFC; }

/* ── Hide Streamlit chrome ──────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 95%; margin: 0 auto; }


/* ── Sidebar (Command Center) ─────────────────────────────── */
[data-testid="stSidebar"] {
background-color: #F8FAFD !important;
border-right: 1px solid #E2E8F0;
width: 340px !important;
min-width: 340px !important;
max-width: 340px !important;
}
/* Scrollbar */
[data-testid="stSidebar"] ::-webkit-scrollbar {
width: 6px;
height: 6px;
}
[data-testid="stSidebar"] ::-webkit-scrollbar-track {
background: transparent;
}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
background: #CBD5E1;
border-radius: 10px;
}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
background: #94A3B8;
}

/* Branding */
.sb-logo-container {
display: flex; align-items: center; gap: 14px;
padding: 16px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 24px;
}
.sb-logo-mark {
background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
width: 44px; height: 44px; border-radius: 12px;
display: flex; align-items: center; justify-content: center;
color: white; font-weight: 800; font-size: 1.5rem;
box-shadow: 0 4px 10px rgba(37, 99, 235, 0.2);
}
.sb-logo-text { font-size: 20px; font-weight: 800; color: #102A56; letter-spacing: 0.05em; line-height: 1.1; }
.sb-logo-sub { font-size: 9px; color: #64748B; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 700; margin-top: 2px;}
.sb-logo-tagline { font-size: 8px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 8px; font-weight: 600;}

/* Section Headers */
.sb-section { 
font-size: 10px; color: #102A56; text-transform: uppercase; letter-spacing: 0.1em; 
margin-bottom: 12px; font-weight: 800; display:flex; align-items:center; gap:8px;
}

/* System Status Card */
.sb-status-card {
background: #F0FDF4; border: 1px solid #DCFCE7; border-radius: 12px;
padding: 12px 16px; display: flex; align-items: center; gap: 12px;
box-shadow: 0 2px 4px rgba(22, 163, 74, 0.05); margin-bottom: 24px;
}
.sb-status-dot {
width: 10px; height: 10px; background: #16B364; border-radius: 50%;
animation: pulse-green 2s infinite;
}
@keyframes pulse-green {
0% { box-shadow: 0 0 0 0 rgba(22, 179, 100, 0.4); }
70% { box-shadow: 0 0 0 6px rgba(22, 179, 100, 0); }
100% { box-shadow: 0 0 0 0 rgba(22, 179, 100, 0); }
}
.sb-status-text { font-size: 12px; font-weight: 800; color: #16A34A; text-transform: uppercase; letter-spacing: 0.05em;}
.sb-status-sub { font-size: 10px; color: #64748B; margin-top: 2px;}

/* Custom Radio (Scenario Cards) */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
display: flex; flex-direction: column; gap: 8px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px;
padding: 10px 14px; display: flex; align-items: center; cursor: pointer;
box-shadow: 0 1px 2px rgba(0,0,0,0.02); transition: all 0.2s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
transform: translateX(2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); background: #F4F8FF;
}
/* Hide native radio circle */
[data-testid="stSidebar"] [data-testid="stRadio"] label [data-baseweb="radio"] div:first-child {
display: none !important;
}
/* Style selected radio card */
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
background: #EFF6FF; border: 1px solid #3B82F6; border-left: 4px solid #3B82F6;
box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] p {
color: #1E3A8A !important; font-weight: 700 !important;
}
/* Inject icons via nth-child */
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-child(1)::before { content: "◉"; color: #3B82F6; font-size: 14px; margin-right: 12px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-child(2)::before { content: "○"; color: #16A34A; font-size: 14px; margin-right: 12px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-child(3)::before { content: "○"; color: #F59E0B; font-size: 14px; margin-right: 12px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:nth-child(4)::before { content: "○"; color: #EF4444; font-size: 14px; margin-right: 12px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"]:nth-child(1)::before { content: "◉"; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"]:nth-child(2)::before { content: "◉"; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"]:nth-child(3)::before { content: "◉"; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"]:nth-child(4)::before { content: "◉"; }

/* Selectbox */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
background: #FFFFFF !important; border: 1px solid #D8E5F5 !important;
border-radius: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:hover {
border-color: #3B82F6 !important; box-shadow: 0 4px 8px rgba(59, 130, 246, 0.1) !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div:focus-within {
border-color: #3B82F6 !important; border-left: 4px solid #3B82F6 !important;
}

/* Custom Buttons using adjacent selectors */
#btn-data + div[data-testid="stButton"] > button {
background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important;
color: #102A56 !important; font-weight: 600 !important; padding: 12px !important;
width: 100% !important; display: flex !important; justify-content: space-between !important;
box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; transition: all 0.2s ease !important;
}
#btn-data + div[data-testid="stButton"] > button::before { content: "▣"; color: #3B82F6; font-size: 16px; margin-right: 8px;}
#btn-data + div[data-testid="stButton"] > button::after { content: "→"; color: #94A3B8; font-size: 16px; margin-left: auto; transition: transform 0.2s;}
#btn-data + div[data-testid="stButton"] > button:hover {
background: #F4F8FF !important; border-color: #3B82F6 !important; transform: translateX(2px);
}
#btn-data + div[data-testid="stButton"] > button:hover::after { transform: translateX(4px); color: #3B82F6;}

#btn-pipeline + div[data-testid="stButton"] > button {
background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
border: none !important; border-radius: 10px !important; color: #FFFFFF !important;
font-weight: 700 !important; font-size: 14px !important; padding: 14px !important;
width: 100% !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
transition: all 0.2s ease !important;
}
#btn-pipeline + div[data-testid="stButton"] > button::before { content: "▶"; margin-right: 10px; font-size: 12px;}
#btn-pipeline + div[data-testid="stButton"] > button:hover {
background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
transform: translateY(-2px); box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4) !important;
}
#btn-pipeline + div[data-testid="stButton"] > button:active {
transform: translateY(0); box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2) !important;
}

/* Model Status Panel */
.sb-model-panel {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 32px;
}
.sb-model-row {
display: flex; justify-content: space-between; align-items: center;
height: 40px; padding: 0 12px; border-bottom: 1px solid #F1F5F9;
transition: all 0.2s ease; border-radius: 6px;
}
.sb-model-row:last-child { border-bottom: none; }
.sb-model-row:hover { background: #F4F8FF; transform: translateX(2px); }
.sb-model-row:hover .sb-model-icon { color: #2563EB; }
.sb-model-icon { font-size: 14px; color: #64748B; margin-right: 12px; width: 20px; text-align: center; transition: color 0.2s; }
.sb-model-name { font-size: 12px; font-weight: 600; color: #102A56; flex: 1; }
.sb-model-status { display: flex; align-items: center; gap: 6px; font-size: 10px; font-weight: 800; }
.sb-status-ready { color: #102A56; }
.sb-status-dot-ready { color: #16A34A; font-size: 12px;}

/* Footer */
.sb-footer {
position: relative; margin-top: auto; padding: 32px 0 16px 0;
text-align: right;
}
.sb-footer-text {
font-size: 9px; color: #64748B; text-transform: uppercase; letter-spacing: 0.15em; font-weight: 800;
position: relative; z-index: 2; padding-right: 16px;
}
.sb-footer-svg {
position: absolute; bottom: 0; left: -20px; width: 120%; height: 60px;
opacity: 0.05; pointer-events: none; z-index: 1;
}
/* ── Premium Control-Room Navigation (Tabs) ────────────────────── */
.stTabs [data-baseweb="tab-list"] {
background-color: #FFFFFF !important;
border: 1px solid #E2E8F0 !important;
border-radius: 12px !important;
box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
padding: 8px 12px !important;
gap: 8px !important;
margin-bottom: 32px !important;
overflow-x: auto;
}
.stTabs [data-baseweb="tab"] {
background-color: transparent !important;
color: #0F172A !important;
font-size: 13px !important;
font-weight: 600 !important;
letter-spacing: 0.03em !important;
text-transform: uppercase !important;
padding: 12px 14px !important;
border: 1px solid transparent !important;
border-top: 3px solid transparent !important;
border-radius: 8px !important;
transition: all 0.2s ease !important;
display: flex !important;
flex-direction: column !important;
align-items: center !important;
justify-content: center !important;
flex: 1 1 0px !important;
min-width: max-content;
}

/* Icon Injection using CSS Pseudo-Elements (No Python changes) */
.stTabs [data-baseweb="tab"]::before {
font-size: 1.4rem;
color: #64748B;
margin-bottom: 6px;
font-weight: normal;
transition: color 0.2s ease;
}
.stTabs [data-baseweb="tab"]:nth-child(1)::before { content: "⌂"; }
.stTabs [data-baseweb="tab"]:nth-child(2)::before { content: "◒"; }
.stTabs [data-baseweb="tab"]:nth-child(3)::before { content: "⚙"; }
.stTabs [data-baseweb="tab"]:nth-child(4)::before { content: "◫"; }
.stTabs [data-baseweb="tab"]:nth-child(5)::before { content: "⛨"; }
.stTabs [data-baseweb="tab"]:nth-child(6)::before { content: "⍟"; }

/* Hover State */
.stTabs [data-baseweb="tab"]:hover {
background-color: #F8FAFC !important;
transform: translateY(-1px);
}
.stTabs [data-baseweb="tab"]:hover::before {
color: #2563EB !important;
}

/* Active State (Control Module Selected) */
.stTabs [aria-selected="true"] {
background-color: #EFF6FF !important;
border-top: 3px solid #2563EB !important;
border-radius: 4px 4px 8px 8px !important;
box-shadow: 0 4px 12px rgba(37, 99, 235, 0.05) !important;
color: #0F172A !important;
}
.stTabs [aria-selected="true"]::before {
color: #2563EB !important;
}

/* Remove default Streamlit tab artifacts */
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
display: none !important;
visibility: hidden !important;
height: 0 !important;
width: 0 !important;
background-color: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
background-color: transparent !important;
}

/* ── Top Header ────────────────────────────────────────────── */
.gp-top-header {
display: flex; align-items: center; justify-content: space-between;
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 16px 32px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);
}

/* ── Status Indicators ───────────────────────────────────────── */
.gp-status-indicator {
display: flex; flex-direction: column;
border-radius: 12px; padding: 20px 24px; margin-bottom: 24px;
box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.gp-status-GREEN { background: #F0FDF4; border: 1px solid #BBF7D0; }
.gp-status-GREEN .gp-status-icon { color: #16A34A; }
.gp-status-GREEN .gp-status-title { color: #166534; }
.gp-status-YELLOW { background: #FEFCE8; border: 1px solid #FEF08A; }
.gp-status-YELLOW .gp-status-icon { color: #D97706; }
.gp-status-YELLOW .gp-status-title { color: #854D0E; }
.gp-status-RED { background: #FEF2F2; border: 1px solid #FECACA; }
.gp-status-RED .gp-status-icon { color: #DC2626; }
.gp-status-RED .gp-status-title { color: #991B1B; }

/* ── Action Plan Pipeline ────────────────────────────────────── */
.gp-pipeline-container {
display: flex; align-items: center; justify-content: space-between;
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 24px; margin-bottom: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}
.gp-pipeline-node {
display: flex; flex-direction: column; align-items: flex-start;
padding: 16px; border: 1px solid #E2E8F0; border-radius: 8px;
background: #F8FAFC; width: 18%; position: relative;
box-shadow: 0 2px 4px rgba(0,0,0,0.01);
}
.gp-pipeline-node-icon { font-size: 1.5rem; color: #2563EB; margin-bottom: 8px; }
.gp-pipeline-node-title { font-size: 0.75rem; font-weight: 700; color: #475569; margin-bottom: 4px; }
.gp-pipeline-node-val { font-size: 1.25rem; font-weight: 800; color: #0F172A; }
.gp-pipeline-node-sub { font-size: 0.65rem; color: #64748B; margin-top: 4px; }
.gp-pipeline-arrow { font-size: 1.5rem; color: #CBD5E1; }

.gp-recommendation-card {
background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
border-radius: 16px; padding: 32px; color: #FFFFFF;
box-shadow: 0 10px 25px rgba(15, 23, 42, 0.2);
position: relative; overflow: hidden; height: 100%;
}
.gp-rec-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #94A3B8; margin-bottom: 16px; font-weight: 700;}
.gp-rec-action { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.gp-rec-action-icon { font-size: 1.5rem; color: #38BDF8; }
.gp-rec-action-text { font-size: 1.1rem; font-weight: 600; color: #E2E8F0; }
.gp-rec-value { font-size: 3.5rem; font-weight: 800; color: #FFFFFF; line-height: 1.1; margin-bottom: 16px;}
.gp-rec-value span { font-size: 1.25rem; color: #94A3B8; font-weight: 600; }
.gp-rec-sub { font-size: 0.85rem; color: #CBD5E1; border-bottom: 1px solid #334155; padding-bottom: 16px; margin-bottom: 16px;}
.gp-rec-reason { font-size: 0.75rem; color: #94A3B8; }

.gp-chain-details {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.01); height: 100%;
}
.gp-chain-step { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 16px; position: relative;}
.gp-chain-number { 
background: #EFF6FF; color: #2563EB; font-weight: 700; font-size: 0.8rem;
width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 2;
}
.gp-chain-line { position: absolute; left: 11px; top: 24px; bottom: -16px; width: 2px; background: #E2E8F0; z-index: 1;}
.gp-chain-content { display: flex; flex-direction: column; }
.gp-chain-title { font-size: 0.8rem; font-weight: 700; color: #334155; }
.gp-chain-desc { font-size: 0.75rem; color: #64748B; }

.gp-expected-effect {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);
}
.gp-effect-row { display: flex; justify-content: space-between; gap: 24px;}
.gp-effect-box { flex: 1; border: 1px solid #F1F5F9; border-radius: 8px; padding: 16px; background: #F8FAFC;}
.gp-effect-title { font-size: 0.75rem; font-weight: 600; color: #64748B; margin-bottom: 8px;}
.gp-effect-val { font-size: 1.8rem; font-weight: 800; color: #0F172A;}
.gp-effect-sub { font-size: 0.7rem; color: #94A3B8; margin-top: 4px;}

.gp-constraint-check {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.01);
}
.gp-constraint-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid #F1F5F9; padding-bottom: 12px;}
.gp-constraint-title { font-size: 0.75rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;}
.gp-constraint-badge { background: #DCFCE7; color: #166534; font-size: 0.65rem; font-weight: 700; padding: 4px 8px; border-radius: 12px; display:flex; align-items:center; gap:4px;}
.gp-constraint-item { display: flex; align-items: center; gap: 12px; margin-bottom: 12px;}
.gp-constraint-icon { color: #16A34A; font-size: 1rem; }
.gp-constraint-text { font-size: 0.8rem; color: #334155; font-weight: 500;}

/* ── 3D Flow Visual ──────────────────────────────────────────── */
.gp-3d-container {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-top: 24px;
display: flex; justify-content: space-between; align-items: center;
}
.gp-3d-node {
display: flex; flex-direction: column; align-items: center; justify-content: center;
width: 120px; height: 120px; border-radius: 16px;
background: linear-gradient(145deg, #ffffff, #f1f5f9);
box-shadow: 8px 8px 16px #e2e8f0, -8px -8px 16px #ffffff;
border: 1px solid #F8FAFC; position: relative;
}
.gp-3d-node-accent { border: 2px solid #38BDF8; }
.gp-3d-icon { font-size: 2rem; color: #2563EB; margin-bottom: 8px; }
.gp-3d-label { font-size: 0.7rem; font-weight: 700; color: #475569; text-transform: uppercase; }
.gp-3d-val { font-size: 1.1rem; font-weight: 800; color: #0F172A; }
.gp-3d-arrow { font-size: 1.5rem; color: #CBD5E1; }
</style>

""", unsafe_allow_html=True)



# -----------------------------------------
# DATA LOADING (CACHED)
# -----------------------------------------
@st.cache_data
def load_data():
    try:
        data_dicts = {
            'demand': pd.read_csv('outputs/demand_model/demand_predictions.csv'),
            'renewable': pd.read_csv('outputs/renewable_model/renewable_predictions.csv'),
            'anomaly': pd.read_csv('outputs/anomaly_model/current_asset_status.csv'),
            'root_cause': pd.read_csv('outputs/root_cause/root_cause_predictions.csv'),
            'grid_risk': pd.read_csv('outputs/grid_risk/grid_risk_predictions.csv'),
            'opt': pd.read_csv('outputs/optimization/optimization_actions.csv'),
            'sim': pd.read_csv('outputs/simulation/baseline_vs_optimized.csv')
        }
        return data_dicts
    except FileNotFoundError as e:
        st.error(f"Required GridPulse output missing: {e}")
        st.stop()

data_dicts = load_data()

# -----------------------------------------
# SIDEBAR — COMMAND PANEL
# -----------------------------------------
with st.sidebar:
    st.markdown('''
<div class="sb-logo-container">
<div class="sb-logo-mark">⚡</div>
<div>
<div class="sb-logo-text">GRIDPULSE</div>
<div class="sb-logo-sub">Energy Operations Intelligence</div>
<div class="sb-logo-tagline">A STABLE GRID. A BRIGHTER TOMORROW.</div>
</div>
</div>
<div class="sb-status-card">
<div class="sb-status-dot"></div>
<div>
<div class="sb-status-text">System Online</div>
<div class="sb-status-sub">All systems operational</div>
</div>
<div style="margin-left:auto; color:#16A34A; font-size:16px;">∿</div>
</div>
''', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><span style="color:#2563EB;font-size:14px;">📍</span> GRID ZONE<br><span style="font-size:9px; color:#64748B; font-weight:500;">Select operational zone</span></div>', unsafe_allow_html=True)
    zones = data_dicts['demand']['zone_id'].unique().tolist()
    selected_zone = st.selectbox("Zone", zones, label_visibility="collapsed")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><span style="color:#2563EB;font-size:14px;">📚</span> VIEW / SCENARIO<br><span style="font-size:9px; color:#64748B; font-weight:500;">Select data view for analysis</span></div>', unsafe_allow_html=True)
    scenario = st.radio("Scenario", [
        "Live / Latest",
        "Demo A: Normal",
        "Demo B: High Stress",
        "Demo C: Adverse Counterfactual"
    ], label_visibility="collapsed")
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><span style="color:#2563EB;font-size:14px;">🗄</span> DATA<br><span style="font-size:9px; color:#64748B; font-weight:500;">Upload or enter data manually</span></div>', unsafe_allow_html=True)
    st.markdown('<div id="btn-data"></div>', unsafe_allow_html=True)
    if st.button("Manual Data Entry", use_container_width=True):
        st.session_state['show_manual'] = not st.session_state.get('show_manual', False)
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><span style="color:#2563EB;font-size:14px;">⚙</span> PIPELINE<br><span style="font-size:9px; color:#64748B; font-weight:500;">Administrative — re-run ML pipeline<br>with latest sensor data.</span></div>', unsafe_allow_html=True)
    st.markdown('<div id="btn-pipeline"></div>', unsafe_allow_html=True)
    run_pipeline = st.button("Run Full Pipeline", use_container_width=True)
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><span style="color:#2563EB;font-size:14px;">🎛</span> MODEL STATUS<br><span style="font-size:9px; color:#64748B; font-weight:500;">ML models and components</span></div>', unsafe_allow_html=True)
    
    model_rows = [
        ("Demand", "▥", True), ("Renewables", "♨", True), ("Asset Health", "∿", True),
        ("Risk Engine", "◈", True), ("Optimizer", "☷", True), ("Simulation", "▤", True),
    ]
    
    html_rows = ""
    for name, icon, ready in model_rows:
        html_rows += f'''
        <div class="sb-model-row">
            <div class="sb-model-icon">{icon}</div>
            <div class="sb-model-name">{name}</div>
            <div class="sb-model-status"><span class="sb-status-dot-ready">●</span> <span class="sb-status-ready">READY</span></div>
        </div>'''
        
    st.markdown(f'<div class="sb-model-panel">{html_rows}</div>', unsafe_allow_html=True)

    st.markdown('''
<div class="sb-footer">
<svg class="sb-footer-svg" viewBox="0 0 100 20" preserveAspectRatio="none">
<path d="M0,10 C20,20 30,0 50,10 C70,20 80,0 100,10 L100,20 L0,20 Z" fill="#2563EB"/>
<path d="M0,15 C25,5 35,20 60,10 C80,0 90,15 100,5 L100,20 L0,20 Z" fill="#1D4ED8"/>
</svg>
<div class="sb-footer-text">CLEANER GRIDS<br>BRIGHTER TOMORROWS <span style="font-size:12px; margin-left:4px;">🍃</span></div>
</div>
''', unsafe_allow_html=True)

# -----------------------------------------
# PIPELINE EXECUTION (runs before main UI render)
# -----------------------------------------
if run_pipeline:
    PIPELINE_STEPS = [
        ("src/features.py",              "PATH 2 — Feature Engineering"),
        ("src/demand_forecast.py",        "PATH 3 — Demand Spike Prediction"),
        ("src/renewable_forecast.py",     "PATH 4 — Renewable Generation Forecast"),
        ("src/asset_anomaly.py",          "PATH 5 — Asset Anomaly Detection"),
        ("src/root_cause.py",             "PATH 6 — Root Cause Analysis"),
        ("src/grid_risk.py",              "PATH 7 — Grid Risk Prediction"),
        ("src/optimizer.py",              "PATH 8 — Optimization Actions"),
        ("src/baseline_vs_optimized.py",  "PATH 9 — Baseline vs Optimized Simulation"),
        ("src/operator_brief.py",         "PATH 10 — Operator Brief"),
    ]
    st.markdown("---")
    st.markdown("## Pipeline Execution — Live Log")
    st.caption("Each step runs in sequence. Dashboard reloads on completion.")
    log_area = st.empty()
    log_lines = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.markdown("**Ingesting new 15-minute data tick...**")
    log_lines.append("Simulating new sensor data tick...")
    log_area.code("\n".join(log_lines), language="bash")
    t0 = time.time()
    sim_result = subprocess.run([sys.executable, "scripts/simulate_new_data.py"], capture_output=True, text=True)
    elapsed = time.time() - t0
    if sim_result.returncode == 0:
        new_ts_line = [l for l in sim_result.stdout.split("\n") if "New timestamp:" in l]
        new_ts_label = new_ts_line[0].replace("Done.", "").strip() if new_ts_line else ""
        log_lines[-1] = f"OK  New data ingested — {new_ts_label} ({elapsed:.1f}s)"
    else:
        log_lines[-1] = f"ERR Data simulation failed ({elapsed:.1f}s)"
        for err in sim_result.stderr.strip().split("\n")[-5:]:
            log_lines.append(f"    {err}")
        status_text.markdown("### Data ingestion failed.")
        log_area.code("\n".join(log_lines), language="bash")
        st.stop()
    log_area.code("\n".join(log_lines), language="bash")

    all_passed = True
    for idx, (script, label) in enumerate(PIPELINE_STEPS):
        pct = int(((idx + 1) / (len(PIPELINE_STEPS) + 1)) * 100)
        progress_bar.progress(pct)
        status_text.markdown(f"**Running:** `{label}`")
        log_lines.append(f"... {label}")
        log_area.code("\n".join(log_lines), language="bash")
        t0 = time.time()
        result = subprocess.run([sys.executable, script], capture_output=True, text=True)
        elapsed = time.time() - t0
        if result.returncode == 0:
            log_lines[-1] = f"OK  {label} ({elapsed:.1f}s)"
        else:
            log_lines[-1] = f"ERR {label} — FAILED ({elapsed:.1f}s)"
            for err in result.stderr.strip().split("\n")[-5:]:
                log_lines.append(f"    {err}")
            all_passed = False
        log_area.code("\n".join(log_lines), language="bash")

    progress_bar.progress(100)
    if all_passed:
        status_text.markdown("### Pipeline complete — all paths passed.")
        log_lines.append("")
        log_lines.append("Reloading dashboard...")
        log_area.code("\n".join(log_lines), language="bash")
        time.sleep(1.5)
        st.cache_data.clear()
        st.rerun()
    else:
        status_text.markdown("### Pipeline finished with errors. Check log above.")
    st.stop()

# -----------------------------------------
# TIMESTAMP / SCENARIO RESOLUTION
# -----------------------------------------
latest_ts = get_latest_valid_timestamp(data_dicts)

def get_demo_timestamp(scenario_name, zone_id):
    sim = data_dicts['sim']
    for i, sim_row in sim.iterrows():
        if sim_row['zone_id'] != zone_id: continue
        ts_target = sim_row['target_timestamp']
        ts_decision = (dateutil.parser.parse(ts_target) - timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')
        try:
            ctx = build_operator_context(data_dicts, ts_decision, zone_id)
        except Exception:
            continue
        flag = ctx['operator_decision']['decision_flag']
        has_adv = ctx['simulation']['adverse_counterfactual']
        if scenario_name == "Demo A: Normal" and flag == 'GREEN': return ts_decision
        if scenario_name == "Demo B: High Stress" and flag in ['YELLOW', 'RED'] and not has_adv: return ts_decision
        if scenario_name == "Demo C: Adverse Counterfactual" and flag == 'RED' and has_adv: return ts_decision
    return None

if scenario == "Live / Latest":
    selected_ts = latest_ts
else:
    demo_ts = get_demo_timestamp(scenario, selected_zone)
    if demo_ts is None:
        st.sidebar.warning(f"Scenario not found for {selected_zone}. Falling back to Live.")
        selected_ts = latest_ts
    else:
        selected_ts = demo_ts

try:
    context = build_operator_context(data_dicts, selected_ts, selected_zone)
except Exception as e:
    st.error(f"Error building context for {selected_ts} / {selected_zone}: {e}")
    st.stop()

flag = context['operator_decision']['decision_flag']
explanation = context['operator_decision']['explanation']

# -----------------------------------------
# GLOBAL HEADER
# -----------------------------------------
ts_display = selected_ts.replace(':00', '', 1) if selected_ts else "—"
try:
    import datetime as dt_mod
    ts_dt = dateutil.parser.parse(selected_ts)
    ts_display = ts_dt.strftime("%b %d, %Y  %H:%M:%S IST")
except Exception:
    ts_display = selected_ts

flag_color = {"GREEN": "#16A34A", "YELLOW": "#D97706", "RED": "#DC2626"}.get(flag, "#64748B")
flag_label = {"GREEN": "NORMAL OPERATION", "YELLOW": "ELEVATED RISK", "RED": "VALIDATION FAILED"}.get(flag, flag)

st.markdown(f"""
<div class="gp-top-header">
<div style="display:flex; align-items:center; gap:24px;">
<div style="font-size:0.75rem; color:#64748B; font-weight:600; background:#F1F5F9; padding:6px 12px; border-radius:6px;">{ts_display}</div>
<div style="display:flex; align-items:center; gap:12px;">
<span style="font-size:1.4rem; font-weight:800; color:#0F172A; letter-spacing:0.02em;">GRIDPULSE</span>
<span style="color:#2563EB; font-weight:800;">──╱╲──</span>
<span style="font-size:0.7rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; max-width:150px; line-height:1.2;">REAL-TIME INSIGHTS FOR A STABLE, SUSTAINABLE GRID</span>
</div>
</div>
<div style="display:flex; align-items:center; gap:32px;">
<div style="display:flex; flex-direction:column; align-items:flex-end;">
<span style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; font-weight:700;">Zone</span>
<span style="font-size:1rem; color:#0F172A; font-weight:700;">{selected_zone}</span>
</div>
<div style="display:flex; flex-direction:column; align-items:flex-end;">
<span style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; font-weight:700;">Status</span>
<span style="font-size:1rem; color:{flag_color}; font-weight:700; display:flex; align-items:center; gap:6px;"><span style="font-size:0.8rem;">●</span> {flag_label}</span>
</div>
<div style="width:1px; height:32px; background:#E2E8F0;"></div>
<div style="display:flex; align-items:center; gap:8px;">
<div style="background:#EFF6FF; color:#2563EB; width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">OP</div>
<span style="font-size:0.8rem; font-weight:600; color:#475569;">Operator</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# GLOBAL STATUS BANNER
# -----------------------------------------
if flag == 'GREEN':
    st.markdown(f"""<div class="gp-status-indicator gp-status-GREEN">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">●</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">Normal Operation</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">{explanation}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
elif flag == 'YELLOW':
    st.markdown(f"""<div class="gp-status-indicator gp-status-YELLOW">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">●</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">Elevated Condition — Operator Review Recommended</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">{explanation}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
elif flag == 'RED':
    st.markdown(f"""<div class="gp-status-indicator gp-status-RED">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">⚠</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">Action Validation Failed — Operator Approval Required</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">{explanation}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
# -----------------------------------------
# TABS — MAIN NAVIGATION
# -----------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "GRID STATUS", "FORECAST", "ASSET HEALTH", "ACTION PLAN", "ACTION VALIDATION", "OPERATOR DECISION"
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — GRID STATUS (Overview)
# ═══════════════════════════════════════════════════════════════════
with tab1:
    # ── PAGE HEADER ─────────────────────────────────────────────
    st.markdown(f'''
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:32px;">
<div style="display:flex; align-items:center; gap:16px;">
<div style="width:56px; height:56px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.8rem; color:#3B82F6; box-shadow:0 4px 6px rgba(59,130,246,0.05);">🗼</div>
<div>
<div style="font-size:1.5rem; font-weight:800; color:#0F172A; letter-spacing:0.02em;">Grid Status</div>
<div style="font-size:0.9rem; color:#64748B;">Real-time grid conditions and key indicators</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:16px;">
<div style="display:flex; align-items:center; gap:12px; border:1px solid #E2E8F0; padding:10px 16px; border-radius:12px; background:#FFFFFF; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
<div style="color:#3B82F6; font-size:1.4rem;">⏱</div>
<div>
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; font-weight:700;">Last Updated</div>
<div style="font-size:0.85rem; color:#0F172A; font-weight:800;">{ts_display}</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:12px; border:1px solid #E2E8F0; padding:10px 16px; border-radius:12px; background:#FFFFFF; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
<div style="color:#3B82F6; font-size:1.4rem;">📍</div>
<div>
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; font-weight:700;">Zone</div>
<div style="font-size:0.85rem; color:#0F172A; font-weight:800; display:flex; align-items:center; gap:8px;">{selected_zone} <span style="font-size:0.7rem; color:#94A3B8;">▼</span></div>
</div>
</div>
</div>
</div>
''', unsafe_allow_html=True)

    # ── OBSERVED — NOW ─────────────────────────────────────────
    st.markdown('''
<div style="font-size:0.7rem; color:#3B82F6; font-weight:800; text-transform:uppercase; letter-spacing:0.1em; display:flex; align-items:center; gap:8px; margin-bottom:16px;">
<div style="width:18px; height:18px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px;">⬇</div> OBSERVED — NOW
</div>
<style>
.gp-kpi-card {
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
padding: 20px 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
transition: transform 0.2s ease, box-shadow 0.2s ease;
display: flex; gap: 16px; align-items: center; cursor: default; position: relative; overflow: hidden;
}
.gp-kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.06); }
.gp-kpi-card::before {
content: ""; position: absolute; bottom: 0; right: 0; width: 100px; height: 100px;
border-radius: 50%; filter: blur(30px); opacity: 0.15; z-index: 0; pointer-events: none;
}
.gp-kpi-load::before { background: #3B82F6; }
.gp-kpi-ren::before { background: #22C55E; }
.gp-kpi-tx::before { background: #8B5CF6; }
.gp-kpi-curt::before { background: #EF4444; }
.gp-kpi-content { position: relative; z-index: 1; }
</style>
''', unsafe_allow_html=True)

    risk_now = context['grid_forecast']['transmission_risk']
    risk_colors = {"LOW": "#22C55E", "MEDIUM": "#F59E0B", "HIGH": "#F97316", "CRITICAL": "#EF4444"}
    rc = risk_colors.get(risk_now, "#64748B")
    
    st.markdown(f'''
<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr 1.2fr; gap:16px; margin-bottom:32px;">
<div class="gp-kpi-card gp-kpi-load">
<div style="font-size:2.2rem; color:#3B82F6; position:relative; z-index:1;">📈</div>
<div class="gp-kpi-content">
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Load</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1;">{context['current_state']['demand_mw']:.1f} <span style="font-size:1rem; font-weight:600; color:#64748B;">MW</span></div>
</div>
</div>
<div class="gp-kpi-card gp-kpi-ren">
<div style="font-size:2.2rem; color:#22C55E; position:relative; z-index:1;">🍃</div>
<div class="gp-kpi-content">
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Renewables</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1;">{context['current_state']['renewable_mw']:.1f} <span style="font-size:1rem; font-weight:600; color:#64748B;">MW</span></div>
</div>
</div>
<div class="gp-kpi-card gp-kpi-tx">
<div style="font-size:2.2rem; color:#8B5CF6; position:relative; z-index:1;">🗼</div>
<div class="gp-kpi-content">
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Transmission</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1;">{context['current_state']['transmission_utilization_pct']*100:.1f}%</div>
</div>
</div>
<div class="gp-kpi-card gp-kpi-curt">
<div style="font-size:2.2rem; color:#EF4444; position:relative; z-index:1;">📊</div>
<div class="gp-kpi-content">
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Curtailment</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1;">{context['current_state']['curtailment_mw']:.1f} <span style="font-size:1rem; font-weight:600; color:#64748B;">MW</span></div>
</div>
</div>
<div class="gp-kpi-card" style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-color:#0F172A;">
<div style="font-size:2.5rem; color:{rc}; text-shadow: 0 0 15px {rc}; position:relative; z-index:1;">🛡️</div>
<div class="gp-kpi-content">
<div style="font-size:0.65rem; color:#94A3B8; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Grid Risk</div>
<div style="font-size:1.6rem; font-weight:800; color:#FFFFFF; line-height:1;">0</div>
<div style="font-size:0.8rem; color:{rc}; font-weight:700; margin-top:4px;">{risk_now} <span style="color:#64748B; font-weight:600; font-size:0.7rem; margin-left:8px; text-transform:none;">No critical anomalies</span></div>
</div>
</div>
</div>
''', unsafe_allow_html=True)

    # ── FORECAST HORIZON — NEXT 60 MINUTES ──────────────────────
    st.markdown('''
<div style="font-size:0.7rem; color:#3B82F6; font-weight:800; text-transform:uppercase; letter-spacing:0.1em; display:flex; align-items:center; gap:8px; margin-bottom:16px;">
<div style="width:18px; height:18px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px;">🕒</div> FORECAST HORIZON — NEXT 60 MINUTES
</div>
''', unsafe_allow_html=True)

    delta_demand = context['demand_forecast']['predicted_demand_60m'] - context['current_state']['demand_mw']
    delta_ren = context['renewable_forecast']['renewable_60m'] - context['current_state']['renewable_mw']
    curt_prob = context['grid_forecast']['curtailment_probability']
    spike_prob = context['demand_forecast']['spike_probability']

    dem_arrow = "↑" if delta_demand > 0 else "↓"
    dem_color = "#EF4444" if delta_demand > 0 else "#22C55E"
    dem_bg    = "#FEF2F2" if delta_demand > 0 else "#F0FDF4"
    dem_pct   = (delta_demand / context['current_state']['demand_mw']) * 100 if context['current_state']['demand_mw'] > 0 else 0

    ren_arrow = "↑" if delta_ren > 0 else "↓"
    ren_color = "#22C55E" if delta_ren > 0 else "#EF4444"
    ren_bg    = "#F0FDF4" if delta_ren > 0 else "#FEF2F2"
    ren_pct   = (delta_ren / context['current_state']['renewable_mw']) * 100 if context['current_state']['renewable_mw'] > 0 else 0

    curt_label = "High" if curt_prob > 0.7 else "Moderate" if curt_prob > 0.3 else "Low"
    curt_color = "#EF4444" if curt_prob > 0.7 else "#F59E0B" if curt_prob > 0.3 else "#22C55E"
    curt_bg    = "#FEF2F2" if curt_prob > 0.7 else "#FEFCE8" if curt_prob > 0.3 else "#F0FDF4"

    fcol1, fcol2 = st.columns([3, 1])
    with fcol1:
        st.markdown(f'''
<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px;">
<div class="gp-kpi-card" style="flex-direction:column; align-items:flex-start; gap:8px;">
<div style="display:flex; gap:12px; align-items:center;">
<div style="font-size:1.5rem; color:#3B82F6;">📈</div>
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">Predicted Load</div>
</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1; margin-top:4px;">{context['demand_forecast']['predicted_demand_60m']:.1f} <span style="font-size:1rem; font-weight:600; color:#64748B;">MW</span></div>
<div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
<span style="font-size:0.75rem; font-weight:800; color:{dem_color}; background:{dem_bg}; padding:4px 8px; border-radius:6px;">{dem_arrow} {delta_demand:+.1f} MW</span>
<span style="font-size:0.75rem; color:#64748B; font-weight:600;">({dem_pct:+.1f}%)</span>
</div>
</div>
<div class="gp-kpi-card" style="flex-direction:column; align-items:flex-start; gap:8px;">
<div style="display:flex; gap:12px; align-items:center;">
<div style="font-size:1.5rem; color:#22C55E;">🍃</div>
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">Predicted Renewables</div>
</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1; margin-top:4px;">{context['renewable_forecast']['renewable_60m']:.1f} <span style="font-size:1rem; font-weight:600; color:#64748B;">MW</span></div>
<div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
<span style="font-size:0.75rem; font-weight:800; color:{ren_color}; background:{ren_bg}; padding:4px 8px; border-radius:6px;">{ren_arrow} {delta_ren:+.1f} MW</span>
<span style="font-size:0.75rem; color:#64748B; font-weight:600;">({ren_pct:+.1f}%)</span>
</div>
</div>
<div class="gp-kpi-card" style="flex-direction:column; align-items:flex-start; gap:8px;">
<div style="display:flex; gap:12px; align-items:center;">
<div style="font-size:1.5rem; color:#3B82F6;">🕒</div>
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">Curtailment Probability</div>
</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1; margin-top:4px;">{curt_prob:.0%}</div>
<div style="margin-top:8px;">
<span style="font-size:0.75rem; font-weight:800; color:{curt_color}; background:{curt_bg}; padding:4px 12px; border-radius:6px;">{curt_label}</span>
</div>
</div>
<div class="gp-kpi-card" style="flex-direction:column; align-items:flex-start; gap:8px;">
<div style="display:flex; gap:12px; align-items:center;">
<div style="font-size:1.5rem; color:#3B82F6;">📊</div>
<div style="font-size:0.65rem; color:#64748B; font-weight:800; text-transform:uppercase; letter-spacing:0.05em;">Demand Spike Risk</div>
</div>
<div style="font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1; margin-top:4px;">{spike_prob:.0%}</div>
<div style="margin-top:8px;">
<span style="font-size:0.75rem; font-weight:800; color:#22C55E; background:#F0FDF4; padding:4px 12px; border-radius:6px;">Low</span>
</div>
</div>
</div>
''', unsafe_allow_html=True)
    
    with fcol2:
        # Mini chart
        import plotly.graph_objects as go
        fig = go.Figure()
        y_vals = [context['current_state']['demand_mw'], context['demand_forecast']['predicted_demand_60m']]
        fig.add_trace(go.Scatter(
            x=[0, 1], y=y_vals, mode='lines', 
            line=dict(color='#3B82F6', width=3, shape='spline'), 
            fill='tozeroy', fillcolor='rgba(59,130,246,0.1)'
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=20), height=140,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, showticklabels=True, tickvals=[0, 1], ticktext=['Now', '+60 min'], color='#64748B', tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', showticklabels=True, color='#64748B', tickfont=dict(size=10), range=[2000, 3000]),
            title=dict(text='Load Forecast Trend (Next 60 min)', font=dict(size=11, color='#0F172A', weight='bold'), x=0)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ── EXPLANATION CARD (WHY GREEN?) ──────────────────────────
    if curt_prob > 0.5 and flag == 'GREEN':
        st.markdown(f'''
<div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:12px; padding:24px; margin-top:8px; margin-bottom:32px; display:flex; gap:20px; box-shadow:0 4px 6px rgba(22,163,74,0.02);">
<div style="font-size:2.5rem; color:#22C55E; text-shadow:0 0 10px rgba(34,197,94,0.3);">💡</div>
<div>
<div style="font-size:1.1rem; font-weight:800; color:#14532D; text-transform:uppercase; letter-spacing:0.02em; margin-bottom:8px;">Why GREEN with {curt_prob:.0%} Curtailment Probability?</div>
<div style="font-size:0.9rem; color:#166534; margin-bottom:12px;">Curtailment probability reflects forecast uncertainty — it does not indicate a physical grid safety violation.</div>
<div style="display:flex; gap:24px; font-size:0.85rem; color:#166534; font-weight:600; margin-bottom:12px;">
<div style="display:flex; align-items:center; gap:6px;"><div style="background:#22C55E; color:white; border-radius:50%; width:16px; height:16px; display:flex; align-items:center; justify-content:center; font-size:10px;">✓</div> No physical overload detected</div>
<div style="display:flex; align-items:center; gap:6px;"><div style="background:#22C55E; color:white; border-radius:50%; width:16px; height:16px; display:flex; align-items:center; justify-content:center; font-size:10px;">✓</div> No critical asset anomaly</div>
<div style="display:flex; align-items:center; gap:6px;"><div style="background:#22C55E; color:white; border-radius:50%; width:16px; height:16px; display:flex; align-items:center; justify-content:center; font-size:10px;">✓</div> No adverse counterfactual</div>
<div style="display:flex; align-items:center; gap:6px;"><div style="background:#22C55E; color:white; border-radius:50%; width:16px; height:16px; display:flex; align-items:center; justify-content:center; font-size:10px;">✓</div> Grid safety limits currently satisfied</div>
</div>
<div style="font-size:0.85rem; color:#166534; font-weight:600; opacity:0.8;">Elevated curtailment probability does not imply a critical grid-safety condition at this time.</div>
</div>
</div>
''', unsafe_allow_html=True)
    else:
        st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    # ── ENERGY FLOW & RECOMMENDED ACTION ───────────────────────
    eflow1, eflow2 = st.columns([3, 2])
    
    with eflow1:
        total_ren = context['current_state']['renewable_mw']
        demand_mw = context['current_state']['demand_mw']
        tx_util   = context['current_state']['transmission_utilization_pct'] * 100
        
        st.markdown(f'''
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:24px; height:100%; box-shadow:0 4px 6px rgba(0,0,0,0.02);">
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:32px;">
<div style="display:flex; align-items:center; gap:12px;">
<div style="background:#EFF6FF; color:#3B82F6; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">📚</div>
<div>
<div style="font-size:1.1rem; font-weight:800; color:#0F172A;">Energy Flow</div>
<div style="font-size:0.8rem; color:#64748B;">Real-time power flow across the grid</div>
</div>
</div>
<div style="display:flex; gap:20px; font-size:0.7rem; color:#64748B; font-weight:700;">
<div style="display:flex; align-items:center; gap:6px;"><span style="color:#22C55E; font-size:1.2rem;">→</span> Generation Flow</div>
<div style="display:flex; align-items:center; gap:6px;"><span style="color:#3B82F6; font-size:1.2rem;">→</span> Grid Flow</div>
<div style="display:flex; align-items:center; gap:6px;"><span style="color:#94A3B8; font-size:1.2rem;">⇢</span> Forecast Flow</div>
</div>
</div>

<div style="display:flex; justify-content:space-between; align-items:center; padding:0 24px; position:relative;">

<!-- Node 1 -->
<div style="text-align:center; z-index:2; display:flex; flex-direction:column; align-items:center;">
<div style="width:70px; height:70px; background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:2.2rem; box-shadow: 0 10px 15px -3px rgba(34,197,94,0.2); margin-bottom:12px; border:4px solid #FFFFFF;">🍃</div>
<div style="font-size:0.85rem; font-weight:800; color:#0F172A;">Solar + Wind</div>
<div style="font-size:1.1rem; font-weight:800; color:#0F172A;">{total_ren:.0f} <span style="font-size:0.75rem; color:#64748B;">MW</span></div>
</div>

<!-- Arrow 1 -->
<div style="font-size:2rem; color:#22C55E; font-weight:800; animation: gpPulse 2s infinite ease-in-out;">→</div>

<!-- Node 2 -->
<div style="text-align:center; z-index:2; display:flex; flex-direction:column; align-items:center;">
<div style="width:70px; height:70px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:2.2rem; box-shadow: 0 10px 15px -3px rgba(59,130,246,0.2); margin-bottom:12px; border:4px solid #FFFFFF;">🗼</div>
<div style="font-size:0.85rem; font-weight:800; color:#0F172A;">Grid Zone</div>
<div style="font-size:0.75rem; color:#3B82F6; background:#EFF6FF; padding:4px 10px; border-radius:12px; font-weight:800; margin-top:4px; border:1px solid #BFDBFE;">{selected_zone}</div>
</div>

<!-- Arrow 2 -->
<div style="font-size:2rem; color:#3B82F6; font-weight:800; animation: gpPulse 2.5s infinite ease-in-out;">→</div>

<!-- Node 3 -->
<div style="text-align:center; z-index:2; display:flex; flex-direction:column; align-items:center;">
<div style="width:70px; height:70px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:2.2rem; box-shadow: 0 10px 15px -3px rgba(59,130,246,0.2); margin-bottom:12px; border:4px solid #FFFFFF;">⚡</div>
<div style="font-size:0.85rem; font-weight:800; color:#0F172A;">Transmission</div>
<div style="font-size:1.1rem; font-weight:800; color:#0F172A;">{tx_util:.1f}%</div>
<div style="font-size:0.75rem; color:#64748B;">Utilization</div>
</div>

<!-- Arrow 3 -->
<div style="font-size:2rem; color:#3B82F6; font-weight:800; animation: gpPulse 3s infinite ease-in-out;">→</div>

<!-- Node 4 -->
<div style="text-align:center; z-index:2; display:flex; flex-direction:column; align-items:center;">
<div style="width:70px; height:70px; background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%); border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:2.2rem; box-shadow: 0 10px 15px -3px rgba(100,116,139,0.2); margin-bottom:12px; border:4px solid #FFFFFF;">🏢</div>
<div style="font-size:0.85rem; font-weight:800; color:#0F172A;">Load</div>
<div style="font-size:1.1rem; font-weight:800; color:#0F172A;">{demand_mw:.0f} <span style="font-size:0.75rem; color:#64748B;">MW</span></div>
<div style="font-size:0.75rem; color:#64748B;">Current Demand</div>
</div>
</div>
</div>
<style>
@keyframes gpPulse {{ 0% {{ opacity: 0.3; transform: translateX(0); }} 50% {{ opacity: 1; transform: translateX(4px); }} 100% {{ opacity: 0.3; transform: translateX(0); }} }}
</style>
''', unsafe_allow_html=True)
        
    with eflow2:
        action_mw = context['optimization']['action_mw']
        if action_mw > 0:
            action_type = context['optimization']['action']
            resource = context['optimization']['resource_type']
            reason = context['optimization']['reason']
            st.markdown(f'''
<div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius:12px; padding:24px; height:100%; box-shadow: 0 10px 25px -5px rgba(15,23,42,0.4); color:#FFFFFF; position:relative; overflow:hidden; transition:transform 0.2s; cursor:default;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">

<!-- Decorative CSS graphic mimicking battery -->
<div style="position:absolute; bottom:20px; right:20px; width:80px; height:120px; background:rgba(255,255,255,0.03); border-radius:12px; border:2px solid rgba(59,130,246,0.3); display:flex; flex-direction:column; padding:8px; gap:8px;">
<div style="flex:1; background:rgba(59,130,246,0.2); border-radius:4px; box-shadow: inset 0 0 10px rgba(59,130,246,0.5);"></div>
<div style="flex:1; background:rgba(59,130,246,0.2); border-radius:4px; box-shadow: inset 0 0 10px rgba(59,130,246,0.5);"></div>
<div style="flex:1; background:rgba(59,130,246,0.2); border-radius:4px; box-shadow: inset 0 0 10px rgba(59,130,246,0.5);"></div>
</div>

<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:32px; position:relative; z-index:1;">
<div style="display:flex; gap:12px; align-items:center;">
<div style="background:rgba(59,130,246,0.2); color:#60A5FA; width:40px; height:40px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:1.2rem;">⚙</div>
<div>
<div style="font-size:1.1rem; font-weight:800; color:#FFFFFF;">Recommended Action</div>
<div style="font-size:0.75rem; color:#94A3B8;">AI-driven operational recommendation</div>
</div>
</div>
<div style="background:rgba(255,255,255,0.1); padding:6px 10px; border-radius:6px; font-size:0.65rem; color:#CBD5E1; font-weight:600; letter-spacing:0.05em;">Based on current forecast</div>
</div>

<div style="position:relative; z-index:1; max-width:70%;">
<div style="font-size:0.75rem; color:#60A5FA; font-weight:800; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">{action_type}</div>
<div style="font-size:3.5rem; font-weight:800; color:#FFFFFF; line-height:1; margin-bottom:12px;">{action_mw:.1f} <span style="font-size:1.5rem; color:#94A3B8; font-weight:600;">MW</span></div>
<div style="font-size:0.85rem; color:#CBD5E1; font-weight:600; margin-bottom:32px;">{resource.capitalize()} · {selected_zone}</div>

<div style="border-top:1px solid rgba(255,255,255,0.1); padding-top:20px; font-size:0.85rem; color:#94A3B8; line-height:1.5;">
{reason}
</div>
</div>
</div>
''', unsafe_allow_html=True)
        else:
            st.markdown('''
<div style="background: linear-gradient(135deg, #064E3B 0%, #022C22 100%); border-radius:12px; padding:24px; height:100%; box-shadow: 0 10px 25px -5px rgba(2,44,34,0.4); color:#FFFFFF; transition:transform 0.2s; cursor:default;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
<div style="display:flex; gap:16px; align-items:center; margin-bottom:24px;">
<div style="background:rgba(16,185,129,0.2); color:#34D399; width:48px; height:48px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.5rem; font-weight:800;">✓</div>
<div>
<div style="font-size:1.2rem; font-weight:800; color:#FFFFFF;">No Action Required</div>
<div style="font-size:0.85rem; color:#A7F3D0;">Grid is operating safely</div>
</div>
</div>
<div style="font-size:0.95rem; color:#D1FAE5; line-height:1.6; border-top:1px solid rgba(255,255,255,0.1); padding-top:20px;">
Grid conditions are within normal operating parameters. No intervention recommended at this time.
</div>
</div>
''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — FORECAST
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""<div style="font-size:0.65rem; color:#3b6080; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:14px;">
Load &amp; Generation Forecast — Observed → +60 Minute Horizon
</div>""", unsafe_allow_html=True)

    # Summary row
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        st.metric("CURRENT LOAD", f"{context['current_state']['demand_mw']:.1f} MW")
    with fc2:
        st.metric("FORECAST LOAD (+60)", f"{context['demand_forecast']['predicted_demand_60m']:.1f} MW",
                  f"{context['demand_forecast']['predicted_demand_60m'] - context['current_state']['demand_mw']:+.1f} MW")
    with fc3:
        st.metric("CURRENT RENEWABLES", f"{context['current_state']['renewable_mw']:.1f} MW")
    with fc4:
        st.metric("FORECAST RENEWABLES (+60)", f"{context['renewable_forecast']['renewable_60m']:.1f} MW",
                  f"{context['renewable_forecast']['renewable_60m'] - context['current_state']['renewable_mw']:+.1f} MW")

    # Forecast comparison chart
    categories = ['Load (MW)', 'Renewables (MW)', 'Curtailment (MW)']
    obs_vals  = [context['current_state']['demand_mw'],
                 context['current_state']['renewable_mw'],
                 context['current_state']['curtailment_mw']]
    fc_vals   = [context['demand_forecast']['predicted_demand_60m'],
                 context['renewable_forecast']['renewable_60m'],
                 context['grid_forecast']['curtailment_predicted_mw']]

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(
        name='Observed (Now)',
        x=categories, y=obs_vals,
        marker_color='#3b82d4',
        marker_line=dict(color='#1d3a6a', width=1),
    ))
    fig_fc.add_trace(go.Bar(
        name='Forecast (t+60 min)',
        x=categories, y=fc_vals,
        marker_color='#4eb8c8',
        marker_line=dict(color='#1d4a5a', width=1),
        marker_pattern_shape='/',
    ))
    fig_fc.update_layout(
        barmode='group',
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='-apple-system, "Segoe UI", sans-serif', size=11, color='#495057'),
        title=dict(text='Observed vs Forecast  ·  t+60 min', font=dict(size=12, color='#6C757D'), x=0),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor='#E9ECEF', linecolor='#DEE2E6'),
        yaxis=dict(gridcolor='#E9ECEF', linecolor='#DEE2E6', title='MW'),
    )
    st.plotly_chart(fig_fc, use_container_width=True, theme=None)

    # Detailed breakdown
    st.markdown('<div class="gp-divider-label">Forecast Detail</div>', unsafe_allow_html=True)
    d1, d2 = st.columns(2)

    with d1:
        st.markdown("""<div class="gp-panel">
<div class="gp-panel-title">Demand Forecast</div>""", unsafe_allow_html=True)
        risk_level = context['demand_forecast']['risk_level']
        risk_c = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#f97316", "CRITICAL": "#ef4444"}.get(risk_level, "#8a9bb0")
        st.markdown(f"""
<div class="gp-brief-row"><span class="gp-brief-key">Current Load</span><span class="gp-brief-val">{context['current_state']['demand_mw']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Predicted Load (t+60)</span><span class="gp-brief-val">{context['demand_forecast']['predicted_demand_60m']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Demand Spike Probability</span><span class="gp-brief-val">{context['demand_forecast']['spike_probability']:.1%}</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Risk Level</span><span class="gp-brief-val" style="color:{risk_c};">{risk_level}</span></div>
</div>""", unsafe_allow_html=True)

    with d2:
        st.markdown("""<div class="gp-panel">
<div class="gp-panel-title">Renewable Forecast</div>""", unsafe_allow_html=True)
        st.markdown(f"""
<div class="gp-brief-row"><span class="gp-brief-key">Current Total Renewable</span><span class="gp-brief-val">{context['current_state']['renewable_mw']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Predicted Solar (t+60)</span><span class="gp-brief-val">{context['renewable_forecast']['solar_60m']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Predicted Wind (t+60)</span><span class="gp-brief-val">{context['renewable_forecast']['wind_60m']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Total Renewable (t+60)</span><span class="gp-brief-val">{context['renewable_forecast']['renewable_60m']:.1f} MW</span></div>
</div>""", unsafe_allow_html=True)

    st.markdown("""<div class="gp-panel" style="margin-top:4px;">
<div class="gp-panel-title">Grid Risk Forecast</div>""", unsafe_allow_html=True)
    tr = context['grid_forecast']['transmission_risk']
    tr_c = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#f97316", "CRITICAL": "#ef4444"}.get(tr, "#8a9bb0")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown(f"""<div class="gp-brief-row"><span class="gp-brief-key">Transmission Risk Class</span><span class="gp-brief-val" style="color:{tr_c};">{tr}</span></div>""", unsafe_allow_html=True)
    with g2:
        st.markdown(f"""<div class="gp-brief-row"><span class="gp-brief-key">Curtailment Probability</span><span class="gp-brief-val">{context['grid_forecast']['curtailment_probability']:.1%}</span></div>""", unsafe_allow_html=True)
    with g3:
        st.markdown(f"""<div class="gp-brief-row"><span class="gp-brief-key">Predicted Curtailment (t+60)</span><span class="gp-brief-val">{context['grid_forecast']['curtailment_predicted_mw']:.1f} MW</span></div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — ASSET HEALTH
# ═══════════════════════════════════════════════════════════════════
with tab3:
    anom_df = data_dicts['anomaly']
    zone_assets = anom_df[anom_df['zone_id'] == selected_zone].copy()

    # Calculate Summary Counts
    n_critical = (zone_assets['latest_anomaly_status'] == 'CRITICAL').sum()
    n_watch    = (zone_assets['latest_anomaly_status'] == 'WATCH').sum()
    n_normal   = (zone_assets['latest_anomaly_status'] == 'NORMAL').sum()
    n_total    = len(zone_assets)

    # PAGE HEADER
    st.markdown(f'''
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
<div style="display:flex; align-items:center; gap:16px;">
<div style="width:48px; height:48px; background:#F0FDF4; border:1px solid #DCFCE7; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:1.5rem; color:#16A34A; box-shadow:0 4px 6px rgba(22,163,74,0.05);">🌿</div>
<div>
<div style="font-size:1.4rem; font-weight:800; color:#0F172A; letter-spacing:0.02em;">Renewable Fleet</div>
<div style="font-size:0.85rem; color:#64748B;">Asset Health & Anomaly Status</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:16px;">
<div style="display:flex; align-items:center; gap:12px; border:1px solid #E2E8F0; padding:8px 16px; border-radius:12px; background:#FFFFFF; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
<div style="color:#3B82F6; font-size:1.2rem;">⏱</div>
<div>
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; font-weight:600;">Last Updated</div>
<div style="font-size:0.85rem; color:#0F172A; font-weight:700;">{ts_display}</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:12px; border:1px solid #E2E8F0; padding:8px 16px; border-radius:12px; background:#FFFFFF; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
<div style="color:#3B82F6; font-size:1.2rem;">📍</div>
<div>
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; font-weight:600;">Zone</div>
<div style="font-size:0.85rem; color:#0F172A; font-weight:700;">{selected_zone}</div>
</div>
</div>
</div>
</div>
''', unsafe_allow_html=True)

    # KPI CARDS
    st.markdown(f'''
<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px; margin-bottom:24px;">
<div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:12px; padding:20px; box-shadow:0 2px 4px rgba(59,130,246,0.05); transition:transform 0.2s; cursor:default;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
<div style="font-size:0.75rem; color:#1E3A8A; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Total Assets</div>
<div style="color:#2563EB; font-size:1.2rem;">📚</div>
</div>
<div style="font-size:2rem; font-weight:800; color:#1E3A8A; line-height:1;">{n_total}</div>
</div>
<div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:12px; padding:20px; box-shadow:0 2px 4px rgba(22,163,74,0.05); transition:transform 0.2s; cursor:default;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
<div style="font-size:0.75rem; color:#14532D; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Normal</div>
<div style="color:#16A34A; font-size:1.2rem;">☑</div>
</div>
<div style="font-size:2rem; font-weight:800; color:#14532D; line-height:1;">{n_normal}</div>
</div>
<div style="background:#FEFCE8; border:1px solid #FEF08A; border-radius:12px; padding:20px; box-shadow:0 2px 4px rgba(217,119,6,0.05); transition:transform 0.2s; cursor:default;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
<div style="font-size:0.75rem; color:#78350F; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Watch</div>
<div style="color:#D97706; font-size:1.2rem;">⚠</div>
</div>
<div style="font-size:2rem; font-weight:800; color:#78350F; line-height:1;">{n_watch}</div>
</div>
<div style="background:#FEF2F2; border:1px solid #FECACA; border-radius:12px; padding:20px; box-shadow:0 2px 4px rgba(220,38,38,0.05); transition:transform 0.2s; cursor:default;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;">
<div style="font-size:0.75rem; color:#7F1D1D; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">Critical</div>
<div style="color:#DC2626; font-size:1.2rem;">⛔</div>
</div>
<div style="font-size:2rem; font-weight:800; color:#7F1D1D; line-height:1;">{n_critical}</div>
</div>
</div>
''', unsafe_allow_html=True)

    # SEARCH & FILTER ROW
    st.markdown('''
<style>
/* Styling for Search Input */
div[data-baseweb="input"] { border-radius:10px !important; border-color:#E2E8F0 !important; }
div[data-baseweb="input"]:focus-within { border-color:#3B82F6 !important; box-shadow:0 0 0 1px #3B82F6 !important; }
/* Styling for Horizontal Radio Filters */
.stRadio > div { flex-direction:row !important; gap:8px !important; justify-content:flex-end; }
.stRadio label { 
background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:8px 16px; 
box-shadow:0 1px 2px rgba(0,0,0,0.02); transition:all 0.15s ease; cursor:pointer;
display:flex; align-items:center; min-width:max-content;
}
.stRadio label:hover { background:#F4F8FF; border-color:#BFDBFE; transform:translateY(-1px); }
.stRadio label[data-checked="true"] {
background:#EFF6FF; border:1px solid #3B82F6; box-shadow:0 2px 6px rgba(59,130,246,0.15);
}
.stRadio label[data-checked="true"] p { color:#1E3A8A !important; font-weight:700 !important; }
.stRadio label [data-baseweb="radio"] div:first-child { display:none !important; }

/* Inject dot colors into Radio buttons based on position */
.stRadio label:nth-child(2)::before { content:"●"; color:#16A34A; font-size:14px; margin-right:8px; }
.stRadio label:nth-child(3)::before { content:"●"; color:#D97706; font-size:14px; margin-right:8px; }
.stRadio label:nth-child(4)::before { content:"●"; color:#DC2626; font-size:14px; margin-right:8px; }

/* Asset Table row styles */
.gp-asset-row {
display:grid; grid-template-columns:1.5fr 1fr 1fr 1fr 1fr 0.2fr; padding:16px 24px;
border-bottom:1px solid #F1F5F9; font-size:0.85rem; align-items:center;
transition:all 0.15s ease; cursor:pointer; border-left:3px solid transparent; background:#FFFFFF;
}
.gp-asset-row:hover {
background:#F4F8FF; border-left:3px solid #3B82F6;
}
.gp-status-pill-NORMAL { background:#DCFCE7; color:#166534; padding:4px 10px; border-radius:12px; font-size:0.7rem; font-weight:700; display:inline-flex; align-items:center; gap:6px;}
.gp-status-pill-WATCH { background:#FEFCE8; color:#854D0E; padding:4px 10px; border-radius:12px; font-size:0.7rem; font-weight:700; display:inline-flex; align-items:center; gap:6px;}
.gp-status-pill-CRITICAL { background:#FEF2F2; color:#991B1B; padding:4px 10px; border-radius:12px; font-size:0.7rem; font-weight:700; display:inline-flex; align-items:center; gap:6px;}
</style>
''', unsafe_allow_html=True)

    f1, f2 = st.columns([1, 1.5])
    with f1:
        search_q = st.text_input("Search", placeholder="🔍 Search asset (e.g. SOLAR_01...)", label_visibility="collapsed")
    with f2:
        status_filter = st.radio("Filter", [f"All ({n_total})", f"Normal ({n_normal})", f"Watch ({n_watch})", f"Critical ({n_critical})"], label_visibility="collapsed")

    # Filter Logic
    filtered_assets = zone_assets.copy()
    if search_q:
        filtered_assets = filtered_assets[filtered_assets['asset_id'].str.contains(search_q, case=False)]
    
    if "Normal" in status_filter:
        filtered_assets = filtered_assets[filtered_assets['latest_anomaly_status'] == 'NORMAL']
    elif "Watch" in status_filter:
        filtered_assets = filtered_assets[filtered_assets['latest_anomaly_status'] == 'WATCH']
    elif "Critical" in status_filter:
        filtered_assets = filtered_assets[filtered_assets['latest_anomaly_status'] == 'CRITICAL']

    if len(filtered_assets) == 0:
        st.info("No assets match the current search or filter criteria.")
    else:
        # ASSET TABLE HEADER
        st.markdown(f'''
<div style="border:1px solid #E2E8F0; border-radius:12px; margin-top:24px; box-shadow:0 4px 6px rgba(0,0,0,0.02); overflow:hidden;">
<div style="display:grid; grid-template-columns:1.5fr 1fr 1fr 1fr 1fr 0.2fr; padding:12px 24px; background:#F8FAFC; border-bottom:1px solid #E2E8F0; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:#64748B; align-items:center;">
<div><span style="color:#3B82F6; margin-right:8px; font-size:1.1rem;">📦</span> Asset</div>
<div><span style="color:#3B82F6; margin-right:8px; font-size:1.1rem;">⚡</span> Output</div>
<div><span style="color:#3B82F6; margin-right:8px; font-size:1.1rem;">📊</span> Anomaly Score</div>
<div><span style="color:#3B82F6; margin-right:8px; font-size:1.1rem;">⚕</span> Status</div>
<div><span style="color:#3B82F6; margin-right:8px; font-size:1.1rem;">📋</span> Root Cause</div>
<div></div>
</div>
''', unsafe_allow_html=True)

        rc_df = data_dicts['root_cause']
        
        # Build Rows HTML
        rows_html = ""
        for _, row in filtered_assets.sort_values('latest_anomaly_score').iterrows():
            status = row['latest_anomaly_status']
            score  = row['latest_anomaly_score']
            asset  = row['asset_id']

            status_pill = f'<div class="gp-status-pill-{status}"><span style="font-size:0.6rem;">●</span> {status}</div>'
            
            # Icon determination based on name
            asset_icon = "☀" if "SOLAR" in asset.upper() else "✈" if "WIND" in asset.upper() else "📦"
            asset_color = "#F59E0B" if "SOLAR" in asset.upper() else "#3B82F6" if "WIND" in asset.upper() else "#64748B"

            # Root cause
            rc_match = rc_df[(rc_df['asset_id'] == asset)]
            if 'timestamp' in rc_match.columns:
                rc_match = rc_match[rc_match['timestamp'] == selected_ts]
            root_cause_str = rc_match.iloc[0]['primary_root_cause'] if len(rc_match) > 0 else '—'
            if not isinstance(root_cause_str, str) or root_cause_str == 'nan':
                root_cause_str = '—'

            # Output MW
            output_str = '—'
            if 'latest_generation_mw' in row.index and not pd.isna(row['latest_generation_mw']):
                output_str = f"{row['latest_generation_mw']:.1f} MW"
            elif 'latest_output_mw' in row.index and not pd.isna(row['latest_output_mw']):
                output_str = f"{row['latest_output_mw']:.1f} MW"

            rows_html += f'''
            <div class="gp-asset-row">
                <div style="font-weight:700; color:#0F172A;"><span style="color:{asset_color}; margin-right:12px; font-size:1rem;">{asset_icon}</span> {asset}</div>
                <div style="color:#475569;">{output_str}</div>
                <div style="color:#64748B;">{score:.3f}</div>
                <div>{status_pill}</div>
                <div style="color:#94A3B8; font-size:0.75rem;">{root_cause_str}</div>
                <div style="color:#CBD5E1; text-align:right;">›</div>
            </div>
            '''
        
        st.markdown(rows_html + "</div>", unsafe_allow_html=True)
        
        # Expanders for Anomalous Assets (Optional detail views)
        anomalous = filtered_assets[filtered_assets['latest_anomaly_status'] != 'NORMAL']
        if len(anomalous) > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('''<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:8px;">
Anomaly Detail — Flagged Assets
</div>''', unsafe_allow_html=True)

            for _, arow in anomalous.iterrows():
                status   = arow['latest_anomaly_status']
                asset_id = arow['asset_id']
                score    = arow['latest_anomaly_score']

                rc_match2 = rc_df[(rc_df['asset_id'] == asset_id)]
                if 'timestamp' in rc_match2.columns:
                    rc_match2 = rc_match2[rc_match2['timestamp'] == selected_ts]
                rc_row = rc_match2.iloc[0] if len(rc_match2) > 0 else None

                root_cause_str2 = rc_row['primary_root_cause'] if rc_row is not None else 'Unknown'
                confidence_str  = str(rc_row['confidence']) if rc_row is not None else '—'

                border_color = "#FECACA" if status == "CRITICAL" else "#FEF08A"
                status_color = "#DC2626" if status == "CRITICAL" else "#D97706"
                bg_color     = "#FEF2F2" if status == "CRITICAL" else "#FEFCE8"

                # Evidence items
                evidence_items = []
                if rc_row is not None:
                    for ev_col in ['top_evidence_1', 'top_evidence_2', 'top_evidence_3']:
                        if ev_col in rc_row.index and str(rc_row[ev_col]) not in ['nan', '', 'None']:
                            evidence_items.append(str(rc_row[ev_col]))
                if not evidence_items:
                    evidence_items = [
                        "Anomaly score outside normal operating range",
                        "Deviation detected relative to zone peer assets",
                    ]

                ev_html = "".join([f'<div style="color:#64748B; font-size:0.8rem; padding:2px 0;">→ {e}</div>' for e in evidence_items])

                out_str = '—'
                if 'latest_generation_mw' in arow.index and not pd.isna(arow['latest_generation_mw']):
                    out_str = f"{arow['latest_generation_mw']:.1f} MW"
                elif 'latest_output_mw' in arow.index and not pd.isna(arow['latest_output_mw']):
                    out_str = f"{arow['latest_output_mw']:.1f} MW"

                perf_ratio = arow.get('latest_performance_ratio', None)
                expected_gen = arow.get('latest_expected_generation_mw', None)
                perf_str = f"{perf_ratio:.0%}" if perf_ratio is not None and not pd.isna(perf_ratio) else '—'
                expected_str = f"{expected_gen:.1f} MW" if expected_gen is not None and not pd.isna(expected_gen) else '—'

                with st.expander(f"{asset_id}  —  {status}", expanded=(status == 'CRITICAL')):
                    ea1, ea2, ea3, ea4 = st.columns(4)
                    with ea1:
                        st.markdown(f'''<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:8px; text-align:center;">
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em;">Output</div>
<div style="font-size:1.2rem; font-weight:800; color:#0F172A;">{out_str}</div>
</div>''', unsafe_allow_html=True)
                    with ea2:
                        st.markdown(f'''<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:8px; text-align:center;">
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em;">Expected</div>
<div style="font-size:1.2rem; font-weight:800; color:#0F172A;">{expected_str}</div>
</div>''', unsafe_allow_html=True)
                    with ea3:
                        st.markdown(f'''<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:8px; text-align:center;">
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em;">Performance</div>
<div style="font-size:1.2rem; font-weight:800; color:{status_color};">{perf_str}</div>
</div>''', unsafe_allow_html=True)
                    with ea4:
                        st.markdown(f'''<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin-bottom:8px; text-align:center;">
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em;">Status</div>
<div style="font-size:1.2rem; font-weight:800; color:{status_color};">{status}</div>
</div>''', unsafe_allow_html=True)

                    st.markdown(f'''<div style="background:{bg_color}; border:1px solid {border_color}; border-radius:8px; padding:16px 20px; margin-top:8px;">
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px; font-weight:700;">Diagnostic</div>
<div style="font-size:1rem; color:#0F172A; font-weight:700; margin-bottom:6px;">{root_cause_str2}</div>
<div style="font-size:0.75rem; color:#64748B; margin-bottom:12px;">Confidence: {confidence_str}</div>
<div style="border-top:1px solid {border_color}; padding-top:12px; margin-top:8px;">
<div style="font-size:0.65rem; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px; font-weight:700;">Evidence</div>
{ev_html}
</div>
</div>''', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 4 — ACTION PLAN (Optimization)
# ═══════════════════════════════════════════════════════════════════
with tab4:
    opt = context['optimization']
    action_mw = opt['action_mw']
    tr  = context['grid_forecast']['transmission_risk']
    
    st.markdown("""<div style="display:flex; justify-content:space-between; align-items:center; border-left:4px solid #2563EB; padding-left:12px; margin-bottom:24px;">
<span style="font-size:1.1rem; font-weight:800; color:#0F172A; text-transform:uppercase; letter-spacing:0.05em;">GRID ACTION PLAN <span style="color:#CBD5E1; font-weight:400; margin:0 8px;">—</span> <span style="font-size:0.85rem; color:#64748B;">DECISION CHAIN & RECOMMENDED INTERVENTION</span></span>
<span style="font-size:0.75rem; color:#475569; background:#F1F5F9; padding:4px 12px; border-radius:12px; font-weight:600;">Scenario: """ + scenario + """</span>
</div>""", unsafe_allow_html=True)

    # HORIZONTAL PIPELINE
    st.markdown(f"""
<div class="gp-pipeline-container">
<div class="gp-pipeline-node">
<div class="gp-pipeline-node-icon">📈</div>
<div class="gp-pipeline-node-title">Demand Forecast</div>
<div class="gp-pipeline-node-val">{context['demand_forecast']['predicted_demand_60m']:.1f} MW</div>
<div class="gp-pipeline-node-sub">Spike prob {context['demand_forecast']['spike_probability']:.0%}</div>
</div>
<div class="gp-pipeline-arrow">→</div>
<div class="gp-pipeline-node">
<div class="gp-pipeline-node-icon">🍃</div>
<div class="gp-pipeline-node-title">Renewable Forecast</div>
<div class="gp-pipeline-node-val">{context['renewable_forecast']['renewable_60m']:.1f} MW total</div>
<div class="gp-pipeline-node-sub">Solar {context['renewable_forecast']['solar_60m']:.1f} · Wind {context['renewable_forecast']['wind_60m']:.1f}</div>
</div>
<div class="gp-pipeline-arrow">→</div>
<div class="gp-pipeline-node" style="border: 2px solid {'#EF4444' if tr in ['HIGH', 'CRITICAL'] else '#3B82F6'}; background: {'#FEF2F2' if tr in ['HIGH', 'CRITICAL'] else '#EFF6FF'};">
<div class="gp-pipeline-node-icon">🛡️</div>
<div class="gp-pipeline-node-title">Grid Risk</div>
<div class="gp-pipeline-node-val">Curtailment prob</div>
<div class="gp-pipeline-node-sub" style="font-size:1.1rem; font-weight:800; color:{'#B91C1C' if tr in ['HIGH', 'CRITICAL'] else '#1D4ED8'};">{context['grid_forecast']['curtailment_probability']:.0%}</div>
</div>
<div class="gp-pipeline-arrow">→</div>
<div class="gp-pipeline-node">
<div class="gp-pipeline-node-icon">⚡</div>
<div class="gp-pipeline-node-title">Optimization</div>
<div class="gp-pipeline-node-val">{opt['action']} — {opt['resource_type']}</div>
<div class="gp-pipeline-node-sub">{action_mw:.1f} MW</div>
</div>
<div class="gp-pipeline-arrow">→</div>
<div class="gp-pipeline-node" style="border: 2px solid {'#22C55E' if not context['simulation']['adverse_counterfactual'] else '#EF4444'};">
<div class="gp-pipeline-node-icon">{'✅' if not context['simulation']['adverse_counterfactual'] else '❌'}</div>
<div class="gp-pipeline-node-title">Validation</div>
<div class="gp-pipeline-node-val">See Action</div>
<div class="gp-pipeline-node-sub">Validation tab</div>
</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.5, 1.5])
    with c1:
        st.markdown('<div style="font-size:0.7rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;">DECISION CHAIN DETAILS</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="gp-chain-details">
<div class="gp-chain-step">
<div class="gp-chain-number">1</div><div class="gp-chain-line"></div>
<div class="gp-chain-content">
<div class="gp-chain-title">Demand Forecast</div>
<div class="gp-chain-desc">{context['demand_forecast']['predicted_demand_60m']:.1f} MW · Spike prob {context['demand_forecast']['spike_probability']:.0%}</div>
</div>
</div>
<div class="gp-chain-step">
<div class="gp-chain-number">2</div><div class="gp-chain-line"></div>
<div class="gp-chain-content">
<div class="gp-chain-title">Renewable Forecast</div>
<div class="gp-chain-desc">{context['renewable_forecast']['renewable_60m']:.1f} MW total · Solar {context['renewable_forecast']['solar_60m']:.1f} · Wind {context['renewable_forecast']['wind_60m']:.1f}</div>
</div>
</div>
<div class="gp-chain-step">
<div class="gp-chain-number">3</div><div class="gp-chain-line"></div>
<div class="gp-chain-content">
<div class="gp-chain-title">Grid Risk</div>
<div class="gp-chain-desc">Curtailment prob {context['grid_forecast']['curtailment_probability']:.0%}</div>
</div>
</div>
<div class="gp-chain-step">
<div class="gp-chain-number">4</div><div class="gp-chain-line"></div>
<div class="gp-chain-content">
<div class="gp-chain-title">Optimization</div>
<div class="gp-chain-desc">{opt['action']} · {opt['resource_type']} · {action_mw:.1f} MW</div>
</div>
</div>
<div class="gp-chain-step" style="margin-bottom:0;">
<div class="gp-chain-number">5</div>
<div class="gp-chain-content">
<div class="gp-chain-title">Action Validation</div>
<div class="gp-chain-desc">See Action Validation tab</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

    with c2:
        if action_mw > 0:
            st.markdown(f"""
<div class="gp-recommendation-card">
<div class="gp-rec-title">RECOMMENDED ACTION</div>
<div class="gp-rec-action">
<div class="gp-rec-action-icon">🔋</div>
<div class="gp-rec-action-text">{opt['action']}</div>
</div>
<div class="gp-rec-value">{action_mw:.1f} <span>MW</span></div>
<div class="gp-rec-sub">{str(opt['resource_type']).capitalize()} · {selected_zone}</div>
<div class="gp-rec-reason">{opt['reason']}</div>
<!-- Subtle graphic element -->
<div style="position:absolute; right:-20px; bottom:-20px; opacity:0.1; font-size:12rem; line-height:1; user-select:none;">🔋</div>
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="gp-recommendation-card" style="background: linear-gradient(135deg, #14532D 0%, #064E3B 100%);">
<div class="gp-rec-title">RECOMMENDED ACTION</div>
<div class="gp-rec-action">
<div class="gp-rec-action-icon">✅</div>
<div class="gp-rec-action-text">NO ACTION REQUIRED</div>
</div>
<div class="gp-rec-value">0.0 <span>MW</span></div>
<div class="gp-rec-sub">All Systems · {selected_zone}</div>
<div class="gp-rec-reason">Grid conditions are within normal operating parameters. No intervention recommended at this time.</div>
</div>
""", unsafe_allow_html=True)

    with c3:
        if action_mw > 0:
            tx_now   = context['current_state']['transmission_utilization_pct'] * 100
            tx_after = max(0, tx_now - (action_mw / context['current_state']['demand_mw'] * 100))
            tx_delta = tx_after - tx_now
            
            st.markdown(f"""
<div class="gp-expected-effect">
<div style="font-size:0.7rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:12px;">EXPECTED EFFECT</div>
<div class="gp-effect-row">
<div class="gp-effect-box">
<div class="gp-effect-title">Transmission (Now)</div>
<div class="gp-effect-val">{tx_now:.1f}%</div>
<div class="gp-effect-sub">Current utilization</div>
</div>
<div class="gp-effect-box">
<div class="gp-effect-title">Transmission (After)</div>
<div class="gp-effect-val">{tx_after:.1f}%</div>
<div class="gp-effect-sub" style="color: #16A34A; font-weight:700; font-size:0.8rem;">↓ {tx_delta:.1f}%<br><span style="color:#64748B; font-weight:400; font-size:0.7rem;">Expected utilization</span></div>
</div>
</div>
</div>
<div class="gp-constraint-check">
<div class="gp-constraint-header">
<div class="gp-constraint-title">CONSTRAINT CHECK</div>
<div class="gp-constraint-badge">✅ ALL CHECKS PASSED</div>
</div>
<div class="gp-constraint-item"><div class="gp-constraint-icon">✅</div><div class="gp-constraint-text">Within power limits</div></div>
<div class="gp-constraint-item"><div class="gp-constraint-icon">✅</div><div class="gp-constraint-text">Battery capacity available</div></div>
<div class="gp-constraint-item"><div class="gp-constraint-icon">✅</div><div class="gp-constraint-text">Grid constraints satisfied</div></div>
<div class="gp-constraint-item" style="margin-bottom:0;"><div class="gp-constraint-icon">✅</div><div class="gp-constraint-text">No violation of operational limits</div></div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No constraints checked. Baseline conditions normal.")

# ═══════════════════════════════════════════════════════════════════
# TAB 5
with tab5:
    sim = context['simulation']
    has_adverse = sim['adverse_counterfactual']

    st.markdown("""<div style="font-size:0.65rem; color:#3b6080; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:14px;">
Action Validation — Counterfactual Simulation Results
</div>""", unsafe_allow_html=True)

    # Adverse banner
    if has_adverse:
        st.markdown(f"""<div class="gp-adverse">
<div class="gp-adverse-title"> Action Validation Failed</div>
<div class="gp-adverse-body">
The proposed optimization action produces <strong>worse outcomes</strong> than the baseline
under forecast error (counterfactual test). The recommendation cannot be safely auto-executed.<br><br>
<strong style="color:#ef4444;">Operator review required before any grid action is taken.</strong>
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="gp-status-indicator gp-status-GREEN">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">●</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">Action Validation Passed</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">The proposed action performs no worse than baseline under counterfactual simulation. Proceed with operator awareness.</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div class="gp-divider-label">Simulation Comparison — Baseline vs Proposed Action</div>', unsafe_allow_html=True)

    # Comparison table
    baseline_curt   = sim['baseline_curtailment_mwh']
    optimized_curt  = sim['optimized_curtailment_mwh']
    baseline_oload  = sim['baseline_overload_intervals']
    optimized_oload = sim['optimized_overload_intervals']
    curt_delta      = sim['curtailment_difference_mwh']
    oload_delta     = optimized_oload - baseline_oload

    curt_worse  = optimized_curt > baseline_curt
    oload_worse = optimized_oload > baseline_oload

    curt_class  = 'gp-compare-worse' if curt_worse  else 'gp-compare-proposed'
    oload_class = 'gp-compare-worse' if oload_worse else 'gp-compare-proposed'

    st.markdown(f"""
<style>
.gp-table-row {{
display:flex; justify-content:space-between; padding:16px 24px; font-size:0.9rem; align-items:center;
border-bottom:1px solid #F1F5F9; transition: background 0.2s ease; cursor:default;
}}
.gp-table-row:last-child {{ border-bottom:none; }}
.gp-table-row:hover {{ background:#F8FAFC; }}
</style>
<div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; overflow:hidden; margin-bottom:24px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
<div style="display:flex; justify-content:space-between; padding:12px 24px; background:#F8FAFC; border-bottom:1px solid #E2E8F0; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:#64748B; font-weight:700;">
<div style="flex:2;">Metric</div><div style="flex:1; text-align:right;">Baseline</div><div style="flex:1; text-align:right;">Proposed Action</div>
</div>
<div class="gp-table-row">
<div style="flex:2; font-weight:600; color:#102A56;">Curtailment (MWh)</div>
<div style="flex:1; text-align:right; color:#475569;">{baseline_curt:.1f}</div>
<div style="flex:1; text-align:right; font-weight:700; color:{'#EF4444' if curt_worse else '#16A34A'};">{optimized_curt:.1f} {'▲' if curt_worse else '▼'} {abs(curt_delta):.1f}</div>
</div>
<div class="gp-table-row">
<div style="flex:2; font-weight:600; color:#102A56;">Overload Intervals</div>
<div style="flex:1; text-align:right; color:#475569;">{baseline_oload}</div>
<div style="flex:1; text-align:right; font-weight:700; color:{'#EF4444' if oload_worse else '#16A34A'};">{optimized_oload} {'+' if oload_delta > 0 else ''}{oload_delta}</div>
</div>
</div>
""", unsafe_allow_html=True)

    # Scenario C visual — adverse state display
    if has_adverse:
        sv1, sv2 = st.columns(2)
        with sv1:
            st.markdown(f"""<div style="background:#0e1620; border:1px solid #1d2a38; border-radius:3px; padding:16px 20px;">
<div style="font-size:0.65rem; color:#3b6080; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">Baseline</div>
<div style="font-size:0.8rem; color:#8a9bb0; margin-bottom:4px;">Curtailment</div>
<div style="font-size:1.6rem; font-weight:600; color:#cad6e2;">{baseline_curt:.1f} <span style="font-size:0.8rem;">MWh</span></div>
<div style="font-size:0.8rem; color:#8a9bb0; margin-top:10px; margin-bottom:4px;">Overload Intervals</div>
<div style="font-size:1.6rem; font-weight:600; color:#cad6e2;">{baseline_oload}</div>
</div>""", unsafe_allow_html=True)
        with sv2:
            st.markdown(f"""<div style="background:#1a0808; border:2px solid #ef4444; border-radius:3px; padding:16px 20px;">
<div style="font-size:0.65rem; color:#7a3030; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:8px;">Proposed Action</div>
<div style="font-size:0.8rem; color:#9a6060; margin-bottom:4px;">Curtailment</div>
<div style="font-size:1.6rem; font-weight:700; color:#ef4444;">{optimized_curt:.1f} <span style="font-size:0.8rem;">MWh</span></div>
<div style="font-size:0.8rem; color:#9a6060; margin-top:10px; margin-bottom:4px;">Overload Intervals</div>
<div style="font-size:1.6rem; font-weight:700; color:#ef4444;">{optimized_oload}</div>
<div style="margin-top:10px; font-size:0.75rem; color:#c05050;">+{curt_delta:.1f} MWh above baseline  ·  +{oload_delta} overload intervals</div>
</div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="gp-approval-required">
<div class="gp-approval-title"> Operator Review Required</div>
<div class="gp-approval-body">
This recommendation has failed counterfactual validation. The proposed action creates worse physical
outcomes under forecast error than doing nothing.<br><br>
<strong>Do not execute without operator review and approval.</strong><br>
Recommendation → Validation → Human Decision. GridPulse does not automatically execute actions.
</div>
</div>""", unsafe_allow_html=True)
    else:
        # Non-adverse metrics
        st.markdown(f"""
<style>
.gp-metric-card {{
background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
transition: all 0.2s ease;
}}
.gp-metric-card:hover {{
transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.06);
border-color: #CBD5E1;
}}
</style>
<div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px; margin-top:8px;">
<div class="gp-metric-card">
<div style="font-size:0.75rem; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Baseline Curtailment</div>
<div style="font-size:1.8rem; font-weight:800; color:#0F172A;">{baseline_curt:.1f} <span style="font-size:1rem; color:#94A3B8;">MWh</span></div>
</div>
<div class="gp-metric-card">
<div style="font-size:0.75rem; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Proposed Curtailment</div>
<div style="font-size:1.8rem; font-weight:800; color:#0F172A;">{optimized_curt:.1f} <span style="font-size:1rem; color:#94A3B8;">MWh</span></div>
<div style="font-size:0.8rem; font-weight:700; color:#16A34A; margin-top:4px;">▼ {abs(curt_delta):.1f} MWh</div>
</div>
<div class="gp-metric-card">
<div style="font-size:0.75rem; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Baseline Overloads</div>
<div style="font-size:1.8rem; font-weight:800; color:#0F172A;">{baseline_oload}</div>
</div>
<div class="gp-metric-card">
<div style="font-size:0.75rem; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Proposed Overloads</div>
<div style="font-size:1.8rem; font-weight:800; color:#0F172A;">{optimized_oload}</div>
<div style="font-size:0.8rem; font-weight:700; color:#16A34A; margin-top:4px;">{'▼' if oload_delta < 0 else ''}{'-' if oload_delta == 0 else ''} {abs(oload_delta)}</div>
</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 6 — OPERATOR DECISION (Operator Brief)
# ═══════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("""<div style="font-size:0.65rem; color:#3b6080; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:14px;">
Operator Decision — Situational Summary &amp; Action Recommendation
</div>""", unsafe_allow_html=True)

    sim6 = context['simulation']
    opt6 = context['optimization']

    # ── Decision banner ──────────────────────────────────────────
    if flag == 'GREEN':
        st.markdown(f"""<div class="gp-status-indicator gp-status-GREEN">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">●</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">System Status: Normal Operation</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">{explanation}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
    elif flag == 'YELLOW':
        st.markdown(f"""<div class="gp-status-indicator gp-status-YELLOW">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">●</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">System Status: Elevated — Operator Review Recommended</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">{explanation}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)
    elif flag == 'RED':
        st.markdown(f"""<div class="gp-status-indicator gp-status-RED">
<div style="display:flex; align-items:center; gap:16px;">
<div class="gp-status-icon" style="font-size:2rem;">⚠</div>
<div>
<div style="font-size:1.2rem; font-weight:700; color:#212529; letter-spacing:0.05em; text-transform:uppercase;">System Status: Action Validation Failed — Operator Approval Required</div>
<div style="font-size:0.9rem; color:#6C757D; margin-top:4px;">{explanation}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

    # ── 4-column brief ───────────────────────────────────────────
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        st.markdown(f"""<div class="gp-brief-section">
<div class="gp-brief-section-title">Current State</div>
<div class="gp-brief-row"><span class="gp-brief-key">Load</span><span class="gp-brief-val">{context['current_state']['demand_mw']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Renewables</span><span class="gp-brief-val">{context['current_state']['renewable_mw']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Transmission</span><span class="gp-brief-val">{context['current_state']['transmission_utilization_pct']*100:.1f}%</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Curtailment</span><span class="gp-brief-val">{context['current_state']['curtailment_mw']:.1f} MW</span></div>
</div>""", unsafe_allow_html=True)

    with b2:
        tr6 = context['grid_forecast']['transmission_risk']
        tr6_c = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#f97316", "CRITICAL": "#ef4444"}.get(tr6, "#8a9bb0")
        st.markdown(f"""<div class="gp-brief-section">
<div class="gp-brief-section-title">Next 60 Minutes</div>
<div class="gp-brief-row"><span class="gp-brief-key">Predicted Load</span><span class="gp-brief-val">{context['demand_forecast']['predicted_demand_60m']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Predicted Renewables</span><span class="gp-brief-val">{context['renewable_forecast']['renewable_60m']:.1f} MW</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Grid Risk</span><span class="gp-brief-val" style="color:{tr6_c};">{tr6}</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Curtailment Prob</span><span class="gp-brief-val">{context['grid_forecast']['curtailment_probability']:.0%}</span></div>
</div>""", unsafe_allow_html=True)

    with b3:
        action_mw6 = opt6['action_mw']
        if action_mw6 > 0:
            action_html = f"""<div class="gp-brief-row"><span class="gp-brief-key">Action</span><span class="gp-brief-val">{opt6['action']}</span></div>
            <div class="gp-brief-row"><span class="gp-brief-key">Resource</span><span class="gp-brief-val">{opt6['resource_type']}</span></div>
            <div class="gp-brief-row"><span class="gp-brief-key">Magnitude</span><span class="gp-brief-val" style="color:#0D6EFD;">{action_mw6:.1f} MW</span></div>
            <div class="gp-brief-row"><span class="gp-brief-key">Reason</span><span class="gp-brief-val" style="font-size:0.7rem;">{opt6['reason']}</span></div>"""
        else:
            action_html = """<div style="padding:10px 0; color:#22c55e; font-size:0.78rem; font-weight:600;">No action required.<br><span style="color:#3a5a3a; font-weight:400; font-size:0.72rem;">Grid conditions within normal parameters.</span></div>"""
        st.markdown(f"""<div class="gp-brief-section">
<div class="gp-brief-section-title">Recommended Action</div>
{action_html}
</div>""", unsafe_allow_html=True)

    with b4:
        adv6 = sim6['adverse_counterfactual']
        if adv6:
            val_color = "#ef4444"
            val_label = "⚠ FAILED"
            val_body  = "Simulation shows adverse outcomes. Do not execute."
        else:
            val_color = "#22c55e"
            val_label = "✓ PASSED"
            val_body  = "Action produces acceptable simulation outcomes."
        st.markdown(f"""<div class="gp-brief-section">
<div class="gp-brief-section-title">Action Validation</div>
<div style="font-size:1.2rem; font-weight:700; color:{val_color}; margin:8px 0;">{val_label}</div>
<div class="gp-brief-row"><span class="gp-brief-key">Baseline Curtailment</span><span class="gp-brief-val">{sim6['baseline_curtailment_mwh']:.1f} MWh</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Proposed Curtailment</span><span class="gp-brief-val">{sim6['optimized_curtailment_mwh']:.1f} MWh</span></div>
<div class="gp-brief-row"><span class="gp-brief-key">Overload Intervals</span><span class="gp-brief-val">{sim6['baseline_overload_intervals']} → {sim6['optimized_overload_intervals']}</span></div>
<div style="font-size:0.72rem; color:#4e6070; margin-top:6px;">{val_body}</div>
</div>""", unsafe_allow_html=True)

    # Asset alerts summary
    if context['asset_alerts']:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:0.65rem; color:#3b6080; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:8px;">Asset Alerts</div>""", unsafe_allow_html=True)
        for alert in context['asset_alerts']:
            a_status = alert['status']
            a_color  = "#ef4444" if a_status == "CRITICAL" else "#f59e0b"
            st.markdown(f"""<div style="background:#0e1620; border:1px solid {a_color}; border-left:3px solid {a_color}; border-radius:3px; padding:10px 14px; margin-bottom:6px; font-size:0.78rem;">
<span style="color:{a_color}; font-weight:700;">{a_status}</span>
<span style="color:#8a9bb0; margin-left:10px;">{alert['asset_id']}</span>
<span style="color:#5a7080; margin-left:10px; font-size:0.72rem;">{alert.get('root_cause','—')}</span>
<span style="color:#3a5060; margin-left:10px; font-size:0.72rem;">Confidence: {alert.get('confidence','—')}</span>
</div>""", unsafe_allow_html=True)

    # Adverse approval requirement (large)
    if sim6['adverse_counterfactual']:
        st.markdown(f"""<div class="gp-approval-required">
<div class="gp-approval-title"> Operator Review Required — Do Not Execute Without Approval</div>
<div class="gp-approval-body">
The counterfactual simulation indicates that the recommended action produces worse physical outcomes
than the no-action baseline. This recommendation has failed the action validation test.<br><br>
GridPulse does not automatically execute grid actions. This system supports human decision-making.
The operator must review and approve any action explicitly.<br><br>
<strong style="color:#ef4444;">Recommendation → Validation → Human Approval → Execution</strong>
</div>
</div>""", unsafe_allow_html=True)

    # Full deterministic brief (expandable)
    with st.expander("Full Deterministic Brief (Technical Detail)", expanded=False):
        md = render_deterministic_brief(context)
        st.markdown(md)


# =============================================================================
# MANUAL ENTRY (shown when sidebar button clicked)
# =============================================================================
if st.session_state.get('show_manual', False):
    st.markdown("""<div style="background-color:#0e1620; border:1px solid #1d2a38; border-top:3px solid #3b82d4; border-radius:3px; padding:20px 24px; margin-top:20px;">
<div style="font-size:0.65rem; color:#3b6080; text-transform:uppercase; letter-spacing:0.14em; margin-bottom:12px;">Manual Grid Data Entry</div>
<div style="font-size:0.8rem; color:#6a7f96;">
Enter real grid sensor readings. All values are physically validated before acceptance.
After submission, the full pipeline runs automatically and the dashboard reloads.
</div>
</div>""", unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.72rem; color:#3b6080; margin-top:8px;">Solar generation, transmission flow, and curtailment are derived automatically from your inputs.</div>', unsafe_allow_html=True)

    import importlib.util
    spec = importlib.util.spec_from_file_location("manual_entry", "scripts/manual_entry.py")
    me_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(me_mod)

    zones_list = data_dicts['demand']['zone_id'].unique().tolist()

    with st.form("manual_entry_form", clear_on_submit=False):

        st.markdown("**Zone**")
        me_zone = st.selectbox("Zone", zones_list, key="me_zone",
                               help="Which grid zone this reading applies to.")

        st.markdown("**Demand & Load**")
        col_a, col_b = st.columns(2)
        me_demand = col_a.number_input(
            "Demand (MW)", min_value=100.0, max_value=5000.0, value=2000.0, step=10.0,
            help="Total zone load. Typical: 1000-3500 MW.")
        me_reserve = col_b.number_input(
            "Reserve Margin (%)", min_value=0.0, max_value=60.0, value=15.0, step=0.5,
            help="Healthy grid: 10-20%.")

        st.markdown("**Weather**")
        col_c, col_d, col_e = st.columns(3)
        me_temp = col_c.number_input(
            "Temperature (°C)", min_value=-30.0, max_value=55.0, value=18.0, step=0.5,
            help="Ambient temperature. Range: -30 to 55 °C.")
        me_humidity = col_d.number_input(
            "Humidity (%)", min_value=0.0, max_value=100.0, value=65.0, step=1.0)
        me_wind = col_e.number_input(
            "Wind Speed (m/s)", min_value=0.0, max_value=25.0, value=6.0, step=0.1,
            help="Turbine cut-out at 25 m/s.")

        col_f, col_g = st.columns(2)
        me_irr = col_f.number_input(
            "Solar Irradiance (W/m²)", min_value=0.0, max_value=1200.0, value=0.0, step=10.0,
            help="0 at night. Max ~1000 W/m² in full sun.")
        me_cloud = col_g.number_input(
            "Cloud Cover (%)", min_value=0.0, max_value=100.0, value=70.0, step=1.0,
            help="High cloud cover + high irradiance is physically inconsistent.")

        st.markdown("**Battery & Grid**")
        col_h, col_i = st.columns(2)
        me_soc = col_h.number_input(
            "Battery SOC (%)", min_value=5.0, max_value=100.0, value=50.0, step=1.0,
            help="Safe range: 10-90%.")
        me_freq = col_i.number_input(
            "Grid Frequency (Hz)", min_value=49.0, max_value=51.0, value=50.0, step=0.01,
            help="Nominal = 50 Hz. Danger if < 49.5 or > 50.5 Hz.")

        st.markdown("**Event Flags**")
        me_spike = st.checkbox(
            "Mark as Demand Spike Event",
            help="Tick if this reading is an abnormal demand surge.")
        st.caption("Curtailment event flag is derived automatically.")

        submitted = st.form_submit_button(
            "Submit & Run Pipeline", type="primary", use_container_width=True)

    if submitted:
        entry = {
            'zone_id': me_zone, 'demand_mw': me_demand,
            'temperature_c': me_temp, 'humidity_pct': me_humidity,
            'wind_speed_ms': me_wind, 'irradiance_wm2': me_irr,
            'cloud_cover_pct': me_cloud, 'battery_soc_pct': me_soc,
            'grid_frequency_hz': me_freq, 'reserve_margin_pct': me_reserve,
            'demand_spike': me_spike,
        }

        with st.spinner("Validating entry against physical constraints..."):
            result = me_mod.append_manual_entry(entry)

        if not result['success']:
            st.error("Validation failed — entry rejected.")
            for err in result['errors']:
                st.markdown(f"- {err}")
            st.warning("Please correct the values above and resubmit.")
        else:
            d = result['derived']
            st.success(f"Entry accepted for timestamp: `{result['timestamp']}`")
            st.markdown("**Derived values computed from your inputs:**")
            dc1, dc2, dc3, dc4 = st.columns(4)
            dc1.metric("Solar Generation", f"{d['solar_generation_mw']:.1f} MW")
            dc2.metric("Wind Generation",  f"{d['wind_generation_mw']:.1f} MW")
            dc3.metric("Curtailment",      f"{d['curtailment_mw']:.1f} MW")
            dc4.metric("TX Utilization",
                       f"{d['utilization_pct']:.1f}%",
                       f"{d['transmission_flow_mw']:.0f}/{d['transmission_capacity_mw']} MW")

            st.markdown("---")
            st.markdown("Running full pipeline on your data...")
            PIPELINE_STEPS = [
                ("src/features.py",             "PATH 2 - Feature Engineering"),
                ("src/demand_forecast.py",       "PATH 3 - Demand Spike Prediction"),
                ("src/renewable_forecast.py",    "PATH 4 - Renewable Forecast"),
                ("src/asset_anomaly.py",         "PATH 5 - Asset Anomaly Detection"),
                ("src/root_cause.py",            "PATH 6 - Root Cause Analysis"),
                ("src/grid_risk.py",             "PATH 7 - Grid Risk Prediction"),
                ("src/optimizer.py",             "PATH 8 - Optimization Actions"),
                ("src/baseline_vs_optimized.py", "PATH 9 - Simulation"),
                ("src/operator_brief.py",        "PATH 10 - Operator Brief"),
            ]
            log2   = st.empty()
            lines2 = []
            pb2    = st.progress(0)
            stat2  = st.empty()
            all_ok = True
            for idx, (script, label) in enumerate(PIPELINE_STEPS):
                pb2.progress(int(idx / len(PIPELINE_STEPS) * 100))
                stat2.markdown(f"**Running:** `{label}`")
                lines2.append(f"Running {label}...")
                log2.code("\n".join(lines2), language="bash")
                t0  = time.time()
                res = subprocess.run([sys.executable, script], capture_output=True, text=True)
                elapsed = time.time() - t0
                if res.returncode == 0:
                    lines2[-1] = f"OK  {label} ({elapsed:.1f}s)"
                else:
                    lines2[-1] = f"ERR {label} ({elapsed:.1f}s)"
                    for e in res.stderr.strip().split("\n")[-3:]:
                        lines2.append(f"    {e}")
                    all_ok = False
                log2.code("\n".join(lines2), language="bash")
            pb2.progress(100)
            if all_ok:
                stat2.markdown("### Pipeline complete. Reloading dashboard...")
                time.sleep(1.2)
                st.cache_data.clear()
                st.rerun()
            else:
                stat2.markdown("### Pipeline finished with errors.")

# ── Footer ────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:30px; padding-top:12px; border-top:1px solid #1d2a38; text-align:center; font-size:0.65rem; color:#2e4055;">
GRIDPULSE &nbsp;·&nbsp; Grid Operations Intelligence &nbsp;·&nbsp;
Forecast → Detect → Optimize → Simulate → Human Decision &nbsp;·&nbsp;
<span style="color:#1e3048;">Decision-support only. Recommendations are not automatically executed.</span>
</div>
""", unsafe_allow_html=True)
