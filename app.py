import os

import pandas as pd
import streamlit as st

from ai_engine import (
    BUDGET_CHOICES,
    PRIORITY_CHOICES,
    PROBLEM_CHOICES,
    STRESS_CHOICES,
    generate_scenarios,
    generate_stress_test,
    get_ripple_effects,
)

st.set_page_config(page_title="Echoes of Tomorrow", page_icon="🌍", layout="wide")

live_ai_enabled = bool(os.getenv("OPENAI_API_KEY"))
status_text = "Live AI Configured" if live_ai_enabled else "Demo Mode"
status_class = "status-live" if live_ai_enabled else "status-demo"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --bg: #050b18;
        --bg-soft: #0a1224;
        --panel: rgba(12, 18, 32, 0.72);
        --panel-strong: rgba(15, 24, 41, 0.92);
        --panel-alt: rgba(18, 28, 48, 0.86);
        --line: rgba(126, 184, 255, 0.25);
        --text: #eaf3ff;
        --muted: #9bb3d1;
        --cyan: #71e7ff;
        --blue: #4ea1ff;
        --violet: #9a7dff;
        --magenta: #ff5bcf;
        --green: #7af5b4;
        --shadow: rgba(64, 143, 255, 0.32);
    }

    html {
        scroll-behavior: smooth;
    }

    @media (prefers-reduced-motion: reduce) {
        html { scroll-behavior: auto; }
        * { animation: none !important; transition: none !important; }
    }

    .stApp {
        background:
            radial-gradient(1px 1px at 12% 18%, rgba(220, 241, 255, 0.55) 0, transparent 1.5px),
            radial-gradient(1px 1px at 78% 12%, rgba(220, 241, 255, 0.45) 0, transparent 1.5px),
            radial-gradient(1px 1px at 34% 62%, rgba(220, 241, 255, 0.35) 0, transparent 1.5px),
            radial-gradient(1px 1px at 88% 74%, rgba(220, 241, 255, 0.4) 0, transparent 1.5px),
            radial-gradient(circle at 76% 27%, rgba(46, 195, 255, 0.16), transparent 28%),
            radial-gradient(circle at top left, rgba(97, 125, 255, 0.22), transparent 32%),
            radial-gradient(circle at bottom right, rgba(255, 91, 207, 0.16), transparent 28%),
            linear-gradient(180deg, #040b16 0%, #050b18 28%, #040c17 100%);
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
    }

    h1, h2, h3, .brand-text { font-family: 'Space Grotesk', sans-serif; }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 4rem;
        max-width: 1320px;
    }

    .topbar {
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        background: rgba(7, 13, 25, 0.72);
        border: 1px solid var(--line);
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.9rem 1.1rem;
        margin: 0.7rem 0 1.4rem;
        box-shadow: 0 16px 40px rgba(4, 12, 22, 0.45);
        position: sticky;
        top: 10px;
        z-index: 99;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        min-width: 240px;
    }

    .brand-mark {
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, rgba(113, 231, 255, 0.25), rgba(154, 125, 255, 0.3));
        border: 1px solid rgba(113, 231, 255, 0.4);
        border-radius: 12px;
        box-shadow: 0 0 24px rgba(88, 177, 255, 0.42);
        font-weight: 800;
        color: var(--text);
        letter-spacing: 0.08em;
    }

    .brand-text {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        color: #edf5ff;
        white-space: nowrap;
    }

    .brand-text span {
        background: linear-gradient(90deg, var(--cyan), var(--violet));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .nav-links {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    .nav-links a {
        color: rgba(234, 243, 255, 0.8);
        text-decoration: none;
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        transition: color 0.2s ease;
    }

    .nav-links a:hover {
        color: var(--cyan);
    }

    .status-pill {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.5rem 0.85rem;
        border-radius: 99px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255,255,255,0.02);
        color: var(--text);
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        white-space: nowrap;
    }

    .status-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 16px currentColor;
    }

    .status-live {
        color: var(--green);
        border-color: rgba(122, 245, 180, 0.25);
        background: rgba(122, 245, 180, 0.06);
    }

    .status-demo {
        color: #ffc857;
        border-color: rgba(255, 200, 87, 0.25);
        background: rgba(255, 200, 87, 0.06);
    }

    .hero-shell {
        position: relative;
        margin-top: 1rem;
        padding: 2.4rem 0 1rem;
    }

    .hero-row {
        display: flex;
        align-items: center;
        gap: 2rem;
        min-height: 620px;
    }

    .hero-copy {
        padding: 1.2rem 0 1rem;
        max-width: 650px;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.5rem 0.9rem;
        border-radius: 999px;
        background: rgba(113, 231, 255, 0.08);
        border: 1px solid rgba(113, 231, 255, 0.18);
        color: var(--cyan);
        font-size: 0.72rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        margin-bottom: 1.4rem;
    }

    h1 {
        font-size: 4.75rem;
        line-height: 0.98;
        margin: 0;
        letter-spacing: 0;
        font-weight: 800;
        color: white;
    }

    .gradient-text {
        display: block;
        background: linear-gradient(90deg, var(--cyan) 0%, #8dbdff 18%, #b3a5ff 38%, #d38aff 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .hero-subtitle {
        max-width: 560px;
        margin-top: 1.2rem;
        font-size: 1.1rem;
        line-height: 1.75;
        color: rgba(234, 243, 255, 0.76);
    }

    .hero-actions {
        display: flex;
        gap: 1rem;
        margin-top: 2.2rem;
        align-items: center;
        flex-wrap: wrap;
    }

    .primary-btn, .secondary-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.95rem 1.35rem;
        border-radius: 14px;
        text-decoration: none;
        border: 1px solid rgba(158, 203, 255, 0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease; 
        cursor: pointer;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    .primary-btn {
        background: linear-gradient(90deg, var(--cyan), var(--violet), var(--magenta));
        color: #061521;
        box-shadow: 0 0 36px rgba(115, 141, 255, 0.32);
    }

    .primary-btn:hover, .secondary-btn:hover {
        transform: translateY(-2px);
    }

    .secondary-btn {
        background: rgba(15, 20, 30, 0.8);
        color: var(--text);
        border: 1px solid rgba(255,255,255,0.12);
    }

    .hero-visual {
        position: relative;
        min-height: 610px;
        display: flex;
        align-items: center;
        justify-content: center;
        isolation: isolate;
    }

    .orbital-stage {
        position: relative;
        width: min(620px, 100%);
        height: 590px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .orbital-stage::before {
        content: "";
        position: absolute;
        width: 76%;
        aspect-ratio: 1;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(43, 185, 255, 0.19), rgba(88, 94, 255, 0.09) 42%, transparent 72%);
        filter: blur(20px);
        z-index: -1;
    }

    .planet-glow {
        position: relative;
        width: min(390px, 68vw);
        aspect-ratio: 1;
        border-radius: 50%;
        background: radial-gradient(circle at 40% 35%, rgba(141, 234, 255, 0.95), rgba(57, 112, 255, 0.7) 24%, rgba(16, 41, 96, 0.55) 50%, rgba(5, 11, 18, 0.88) 74%);
        border: 1px solid rgba(148, 219, 255, 0.35);
        box-shadow:
            inset 0 0 28px rgba(115, 228, 255, 0.25),
            0 0 52px rgba(88, 136, 255, 0.36),
            0 0 90px rgba(151, 94, 255, 0.2);
        overflow: hidden;
    }

    .earth-image {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        object-position: center;
        border-radius: 50%;
        z-index: 1;
        filter: saturate(1.16) contrast(1.08) brightness(0.82);
        transform: scale(1.65);
    }

    .planet-glow::before,
    .planet-glow::after {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 50%;
    }

    .planet-glow::before {
        background: linear-gradient(120deg, rgba(133, 193, 255, 0.6), transparent 38%, rgba(191, 128, 255, 0.55) 60%, transparent 100%);
        transform: scale(1.15);
        z-index: 2;
        pointer-events: none;
    }

    .planet-glow::after {
        inset: 18% 15% 14% 18%;
        background: radial-gradient(circle at 35% 30%, rgba(224, 248, 255, 0.8), rgba(64, 123, 255, 0.42) 30%, transparent 70%);
        filter: blur(8px);
        opacity: 0.42;
        z-index: 3;
        pointer-events: none;
    }

    .ring {
        position: absolute;
        border: 1px solid rgba(124, 178, 255, 0.35);
        border-radius: 50%;
        transform: rotateX(72deg);
        box-shadow: 0 0 18px rgba(125, 191, 255, 0.2);
        pointer-events: none;
    }

    .ring.one { width: 420px; height: 220px; }
    .ring.two { width: 520px; height: 300px; border-color: rgba(159, 122, 255, 0.22); }
    .ring.three { width: 610px; height: 380px; border-color: rgba(95, 186, 255, 0.2); }

    .orbital-dot {
        position: absolute;
        width: 8px;
        height: 8px;
        background: var(--cyan);
        border-radius: 50%;
        box-shadow: 0 0 16px var(--cyan);
    }

    .dot-a { top: 18%; left: 52%; }
    .dot-b { bottom: 16%; right: 18%; background: var(--violet); box-shadow: 0 0 18px var(--violet); }
    .dot-c { top: 52%; left: 15%; background: var(--magenta); box-shadow: 0 0 18px var(--magenta); }

    .floating-tag {
        position: absolute;
        z-index: 4;
        display: flex;
        align-items: center;
        gap: 0.55rem;
        background: rgba(12, 22, 40, 0.62);
        border: 1px solid rgba(130, 180, 255, 0.24);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 10px;
        padding: 0.65rem 0.9rem;
        color: rgba(234,243,255,0.92);
        font-size: 0.76rem;
        letter-spacing: 0.05em;
        box-shadow: 0 20px 35px rgba(40, 70, 118, 0.18);
    }

    .tag-one { top: 18%; left: 8%; }
    .tag-two { top: 18%; right: 10%; }
    .tag-three { bottom: 18%; left: 10%; }
    .tag-four { bottom: 24%; right: 10%; }
    .tag-five { top: 52%; right: 8%; }

    .mini-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--cyan), var(--violet));
        box-shadow: 0 0 16px rgba(113, 231, 255, 0.8);
    }

    .feature-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin-top: 2.2rem;
        margin-bottom: 3.7rem;
    }

    .feature-box {
        background: linear-gradient(180deg, rgba(17,26,42,0.76), rgba(10,17,30,0.8));
        border: 1px solid rgba(124, 176, 255, 0.18);
        border-radius: 10px;
        padding: 1.1rem 1rem;
        box-shadow: 0 18px 32px rgba(5, 11, 19, 0.35);
        text-align: center;
    }

    .feature-box strong {
        display: block;
        color: var(--text);
        font-size: 1.18rem;
        margin-bottom: 0.25rem;
    }

    .feature-box span {
        color: rgba(234,243,255,0.7);
        font-size: 0.82rem;
        letter-spacing: 0.04em;
    }

    .section-wrap {
        padding-top: 1.4rem;
        padding-bottom: 1.9rem;
    }

    .section-header {
        align-items: end;
        margin-bottom: 1.2rem;
    }

    .section-header h2 {
        margin: 0;
        font-size: 2.4rem;
        letter-spacing: 0;
    }

    .section-header p {
        margin: 0.5rem 0 0;
        color: rgba(234,243,255,0.68);
        font-size: 1.02rem;
        max-width: 640px;
    }

    .challenge-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1.1rem;
        margin-top: 1.8rem;
    }

    .challenge-card {
        background: linear-gradient(180deg, rgba(18,28,48,0.9), rgba(12,18,32,0.78));
        border: 1px solid rgba(138, 185, 255, 0.18);
        border-radius: 20px;
        padding: 1rem;
        min-height: 230px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 18px 32px rgba(6, 10, 20, 0.3);
        position: relative;
        overflow: hidden;
    }

    div[class*="st-key-challenge_"] div.stButton > button {
        min-height: 96px !important;
        padding: 1rem 1.1rem !important;
        border: 1px solid rgba(117, 205, 255, 0.24) !important;
        border-radius: 10px !important;
        background: linear-gradient(145deg, rgba(18, 34, 57, 0.96), rgba(10, 18, 33, 0.92)) !important;
        color: #edf6ff !important;
        box-shadow: 0 12px 28px rgba(2, 8, 20, 0.28), inset 0 1px rgba(255,255,255,0.04) !important;
        text-align: left !important;
        justify-content: flex-start !important;
        transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease !important;
    }

    div[class*="st-key-challenge_"] div.stButton > button:hover {
        transform: translateY(-3px);
        border-color: rgba(113, 231, 255, 0.62) !important;
        box-shadow: 0 18px 34px rgba(45, 128, 255, 0.2), inset 0 1px rgba(255,255,255,0.08) !important;
    }

    div[class*="st-key-challenge_"] div.stButton > button p {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        line-height: 1.4;
    }

    .challenge-card::before {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 116%;
        background: linear-gradient(180deg, rgba(109, 176, 255, 0.14), transparent 45%);
        pointer-events: none;
    }

    .challenge-card:hover {
        transform: translateY(-6px);
        border-color: rgba(113, 231, 255, 0.38);
        box-shadow: 0 22px 40px rgba(80, 116, 255, 0.2);
    }

    .challenge-card .card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.8rem;
        position: relative;
        z-index: 1;
    }

    .challenge-icon {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        background: rgba(116, 159, 255, 0.12);
        border: 1px solid rgba(146, 202, 255, 0.18);
    }

    .challenge-arrow {
        color: var(--cyan);
        font-size: 1.4rem;
        font-weight: 700;
        opacity: 0.9;
    }

    .challenge-card h3 {
        margin: 0.85rem 0 0.4rem;
        font-size: 1.2rem;
        letter-spacing: -0.04em;
        position: relative;
        z-index: 1;
    }

    .challenge-card p {
        margin: 0;
        color: rgba(234,243,255,0.68);
        line-height: 1.6;
        font-size: 0.88rem;
        position: relative;
        z-index: 1;
    }

    .stButton > button {
        background: transparent !important;
        border: none !important;
        color: inherit !important;
        padding: 0 !important;
        width: 100% !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        font-size: inherit !important;
    }

    .stButton > button:hover {
        background: transparent !important;
    }

    .timeline {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1.2rem;
        margin-top: 2rem;
        position: relative;
    }

    .timeline::before {
        content: "";
        position: absolute;
        top: 38px;
        left: 8%;
        right: 8%;
        height: 2px;
        background: linear-gradient(90deg, rgba(113,231,255,0.1), rgba(113,231,255,0.7), rgba(154,125,255,0.7), rgba(255,91,207,0.15));
    }

    .step-card {
        position: relative;
        z-index: 1;
        background: rgba(15, 24, 40, 0.76);
        border: 1px solid rgba(122, 178, 255, 0.18);
        border-radius: 10px;
        padding: 1.2rem 1rem 1rem;
        min-height: 200px;
        box-shadow: 0 18px 30px rgba(6, 10, 20, 0.25);
    }

    .step-icon {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, rgba(113,231,255,0.2), rgba(154,125,255,0.18));
        border: 1px solid rgba(113,231,255,0.4);
        box-shadow: 0 0 26px rgba(104, 146, 255, 0.22);
        font-weight: 800;
        color: var(--cyan);
    }

    .step-card h3 {
        margin: 0 0 0.55rem;
        font-size: 1.18rem;
    }

    .step-card p {
        margin: 0;
        color: rgba(234,243,255,0.68);
        line-height: 1.6;
        font-size: 0.9rem;
    }

    .cta-box {
        margin-top: 2rem;
        padding: 3rem 1.5rem;
        border-radius: 14px;
        background:
            linear-gradient(135deg, rgba(15, 22, 36, 0.9), rgba(20, 30, 52, 0.8)),
            radial-gradient(circle at top left, rgba(117, 201, 255, 0.14), transparent 40%);
        border: 1px solid rgba(128, 177, 255, 0.2);
        text-align: center;
        box-shadow: 0 30px 60px rgba(4, 8, 16, 0.44);
    }

    .cta-box h2 {
        margin: 0;
        font-size: 2.8rem;
        letter-spacing: 0;
    }

    .cta-box p {
        margin: 0.7rem auto 0;
        max-width: 680px;
        color: rgba(234,243,255,0.72);
        font-size: 1.08rem;
        line-height: 1.7;
    }

    .cta-box .primary-btn {
        margin-top: 1.8rem;
    }

    .panel-box {
        background: rgba(12, 19, 31, 0.72);
        border: 1px solid rgba(120, 172, 255, 0.18);
        border-radius: 20px;
        padding: 1.25rem;
        box-shadow: 0 18px 38px rgba(6, 10, 18, 0.32);
    }

    .status-banner {
        margin-bottom: 1.2rem;
        color: rgba(234,243,255,0.8);
        font-size: 0.85rem;
    }

    .selection-note {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin-top: 0.8rem;
        padding: 0.8rem 1rem;
        border: 1px solid rgba(113, 231, 255, 0.2);
        border-radius: 10px;
        background: rgba(11, 24, 40, 0.72);
        color: rgba(234, 243, 255, 0.88);
    }

    .selection-note a {
        color: var(--cyan);
        text-decoration: none;
        white-space: nowrap;
    }

    .tiny-muted {
        font-size: 0.76rem;
        color: rgba(234,243,255,0.72);
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .app-form-box {
        margin-top: 2.2rem;
    }

    @media (max-width: 1100px) {
        .challenge-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .timeline { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .feature-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .hero-visual { min-height: 500px; margin-top: 1rem; }
        .orbital-stage { height: 500px; }
        .topbar { gap: 0.5rem; flex-wrap: wrap; justify-content: center; }
    }

    @media (max-width: 720px) {
        h1 { font-size: 3.1rem; }
        .hero-visual { min-height: 390px; }
        .orbital-stage { height: 390px; }
        .planet-glow { width: min(280px, 72vw); }
        .ring.one { width: 300px; height: 160px; }
        .ring.two { width: 360px; height: 210px; }
        .ring.three { width: 420px; height: 270px; }
        .floating-tag { padding: 0.5rem 0.65rem; font-size: 0.66rem; }
        .tag-one { left: 0; }
        .tag-two { right: 0; }
        .tag-three { left: 0; }
        .tag-four { right: 0; }
        .tag-five { right: 4%; }
        .brand-text { letter-spacing: 0.12em; font-size: 0.72rem; }
        .nav-links { gap: 0.75rem; }
        .challenge-grid, .feature-strip, .timeline { grid-template-columns: 1fr; }
        .section-header h2 { font-size: 1.9rem; }
        .selection-note { align-items: flex-start; flex-direction: column; }
        .cta-box { padding: 2.3rem 1rem; }
        .cta-box h2 { font-size: 2rem; }
        .hero-actions { flex-direction: column; align-items: stretch; }
        .primary-btn, .secondary-btn { width: 100%; }
        .hero-shell { padding-top: 4px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(f"""
<div class='topbar'>
  <div class='brand'>
    <div class='brand-mark'>E</div>
    <div class='brand-text'><span>ECHOES</span> OF TOMORROW</div>
  </div>
  <nav class='nav-links'>
    <a href='#home'>Home</a>
    <a href='#explore'>Explore</a>
    <a href='#how-it-works'>How It Works</a>
    <a href='#about'>About</a>
  </nav>
  <div class='status-pill {status_class}'><span class='status-dot'></span>{status_text}</div>
</div>
""", unsafe_allow_html=True)

if not live_ai_enabled:
    st.markdown(
        "<div class='status-banner'><strong>DEMO MODE</strong> Offline scenarios are illustrative decision-support examples, not live AI predictions.</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div id='home'></div>", unsafe_allow_html=True)

col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.markdown(
        """
        <div class='hero-copy'>
            <div class='eyebrow'>AI-POWERED FUTURE SIMULATION</div>
            <h1>TOMORROW<br><span class='gradient-text'>ISN'T WRITTEN YET.</span></h1>
            <div class='hero-subtitle'>Explore possible futures. Challenge assumptions. Make better decisions today.</div>
            <div class='hero-actions'>
                <a class='primary-btn' href='#explore'>Explore Possible Futures →</a>
                <a class='secondary-btn' href='#how-it-works'>How It Works</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    st.markdown(
        """
        <div class='hero-visual'>
            <div class='orbital-stage'>
                <div class='ring one'></div>
                <div class='ring two'></div>
                <div class='ring three'></div>
                <div class='planet-glow'>
                    <img class='earth-image' src='https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?auto=format&fit=crop&w=1100&q=90' alt='Earth viewed from space'>
                </div>
                <div class='orbital-dot dot-a'></div>
                <div class='orbital-dot dot-b'></div>
                <div class='orbital-dot dot-c'></div>
                <div class='floating-tag tag-one'><span class='mini-dot'></span> A Greener Planet</div>
                <div class='floating-tag tag-two'><span class='mini-dot'></span> Smarter Cities</div>
                <div class='floating-tag tag-three'><span class='mini-dot'></span> Clean Energy</div>
                <div class='floating-tag tag-four'><span class='mini-dot'></span> Stronger Communities</div>
                <div class='floating-tag tag-five'><span class='mini-dot'></span> Healthier Lives</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class='feature-strip'>
        <div class='feature-box'><strong>8+ Challenges</strong><span>Real-world problem classes</span></div>
        <div class='feature-box'><strong>3 Futures</strong><span>Immediate, collaborative, and long-term paths</span></div>
        <div class='feature-box'><strong>Ripple Effects</strong><span>Indirect consequences and system trade-offs</span></div>
        <div class='feature-box'><strong>Actionable Plans</strong><span>Clear next steps and assumptions</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div id='explore' class='section-wrap'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='section-header'>
        <h2>What future do you want to explore?</h2>
        <p>Choose a challenge and see how today's decisions can shape different tomorrows.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

challenge_cards = [
    {"title": "Climate & Environment", "problem": "Climate & Environmental Protection", "desc": "Model ecological pressure, resilience, and sustainability choices.", "icon": "🌍"},
    {"title": "Water Scarcity", "problem": "Water Scarcity & Conservation", "desc": "Test conservation strategies and scarcity planning.", "icon": "💧"},
    {"title": "Food Waste & Food Security", "problem": "Food Waste & Hunger", "desc": "Reduce waste while improving access and food security.", "icon": "🍲"},
    {"title": "Agriculture & Farmers", "problem": "Agriculture & Crop Sustainability", "desc": "Balance crop productivity, land use, and climate stress.", "icon": "🌾"},
    {"title": "Energy & Electricity", "problem": "Energy Conservation & Electricity Shortages", "desc": "Explore reliable, efficient energy under changing demand.", "icon": "⚡"},
    {"title": "Traffic & Smart Cities", "problem": "Traffic Congestion & Urban Planning", "desc": "Model urban mobility, congestion, and planning trade-offs.", "icon": "🚦"},
    {"title": "Disaster Preparedness", "problem": "Natural Disasters & Emergency Preparedness", "desc": "Stress-test emergency plans and community resilience.", "icon": "🌊"},
    {"title": "Education & Student Life", "problem": "Other Real-World Problem", "desc": "Explore the effects of policies on learning and wellbeing.", "icon": "🎓"},
]

challenge_cols = st.columns(4)
for index, card in enumerate(challenge_cards):
    with challenge_cols[index % 4]:
        button_key = f"challenge_{index}"
        selected = st.session_state.get("challenge_selectbox") == card["problem"]
        button_label = f"{card['icon']}  {card['title']}" + ("  ✓" if selected else "  →")
        if st.button(button_label, key=button_key, use_container_width=True):
            st.session_state.challenge_selectbox = card["problem"]
            st.session_state.selected_problem = card["problem"]
            st.session_state.challenge_selected = True
            st.rerun()
        st.caption(card["desc"])

if st.session_state.get("challenge_selected"):
    selected_title = next(
        card["title"]
        for card in challenge_cards
        if card["problem"] == st.session_state.selected_problem
    )
    st.markdown(
        f"<div class='selection-note'><span>{selected_title} is selected for your simulation.</span><a href='#scenario-form'>Continue to simulator ↓</a></div>",
        unsafe_allow_html=True,
    )

st.markdown("<div id='watch-demo'></div>", unsafe_allow_html=True)

st.markdown("<div id='how-it-works' class='section-wrap'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='section-header'>
        <h2>How it works</h2>
        <p>From a real-world challenge to a practical first step, with the assumptions visible along the way.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

steps = [
    ("1", "Choose a Challenge", "Pick the issue you want to model and the context behind it."),
    ("2", "Explore Scenarios", "Compare three realistic future paths with benefits, risks, and assumptions."),
    ("3", "See the Ripple Effects", "Understand the indirect consequences of each decision across other systems."),
    ("4", "Compare & Plan", "Stress-test assumptions and decide which direction fits your constraints."),
]

step_cols = st.columns(4)
for index, (number, title, desc) in enumerate(steps):
    with step_cols[index]:
        st.markdown(
            f"""
            <div class='step-card'>
                <div class='step-icon'>{number}</div>
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div id='about' class='section-wrap'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='cta-box'>
        <h2>Your Next Decision Could Change Tomorrow.</h2>
        <p>Don't just predict the future. Explore it.</p>
        <a class='primary-btn' href='#scenario-form'>Start Exploring Futures →</a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='app-form-box' id='scenario-form'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='status-banner'>
        <div class='tiny-muted'>Scenario simulator</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("scenario_form"):
    col1, col2 = st.columns(2)
    with col1:
        problem = st.selectbox(
            "Choose a real-world challenge",
            PROBLEM_CHOICES,
            key="challenge_selectbox",
        )
        budget = st.selectbox("Available budget", BUDGET_CHOICES, key="budget_selectbox")
    with col2:
        priority = st.selectbox("Main priority", PRIORITY_CHOICES, key="priority_selectbox")
        stress = st.selectbox("Unexpected change to stress-test", STRESS_CHOICES, key="stress_selectbox")

    situation = st.text_area(
        "Describe the situation",
        placeholder="Example: Our college canteen wastes around 20 kg of food every day. We want to reduce waste, help students, and keep costs low.",
        height=140,
        key="situation_text",
    )

    custom_stress = st.text_input(
        "Or describe another assumption you want to test",
        placeholder="Example: The number of people affected doubles and volunteer support drops by half.",
        key="custom_stress_text",
    )

    submitted = st.form_submit_button("Explore Possible Futures →", type="primary", use_container_width=True)

if submitted:
    if not situation.strip():
        st.warning("Please describe the situation before exploring scenarios.")
    else:
        scenario_stress = custom_stress.strip() if custom_stress.strip() else stress
        try:
            with st.spinner("Generating three possible futures..."):
                scenarios, source = generate_scenarios(
                    problem=problem,
                    situation=situation,
                    budget=budget,
                    priority=priority,
                    stress=scenario_stress,
                    include_metadata=True,
                )
        except RuntimeError as exc:
            st.error(str(exc))
            st.stop()
        st.session_state.scenarios = scenarios
        st.session_state.source = source

        if source == "offline-demo":
            st.warning(
                "DEMO MODE: No API key is configured. These offline scenarios are illustrative and are not live AI predictions."
            )
        elif source == "offline-demo-api-error":
            st.warning(
                "DEMO MODE: OpenAI could not complete the request, possibly because of quota or credit limits, network issues, or another API problem. Showing illustrative offline scenarios instead."
            )

        st.markdown("## 1) Three possible futures")
        for scenario in scenarios:
            with st.container(border=True):
                st.markdown(f"### {scenario['name']}")
                st.caption(scenario["comparison"])
                st.markdown("**Executive summary**")
                st.write(scenario["summary"])

                left_column, right_column = st.columns(2)
                with left_column:
                    st.markdown("**Key assumptions**")
                    st.write(scenario["assumptions"])
                    st.markdown("**Expected benefits**")
                    st.markdown(f"- {scenario['benefits']}")
                    st.markdown("**Short-term impacts**")
                    st.markdown(f"- {scenario['short_term_impacts']}")
                with right_column:
                    st.markdown("**Main risks**")
                    st.markdown(f"- {scenario['risks']}")
                    st.markdown("**Long-term impacts**")
                    st.markdown(f"- {scenario['long_term_impacts']}")

                st.markdown("**Affected stakeholders**")
                stakeholder_items = [
                    item.strip() for item in scenario["affected_stakeholders"].split(";") if item.strip()
                ]
                st.markdown("\n".join(f"- {item}" for item in stakeholder_items))
                st.markdown("**Possible unintended consequences**")
                st.write(scenario["unintended_consequences"])
                st.info(f"**Stress-test response:** {scenario['stress_test_response']}")
                st.markdown("**Practical recommendations**")
                st.write(scenario["practical_recommendations"])
                st.caption(f"Resource fit: {scenario['resources_required']}")

        comparison_rows = []
        for scenario in scenarios:
            comparison_rows.append(
                {
                    "Scenario": scenario["name"],
                    "Strategic difference": scenario["comparison"],
                    "Potential upside": scenario["benefits"],
                    "Main trade-off": scenario["risks"],
                    "Stress response": scenario["stress_test_response"],
                }
            )

        st.markdown("## 2) How the futures differ")
        st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

        st.markdown("## 3) Future stress test")
        stress_change = custom_stress.strip() if custom_stress.strip() else stress
        if stress_change and stress_change != "No unexpected change":
            try:
                with st.spinner("Reassessing the strategies under the new condition..."):
                    stress_result = generate_stress_test(
                        problem=problem,
                        situation=situation,
                        budget=budget,
                        priority=priority,
                        original_scenarios=scenarios,
                        stress_change=stress_change,
                    )

                st.write(f"**Stress test assumption:** {stress_change}")
                st.write(stress_result["summary"])
                if stress_result["source"] == "offline-demo":
                    st.info("DEMO MODE: The stress test is an offline illustrative assessment.")
                elif stress_result["source"] == "offline-demo-api-error":
                    st.warning(
                        "DEMO MODE: The live stress-test request failed. Showing an offline illustrative assessment instead."
                    )
                for item in stress_result["strategies"]:
                    with st.container(border=True):
                        st.markdown(f"### {item['name']}")
                        st.write("**Feasibility:**", item["feasibility"])
                        st.write("**Why it changes:**", item["reason"])
                        st.write("**New risks:**", item["new_risks"])
                        st.write("**Resources now required:**", item["required_resources"])
                        st.write("**Adaptations that could help:**", item["adaptations"])
                        st.write("**Trade-offs:**", item["tradeoffs"])
            except RuntimeError as exc:
                st.error(str(exc))
        else:
            st.info("No changed assumption was entered, so the stress test did not run.")

        st.markdown("## 4) Ripple effects")
        for effect in get_ripple_effects(problem):
            st.write(f"• {effect}")

        st.markdown("## 5) Decision reflection")
        st.write("**Challenge:**", problem)
        st.write("**Situation:**", situation)
        st.write("**Budget:**", budget)
        st.write("**Priority:**", priority)
        st.warning(
            "These scenarios are plausible decision-support tools, not guaranteed predictions of the future. Review local evidence and expert guidance before acting on them."
        )
        st.success(
            "Which strategy aligns best with your stated priority, and what would you test before committing to it?"
        )

st.divider()
st.caption(
    "Echoes of Tomorrow | Explore possible futures. Test assumptions. Make thoughtful decisions."
)