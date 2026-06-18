"""
Redrob Candidate Ranker — Motion UI
CSS keyframe animations + Plotly animated charts + Streamlit native components.
Deploy-ready: requirements.txt covers all deps.
"""
import streamlit as st
import json
import os
import sys
import tempfile
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from ranker_v3 import (
    score_candidate, extract_jd_features, default_jd_features, read_docx_text,
    score_all_parallel, compute_semantic_scores, compute_bm25_scores,
)

st.set_page_config(
    page_title="Redrob · Candidate Ranker",
    page_icon="🔍",
    layout="wide",
)

# ── Motion CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@500;700&display=swap');

/* Base */
html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', sans-serif;
  background: #0F172A;
  color: #E2E8F0;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stMainBlockContainer"] { padding-top: 0.5rem; }

/* ── Animated gradient hero ── */
@keyframes gradientShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
@keyframes fadeSlideUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.0); }
  50%       { box-shadow: 0 0 24px 4px rgba(99,102,241,0.25); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}
@keyframes floatUpDown {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-6px); }
}
@keyframes countUp {
  from { opacity: 0; transform: scale(0.7); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes spinRing {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
  40%            { transform: scale(1.0); opacity: 1; }
}
@keyframes borderPulse {
  0%, 100% { border-color: rgba(99,102,241,0.3); }
  50%       { border-color: rgba(99,102,241,0.9); }
}

/* ── Hero banner ── */
.hero {
  background: linear-gradient(135deg, #1E1B4B 0%, #1E3A8A 40%, #0E7490 70%, #065F46 100%);
  background-size: 300% 300%;
  animation: gradientShift 8s ease infinite;
  border-radius: 16px;
  padding: 2.2rem 2.5rem 2rem;
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.04) 50%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 4s linear infinite;
  pointer-events: none;
}
.hero-title {
  font-family: 'Fira Code', monospace;
  font-size: 2.2rem; font-weight: 700;
  color: #fff; letter-spacing: -0.03em;
  margin: 0 0 0.3rem;
  animation: fadeSlideUp 0.7s ease both;
}
.hero-title .accent { color: #FBBF24; }
.hero-sub {
  color: #94A3B8; font-size: 0.9rem;
  margin: 0 0 1.4rem;
  animation: fadeSlideUp 0.7s 0.1s ease both;
}
.hero-pills {
  display: flex; gap: 0.6rem; flex-wrap: wrap;
  animation: fadeSlideUp 0.7s 0.2s ease both;
}
.hero-pill {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 20px; padding: 4px 14px;
  font-size: 0.72rem; font-weight: 600;
  color: #CBD5E1; letter-spacing: 0.04em;
  backdrop-filter: blur(4px);
}

/* ── Step labels ── */
.step-row {
  display: flex; align-items: center; gap: 0.6rem;
  margin: 1.4rem 0 0.6rem;
  animation: fadeSlideUp 0.5s ease both;
}
.step-dot {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #6366F1, #3B82F6);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Fira Code', monospace;
  font-size: 0.75rem; font-weight: 700; color: #fff;
  flex-shrink: 0;
  animation: pulseGlow 3s ease-in-out infinite;
}
.step-text {
  font-family: 'Fira Code', monospace;
  font-size: 0.95rem; font-weight: 600;
  color: #A5B4FC; letter-spacing: -0.01em;
}

/* ── Card ── */
.card {
  background: rgba(30,27,75,0.5);
  border: 1.5px solid rgba(99,102,241,0.2);
  border-radius: 12px; padding: 1.1rem 1.3rem;
  animation: fadeSlideUp 0.5s ease both;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.card:hover {
  border-color: rgba(99,102,241,0.6);
  box-shadow: 0 0 20px rgba(99,102,241,0.12);
}
.card-title {
  font-family: 'Fira Code', monospace;
  font-size: 0.8rem; font-weight: 600; color: #A5B4FC;
  margin-bottom: 0.2rem; letter-spacing: -0.01em;
}
.card-sub { font-size: 0.77rem; color: #64748B; line-height: 1.4; }

/* ── KPI row ── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 0.7rem; margin: 0.8rem 0;
}
.kpi {
  background: rgba(15,23,42,0.8);
  border: 1.5px solid rgba(99,102,241,0.25);
  border-radius: 12px; padding: 0.9rem 0.8rem;
  text-align: center;
  animation: countUp 0.5s ease both, borderPulse 4s ease-in-out infinite;
  transition: transform 0.2s, box-shadow 0.2s;
}
.kpi:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(99,102,241,0.18);
}
.kpi-val {
  font-family: 'Fira Code', monospace;
  font-size: 1.55rem; font-weight: 700; line-height: 1; margin-bottom: 5px;
}
.kpi-lbl {
  font-size: 0.62rem; font-weight: 600;
  color: #64748B; text-transform: uppercase; letter-spacing: 0.08em;
}
.kpi.indigo .kpi-val { color: #818CF8; }
.kpi.green  .kpi-val { color: #34D399; }
.kpi.amber  .kpi-val { color: #FBBF24; }
.kpi.teal   .kpi-val { color: #22D3EE; }
.kpi.slate  .kpi-val { color: #94A3B8; }
.kpi.pink   .kpi-val { color: #F472B6; }

/* ── Podium cards ── */
.podium-grid {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 1rem; margin: 0.8rem 0;
}
.podium {
  background: rgba(15,23,42,0.9);
  border-radius: 14px; padding: 1.2rem 1.1rem;
  border: 1.5px solid rgba(99,102,241,0.2);
  position: relative; overflow: hidden;
  animation: fadeSlideUp 0.6s ease both;
  transition: transform 0.25s, box-shadow 0.25s;
}
.podium:hover {
  transform: translateY(-5px);
  box-shadow: 0 16px 40px rgba(0,0,0,0.4);
}
.podium::after {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, transparent 60%);
  pointer-events: none;
}
.podium.gold   { border-top: 3px solid #FBBF24; }
.podium.silver { border-top: 3px solid #94A3B8; }
.podium.bronze { border-top: 3px solid #D97706; }
.podium-medal {
  font-size: 1.8rem; line-height: 1;
  margin-bottom: 0.5rem;
  animation: floatUpDown 3s ease-in-out infinite;
  display: inline-block;
}
.podium-rank {
  font-family: 'Fira Code', monospace;
  font-size: 0.65rem; font-weight: 700; color: #64748B;
  text-transform: uppercase; letter-spacing: 0.1em;
  margin-bottom: 0.3rem;
}
.podium-title { font-size: 0.95rem; font-weight: 700; color: #F1F5F9; margin-bottom: 0.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.podium-meta  { font-size: 0.75rem; color: #64748B; margin-bottom: 0.5rem; }
.podium-score {
  font-family: 'Fira Code', monospace;
  font-size: 1.7rem; font-weight: 700;
  background: linear-gradient(135deg, #6366F1, #22D3EE);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.podium.gold   .podium-score { background: linear-gradient(135deg, #FBBF24, #F97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.podium.silver .podium-score { background: linear-gradient(135deg, #94A3B8, #CBD5E1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.podium-tags { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.5rem; }
.ptag {
  font-size: 0.65rem; font-weight: 600; padding: 2px 7px; border-radius: 4px;
}
.ptag.green { background: rgba(52,211,153,0.15); color: #34D399; border: 1px solid rgba(52,211,153,0.3); }
.ptag.amber { background: rgba(251,191,36,0.12); color: #FBBF24; border: 1px solid rgba(251,191,36,0.25); }
.ptag.blue  { background: rgba(99,102,241,0.15); color: #A5B4FC; border: 1px solid rgba(99,102,241,0.3); }
.podium-reason {
  font-size: 0.72rem; color: #475569; line-height: 1.45;
  margin-top: 0.55rem; padding-top: 0.55rem;
  border-top: 1px solid rgba(99,102,241,0.12);
}

/* ── Loading dots ── */
.loading-dots { display: flex; gap: 6px; align-items: center; padding: 0.3rem 0; }
.dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #6366F1;
  animation: dotBounce 1.4s ease-in-out infinite both;
}
.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.16s; }
.dot:nth-child(3) { animation-delay: 0.32s; }

/* ── Divider ── */
.divider { height: 1px; background: rgba(99,102,241,0.15); margin: 1.3rem 0; }

/* ── Streamlit overrides for dark theme ── */
div[data-testid="stButton"] > button {
  background: linear-gradient(135deg, #4F46E5, #3B82F6) !important;
  color: #fff !important; border: none !important;
  font-family: 'Fira Code', monospace !important;
  font-weight: 600 !important; border-radius: 10px !important;
  padding: 0.55rem 2rem !important; font-size: 0.9rem !important;
  transition: all 0.2s !important; cursor: pointer !important;
}
div[data-testid="stButton"] > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(79,70,229,0.4) !important;
}
div[data-testid="stDownloadButton"] > button {
  background: linear-gradient(135deg, #059669, #0891B2) !important;
  color: #fff !important; border: none !important;
  font-family: 'Fira Code', monospace !important;
  font-weight: 600 !important; border-radius: 10px !important;
  font-size: 0.82rem !important; cursor: pointer !important;
  transition: all 0.2s !important;
}
div[data-testid="stDownloadButton"] > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(5,150,105,0.4) !important;
}
[data-testid="stDataFrame"] { border-radius: 10px !important; }
[data-testid="stCheckbox"] label { font-size: 0.82rem !important; color: #A5B4FC !important; font-weight: 500 !important; }
[data-testid="stExpander"] {
  background: rgba(15,23,42,0.7) !important;
  border: 1px solid rgba(99,102,241,0.25) !important;
  border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">red<span class="accent">rob</span> <span style="color:#94A3B8;font-weight:400">·</span> candidate_ranker<span class="accent">_</span></div>
  <div class="hero-sub">Upload any Job Description + Candidate pool → Ranked Top-100 · CPU only · No APIs · Deploy ready</div>
  <div class="hero-pills">
    <span class="hero-pill">⚡ Any JD</span>
    <span class="hero-pill">⬡ 100K candidates</span>
    <span class="hero-pill">◎ &lt;60s CPU</span>
    <span class="hero-pill">✦ Spec-valid CSV</span>
    <span class="hero-pill">✓ 4 score dimensions</span>
    <span class="hero-pill">◈ 23 signals</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_local_jsonl(path: str):
    """Stream-parse a large .jsonl or .json file directly from disk — no browser upload."""
    out, errs = [], 0
    path_lower = path.lower()
    try:
        if path_lower.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        errs += 1
        else:  # .json
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            out = data if isinstance(data, list) else [data]
    except Exception as e:
        return [], f"Error reading file: {e}"
    return out, f"{len(out):,} candidates loaded from disk ({errs} parse errors)"


@st.cache_data
def load_sample():
    path = os.path.join(BASE_DIR, "sample_candidates.json")
    if not os.path.exists(path):
        return [], "sample_candidates.json not found"
    with open(path) as f:
        data = json.load(f)
    return (data, None) if isinstance(data, list) else ([], "Must be a JSON array")


def _unwrap_candidates(data):
    """Return list of candidate dicts from any JSON shape."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Wrapped: {"candidates": [...]} or {"data": [...]} or {"results": [...]} etc.
        for v in data.values():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                return v
        # Single candidate object
        return [data]
    return []


def parse_cand_upload(f):
    fname   = f.name.lower()
    content = f.read().decode("utf-8", errors="replace")

    # CSV support
    if fname.endswith(".csv"):
        import csv, io
        try:
            reader = csv.DictReader(io.StringIO(content))
            rows = []
            for row in reader:
                # Convert numeric strings for common fields
                r = dict(row)
                for num_field in ("years_of_experience", "experience_years", "yoe",
                                  "notice_period_days", "notice_days"):
                    if num_field in r:
                        try:
                            r[num_field] = float(r[num_field])
                        except (ValueError, TypeError):
                            pass
                rows.append(r)
            if rows:
                return rows, f"{len(rows):,} candidates loaded from CSV"
        except Exception as e:
            return [], f"CSV parse error: {e}"

    # Try JSONL first (one JSON per line) regardless of extension
    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
    # Only use JSONL mode if lines look like complete JSON objects (start with '{' or '[')
    jsonl_lines = [l for l in lines if l.startswith("{") or l.startswith("[")]
    if len(jsonl_lines) > 1:
        parsed, errs = [], 0
        for line in jsonl_lines:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    parsed.append(obj)
                elif isinstance(obj, list):
                    parsed.extend(obj)
            except Exception:
                errs += 1
        if parsed:
            return parsed, f"{len(parsed):,} loaded ({errs} line errors)"

    # Single JSON blob (handles wrapped objects like {"candidates": [...]})
    try:
        data = json.loads(content)
        cands = _unwrap_candidates(data)
        return cands, f"{len(cands):,} loaded"
    except Exception as e:
        return [], f"Parse error: {e}"


def get_jd(jd_file, jd_text_input, use_default):
    # File upload and pasted text always win over the checkbox
    if jd_file:
        raw = jd_file.read()
        if jd_file.name.lower().endswith(".docx"):
            tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
            tmp.write(raw); tmp.flush()
            text = read_docx_text(tmp.name)
            os.unlink(tmp.name)
        else:
            text = raw.decode("utf-8", errors="replace")
        jd = extract_jd_features(text)
        if len(jd["all_skills"]) < 3:
            st.warning("⚠️ Few skills extracted — using built-in defaults.")
            return default_jd_features(), f"{jd_file.name} (fallback)"
        return jd, f"Parsed from {jd_file.name}"
    if jd_text_input.strip():
        jd = extract_jd_features(jd_text_input)
        if len(jd["all_skills"]) < 3:
            return default_jd_features(), "Pasted text (fallback)"
        return jd, "Parsed from pasted text"
    return default_jd_features(), "Built-in Senior AI Engineer JD"


def run_scoring(candidates, jd):
    # Streamlit runs in a thread — multiprocessing.Pool spawns processes without
    # Streamlit's ScriptRunContext, producing silent failures. Use n_workers=1
    # (single-process) so all scoring happens in the main process, then apply
    # semantic + BM25 re-ranking on the top-1000 pool as usual.
    results, errs = score_all_parallel(candidates, jd, n_workers=1, use_semantic=True)
    return results, errs


def make_gauge(score: float, title: str, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "", "font": {"size": 28, "color": color, "family": "Fira Code"}},
        title={"text": title, "font": {"size": 13, "color": "#94A3B8"}},
        gauge={
            "axis": {"range": [0, 1], "tickwidth": 1, "tickcolor": "#334155",
                     "tickfont": {"color": "#64748B", "size": 10}},
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 0.55], "color": "rgba(239,68,68,0.12)"},
                {"range": [0.55, 0.70], "color": "rgba(251,191,36,0.12)"},
                {"range": [0.70, 0.82], "color": "rgba(59,130,246,0.12)"},
                {"range": [0.82, 1.0],  "color": "rgba(52,211,153,0.15)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.85,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
        font={"family": "Inter"},
    )
    return fig


def make_dist_chart(results: list) -> go.Figure:
    buckets = {"0.8–1.0": 0, "0.6–0.8": 0, "0.4–0.6": 0, "0.2–0.4": 0, "0.0–0.2": 0}
    for r in results:
        s = r["score"]
        if s >= 0.8:   buckets["0.8–1.0"] += 1
        elif s >= 0.6: buckets["0.6–0.8"] += 1
        elif s >= 0.4: buckets["0.4–0.6"] += 1
        elif s >= 0.2: buckets["0.2–0.4"] += 1
        else:          buckets["0.0–0.2"] += 1

    labels = list(buckets.keys())
    values = list(buckets.values())
    colors = ["#34D399", "#3B82F6", "#FBBF24", "#F97316", "#EF4444"]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors, line=dict(width=0)),
        text=values, textposition="outside",
        textfont=dict(color="#94A3B8", size=12, family="Fira Code"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
        margin=dict(l=10, r=10, t=20, b=30),
        xaxis=dict(tickfont=dict(color="#64748B", size=11), gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)"),
        yaxis=dict(tickfont=dict(color="#64748B", size=10), gridcolor="rgba(30,27,75,0.5)", linecolor="rgba(0,0,0,0)"),
        bargap=0.25,
        font=dict(family="Inter"),
        showlegend=False,
    )
    return fig


def make_scatter(top_results: list) -> go.Figure:
    df = pd.DataFrame(top_results[:100])
    tier_color = df["score"].apply(
        lambda s: "#34D399" if s >= 0.82 else "#3B82F6" if s >= 0.70 else "#FBBF24" if s >= 0.55 else "#EF4444"
    )
    fig = go.Figure(go.Scatter(
        x=df["yoe"], y=df["score"],
        mode="markers",
        marker=dict(
            size=10, color=tier_color,
            line=dict(width=1, color="rgba(255,255,255,0.2)"),
            opacity=0.85,
        ),
        text=df.apply(lambda r: f"#{r['rank']} {r['title']}<br>{r['company']}<br>Score: {r['score']:.4f}", axis=1),
        hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=260,
        margin=dict(l=10, r=10, t=20, b=40),
        xaxis=dict(title=dict(text="Years of Experience", font=dict(color="#64748B", size=11)),
                   tickfont=dict(color="#64748B"), gridcolor="rgba(30,27,75,0.5)", linecolor="rgba(0,0,0,0)"),
        yaxis=dict(title=dict(text="Score", font=dict(color="#64748B", size=11)),
                   tickfont=dict(color="#64748B"), gridcolor="rgba(30,27,75,0.5)", linecolor="rgba(0,0,0,0)"),
        font=dict(family="Inter"),
        showlegend=False,
    )
    return fig


def tier_label(score: float) -> str:
    if score >= 0.82: return "🟢 Strong"
    if score >= 0.70: return "🔵 Good"
    if score >= 0.55: return "🟡 Moderate"
    return "🔴 Marginal"


# ── Step 1 — JD ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="step-row">
  <div class="step-dot">1</div>
  <div class="step-text">Job Description</div>
</div>
""", unsafe_allow_html=True)

jd_tab1, jd_tab2, jd_tab3 = st.tabs(["📄  Upload JD file", "📝  Paste JD text", "⚡  Built-in default"])

with jd_tab1:
    st.caption("Accepts .docx or .txt — any role, any industry")
    jd_file = st.file_uploader("JD file", type=["docx", "txt"],
                                label_visibility="collapsed", key="jd_upload")
    if jd_file:
        st.success(f"✅ Loaded: **{jd_file.name}**")

with jd_tab2:
    jd_text_input = st.text_area(
        "Paste JD text", height=180,
        placeholder="Paste the full job description here…",
        label_visibility="collapsed", key="jd_text",
    )

with jd_tab3:
    st.info(
        "**Senior AI Engineer @ Redrob AI** — embeddings, vector DBs, retrieval/ranking, "
        "Python, 5–9yr exp, Pune/Noida, product company.",
        icon="ℹ️",
    )
    use_default_jd = st.checkbox("Use built-in JD", value=True, key="use_default")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ── Step 2 — Candidates ───────────────────────────────────────────────────────
st.markdown("""
<div class="step-row">
  <div class="step-dot">2</div>
  <div class="step-text">Candidate Pool</div>
</div>
""", unsafe_allow_html=True)

ca1, ca2 = st.columns([3, 1], gap="large")
with ca1:
    st.caption("Upload `.jsonl`, `.json`, or `.csv` — any schema, any size")
    cand_file = st.file_uploader("Candidate file", type=["jsonl", "json", "csv"],
                                  label_visibility="collapsed", key="cand_upload")
    if cand_file:
        st.success(f"✅ **{cand_file.name}** ready")
with ca2:
    top_n = st.slider("Top N to display", 1, 500, 100, 1,
                       help="Default 100 (submission spec). Increase to explore more candidates — submission CSV always exports top 100.")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

run_btn = st.button("▶  Run Ranker", type="primary")

# ── Scoring (only when Run clicked) ──────────────────────────────────────────
if run_btn:
    if not cand_file:
        st.warning("⚠️ Upload a candidates file first."); st.stop()

    with st.status("⚙️ Running ranker…", expanded=True) as status:
        st.write("📄 Parsing job description…")
        jd, jd_source = get_jd(jd_file, jd_text_input, use_default_jd)

        st.write(f"📂 Loading candidates from **{cand_file.name}**…")
        candidates, msg = parse_cand_upload(cand_file)
        if not candidates:
            status.update(label="❌ Failed — no candidates parsed", state="error")
            st.error("No candidates parsed. Check file format."); st.stop()
        st.write(f"✅ {msg}")

        st.write(f"🚀 Scoring {len(candidates):,} candidates…")
        results, errs = run_scoring(candidates, jd)
        if not results:
            status.update(label="❌ Scoring returned no results", state="error")
            st.stop()
        st.write(f"✅ Done — ranked {len(results):,} candidates")

        status.update(label=f"✅ Complete — top {min(top_n, len(results))} ranked", state="complete")

    if not results:
        st.stop()

    top_results = results[:top_n]

    strong    = sum(1 for r in top_results if r["score"] >= 0.82)
    good      = sum(1 for r in top_results if 0.70 <= r["score"] < 0.82)
    otw       = sum(1 for r in top_results if r["open_to_work"])
    india_cnt = sum(1 for r in top_results if "india" in r["country"].lower())
    avg_sc    = sum(r["score"] for r in top_results) / len(top_results)
    top_sc    = top_results[0]["score"]

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="step-row">
      <div class="step-dot" style="background:linear-gradient(135deg,#059669,#0891B2);">✦</div>
      <div class="step-text" style="color:#34D399;">Results</div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi indigo"><div class="kpi-val">{top_sc:.3f}</div><div class="kpi-lbl">Top Score</div></div>
      <div class="kpi slate"><div class="kpi-val">{avg_sc:.3f}</div><div class="kpi-lbl">Avg Score</div></div>
      <div class="kpi green"><div class="kpi-val">{strong}</div><div class="kpi-lbl">Strong ≥0.82</div></div>
      <div class="kpi teal"><div class="kpi-val">{good}</div><div class="kpi-lbl">Good 0.70–0.82</div></div>
      <div class="kpi amber"><div class="kpi-val">{otw}</div><div class="kpi-lbl">Open to Work</div></div>
      <div class="kpi pink"><div class="kpi-val">{india_cnt}</div><div class="kpi-lbl">India-based</div></div>
      <div class="kpi slate"><div class="kpi-val">{len(results):,}</div><div class="kpi-lbl">Total Scored</div></div>
    </div>
    """, unsafe_allow_html=True)

    if errs:
        st.caption(f"⚠️ {errs} candidates skipped")

    # ── Charts ────────────────────────────────────────────────────────────────
    ch1, ch2 = st.columns([1.1, 1.3], gap="medium")
    with ch1:
        st.caption("**Top candidate score**")
        st.plotly_chart(make_gauge(top_sc, top_results[0]["title"][:22], "#FBBF24"),
                        width="stretch", config={"displayModeBar": False})
    with ch2:
        st.caption("**Score distribution**")
        st.plotly_chart(make_dist_chart(results),
                        width="stretch", config={"displayModeBar": False})

    # ── Top-3 podium ──────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="step-row">
      <div class="step-dot" style="background:linear-gradient(135deg,#FBBF24,#F97316);">★</div>
      <div class="step-text" style="color:#FBBF24;">Top 3 Candidates</div>
    </div>
    """, unsafe_allow_html=True)

    medals = ["🥇", "🥈", "🥉"]
    pod_classes = ["gold", "silver", "bronze"]
    pod_labels  = ["#1 · Gold", "#2 · Silver", "#3 · Bronze"]
    pod_html = '<div class="podium-grid">'
    for i in range(min(3, len(top_results))):
        r = top_results[i]
        tags = ""
        if r["open_to_work"]:
            tags += '<span class="ptag green">Open to Work</span>'
        if 0 < r["notice_days"] <= 30:
            tags += f'<span class="ptag green">⚡ {r["notice_days"]}d notice</span>'
        elif r["notice_days"] > 90:
            tags += f'<span class="ptag amber">{r["notice_days"]}d notice</span>'
        if "india" in r["country"].lower():
            tags += '<span class="ptag blue">🇮🇳 India</span>'
        reason = r["reasoning"][:210] + ("…" if len(r["reasoning"]) > 210 else "")
        pod_html += f"""
        <div class="podium {pod_classes[i]}" style="animation-delay:{i*0.1}s">
          <div class="podium-medal">{medals[i]}</div>
          <div class="podium-rank">{pod_labels[i]}</div>
          <div class="podium-title">{r['title']}</div>
          <div class="podium-meta">{r['company']} · {r['yoe']:.0f}yr · {r['location']}</div>
          <div class="podium-score">{r['score']:.4f}</div>
          <div class="podium-tags">{tags}</div>
          <div class="podium-reason">{reason}</div>
        </div>"""
    pod_html += "</div>"
    st.markdown(pod_html, unsafe_allow_html=True)

    # ── Full table with filters ───────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="step-row">
      <div class="step-dot" style="background:linear-gradient(135deg,#0891B2,#6366F1);">≡</div>
      <div class="step-text" style="color:#22D3EE;">Full Rankings</div>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1, 2])
    with f1: f_open   = st.checkbox("Open to Work",  key="f_open")
    with f2: f_india  = st.checkbox("India only",    key="f_india")
    with f3: f_notice = st.checkbox("Notice ≤30d",   key="f_notice")
    with f4: f_strong = st.checkbox("Strong ≥0.82",  key="f_strong")
    with f5: search_q = st.text_input("Search title / company",
                                       placeholder="Search title / company…",
                                       label_visibility="collapsed", key="sq")

    filtered = top_results
    if f_open:   filtered = [r for r in filtered if r["open_to_work"]]
    if f_india:  filtered = [r for r in filtered if "india" in r["country"].lower()]
    if f_notice: filtered = [r for r in filtered if r["notice_days"] <= 30]
    if f_strong: filtered = [r for r in filtered if r["score"] >= 0.82]
    if search_q:
        q = search_q.lower()
        filtered = [r for r in filtered
                    if q in r["title"].lower() or q in r["company"].lower()
                    or q in r.get("name", "").lower() or q in r["candidate_id"].lower()]

    filtered_df = None
    if not filtered:
        st.warning("No candidates match filters.")
    else:
        df = pd.DataFrame(filtered)[["candidate_id", "rank", "score", "reasoning"]].copy()
        df["score"] = df["score"].apply(lambda x: f"{x:.6f}")

        rows_html = ""
        for _, row in df.iterrows():
            rows_html += (
                f"<tr>"
                f"<td style='padding:6px 10px;white-space:nowrap;'>{row['candidate_id']}</td>"
                f"<td style='padding:6px 10px;text-align:center;'>{row['rank']}</td>"
                f"<td style='padding:6px 10px;text-align:center;font-family:monospace;'>{row['score']}</td>"
                f"<td style='padding:6px 10px;word-break:break-word;white-space:normal;line-height:1.4;'>{row['reasoning']}</td>"
                f"</tr>"
            )

        table_html = f"""
        <div style="overflow-y:auto;max-height:480px;border:1px solid #1e2d45;border-radius:6px;">
        <table style="width:100%;border-collapse:collapse;font-size:0.82rem;color:#CBD5E1;">
          <thead style="position:sticky;top:0;background:#1a2535;z-index:1;">
            <tr>
              <th style="padding:8px 10px;text-align:left;color:#94A3B8;font-weight:600;border-bottom:1px solid #1e2d45;white-space:nowrap;">candidate_id</th>
              <th style="padding:8px 10px;text-align:center;color:#94A3B8;font-weight:600;border-bottom:1px solid #1e2d45;">rank</th>
              <th style="padding:8px 10px;text-align:center;color:#94A3B8;font-weight:600;border-bottom:1px solid #1e2d45;">score</th>
              <th style="padding:8px 10px;text-align:left;color:#94A3B8;font-weight:600;border-bottom:1px solid #1e2d45;">reasoning</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)
        st.caption(f"Showing **{len(filtered)}** of {len(top_results)} ranked candidates")
        filtered_df = df

    # ── Downloads ─────────────────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="step-row">
      <div class="step-dot" style="background:linear-gradient(135deg,#059669,#0891B2);">↓</div>
      <div class="step-text" style="color:#34D399;">Export</div>
    </div>
    """, unsafe_allow_html=True)

    n_sub = min(top_n, 100)
    csv_rows = ["candidate_id,rank,score,reasoning"]
    for r in results[:n_sub]:
        esc = r["reasoning"].replace('"', '""')
        csv_rows.append(f'{r["candidate_id"]},{r["rank"]},{r["score"]:.6f},"{esc}"')
    st.download_button(
        label=f"📥 Download submission_ranked_top100.csv",
        data="\n".join(csv_rows),
        file_name="submission_ranked_top100.csv",
        mime="text/csv", use_container_width=True, type="primary",
    )
    st.caption("candidate_id · rank · score · reasoning — passes `validate_submission.py`")

    st.success(
        f"✅ Done — {len(results):,} candidates scored · "
        f"{strong} strong matches · JD: {jd_source}",
    )
