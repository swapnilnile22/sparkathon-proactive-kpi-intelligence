"""Shared palette + global CSS to match the NICE Command Center look
(light theme, Geist font, #126BCE primary, indigo→purple→pink gradient).
"""
from __future__ import annotations

import streamlit as st

# Palette (from the Command Center design system)
PRIMARY = "#126BCE"
PRIMARY_HOVER = "#0B5BC9"
INK = "#0B233D"        # very dark blue — headline text
TEXT = "#1F2937"       # body text
MUTED = "#6B7280"      # secondary text
BORDER = "#E5E7EB"
BORDER2 = "#D1D5DB"
PAGE_BG = "#F5F7F9"
CARD_BG = "#FFFFFF"
GRADIENT = "linear-gradient(77deg,#6366F1 18.3%,#A855F7 51.87%,#EC4899 85.44%)"
PANEL_TINT = "linear-gradient(90deg,rgba(18,107,206,0.10) 0%,rgba(134,48,232,0.10) 100%),#FFFFFF"

# Status
RISK_BG, RISK_FG = "#FEE2E2", "#991B1B"
OK_BG, OK_FG = "#DCFCE7", "#166534"

# Chart
HIST_LINE = INK
FC_LINE = PRIMARY
BREACH = "#DC2626"
GRID = BORDER

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {{ font-family:'Geist', sans-serif; }}
.stApp {{ background:{PAGE_BG}; }}
.block-container {{ padding-top:2.2rem; max-width:1250px; }}

/* Primary buttons (Investigate, etc.) */
.stButton>button {{
  background:{PRIMARY}; color:#fff; border:none; border-radius:8px;
  font-weight:600; padding:0.35rem 0.9rem;
}}
.stButton>button:hover {{ background:{PRIMARY_HOVER}; color:#fff; }}

/* Hero title with gradient */
.pki-title {{
  font-size:2.1rem; font-weight:700; letter-spacing:-0.015em; line-height:1.1;
  background:{GRADIENT}; -webkit-background-clip:text; background-clip:text;
  color:transparent; margin:0 0 4px 0;
}}
.pki-sub {{ color:#4B5563; font-size:0.95rem; margin-bottom:0.4rem; }}

/* KPI cards */
.pki-card {{
  border:1px solid {BORDER2}; border-radius:16px; background:{CARD_BG};
  padding:16px 16px 14px 16px; transition:box-shadow .2s ease; height:100%;
}}
.pki-card:hover {{ box-shadow:0 8px 20px -6px rgba(16,24,40,.15); }}
.pki-card.risk {{ border-color:{BREACH}; }}
.pki-name {{ font-size:0.8rem; color:{MUTED}; font-weight:500; }}
.pki-value {{ font-size:1.7rem; font-weight:700; color:{INK}; line-height:1.2; }}
.pki-unit {{ font-size:0.85rem; color:{MUTED}; font-weight:500; }}
.pki-target {{ font-size:0.72rem; color:{MUTED}; }}
.pki-spark {{ font-size:1.05rem; letter-spacing:1px; margin-top:6px; }}
.pki-badge {{
  display:inline-block; margin-top:10px; padding:3px 10px; border-radius:999px;
  font-size:0.72rem; font-weight:600;
}}
.pki-badge.risk {{ background:{RISK_BG}; color:{RISK_FG}; }}
.pki-badge.ok   {{ background:{OK_BG}; color:{OK_FG}; }}

/* AI insight panel (gradient border) */
.pki-panel-wrap {{ background:{GRADIENT}; border-radius:18px; padding:1px; margin-bottom:14px; }}
.pki-panel {{ background:{PANEL_TINT}; border-radius:17px; padding:16px 18px; }}
.pki-layer-title {{ font-size:1.02rem; font-weight:600; color:{INK}; margin:0 0 2px 0; }}

/* Action cards */
.pki-action {{
  border:1px solid {BORDER}; border-radius:12px; background:rgba(255,255,255,.75);
  padding:12px 14px; margin-bottom:8px;
}}
.pki-action b {{ color:{INK}; }}
.pki-action .imp {{ color:{MUTED}; font-size:0.82rem; }}
.pki-pill {{
  display:inline-block; border:1px solid #8f73e3; background:#fff; color:{INK};
  border-radius:8px; padding:2px 8px; font-size:0.72rem; font-weight:600; margin-top:6px;
}}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
