"use strict";
const pptxgen = require("pptxgenjs");

const C = {
  navy:      "1A2B4A",
  navyLight: "243660",
  coral:     "E8523A",
  teal:      "00A89D",
  ice:       "C8DDF0",
  white:     "FFFFFF",
  offwhite:  "F4F7FA",
  muted:     "7B94B5",
  dark:      "1A2B4A",
  mid:       "3A5070",
  green:     "2DB88C",
  amber:     "F5A623",
};
const FONT = "Calibri";
const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 45, opacity: 0.13
});

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Redrob Hackathon — Intelligent Candidate Ranker";

// ── Slide 1: Title ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.OVAL, { x: 7.8, y: -1.2, w: 3.5, h: 3.5,
    fill: { color: C.teal, transparency: 75 }, line: { color: C.teal, transparency: 80 }});
  s.addShape(pres.shapes.OVAL, { x: -0.8, y: 3.8, w: 2.5, h: 2.5,
    fill: { color: C.coral, transparency: 75 }, line: { color: C.coral, transparency: 80 }});

  s.addText("Intelligent Candidate Ranking", {
    x: 0.7, y: 1.0, w: 8.6, h: 1.1,
    fontSize: 38, bold: true, color: C.white, fontFace: FONT, align: "left", margin: 0
  });
  s.addText("Understanding who fits — not just who matches keywords", {
    x: 0.7, y: 2.15, w: 8.0, h: 0.55,
    fontSize: 18, color: C.ice, fontFace: FONT, italic: true, align: "left", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 2.85, w: 4.0, h: 0.04,
    fill: { color: C.coral }, line: { color: C.coral }});
  s.addText("Redrob Hackathon  ·  Senior AI Engineer  ·  100,000 Candidates", {
    x: 0.7, y: 3.1, w: 8.6, h: 0.4,
    fontSize: 13, color: C.muted, fontFace: FONT, align: "left", margin: 0
  });

  const stats = [
    ["100K", "Candidates\nRanked"],
    ["<35s",  "Runtime\n(CPU only)"],
    ["0",     "External\nAPIs"],
    ["100",   "Top candidates\nshortlisted"]
  ];
  stats.forEach(([val, label], i) => {
    const x = 0.7 + i * 2.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.8, w: 2.1, h: 1.4,
      fill: { color: C.navyLight }, rectRadius: 0.08, shadow: makeShadow() });
    s.addText(val, { x, y: 3.85, w: 2.1, h: 0.6,
      fontSize: 26, bold: true, color: C.coral, fontFace: FONT, align: "center", margin: 0 });
    s.addText(label, { x, y: 4.45, w: 2.1, h: 0.6,
      fontSize: 10, color: C.ice, fontFace: FONT, align: "center", margin: 0 });
  });
}

// ── Slide 2: Introduction — What & How ─────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Introduction: What This System Does", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.dark, fontFace: FONT, margin: 0
  });
  s.addText("A recruiter-grade ranking engine — no LLMs, no APIs, no GPU required.", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.35,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  // Pipeline steps
  const steps = [
    { num: "1", title: "Parse Job Description",
      desc: "Extract must-have skills, bonus skills, required YoE band, location preference, and seniority signals from JD text or DOCX." },
    { num: "2", title: "Stream Candidates",
      desc: "Read 100K candidates as a streaming JSONL — never loads full dataset into memory. Each record scored independently." },
    { num: "3", title: "Four-Dimension Score",
      desc: "Skill match (30%) + Career depth (35%) + Behavioral signals (20%) + Location fit (15%) × availability multiplier." },
    { num: "4", title: "Semantic Re-ranking",
      desc: "Top 1,000 pool re-ranked using BM25 + sentence-transformers cosine similarity against JD text for precision boost." },
    { num: "5", title: "Output & Validate",
      desc: "Emit top-100 CSV: candidate_id · rank · score · reasoning. Passes validate_submission.py with 0 errors." },
  ];

  steps.forEach((st, i) => {
    const y = 1.4 + i * 0.82;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y, w: 9.2, h: 0.72,
      fill: { color: C.white }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.OVAL, { x: 0.55, y: y+0.17, w: 0.38, h: 0.38,
      fill: { color: C.teal }, line: { color: C.teal }});
    s.addText(st.num, { x: 0.55, y: y+0.17, w: 0.38, h: 0.38,
      fontSize: 11, bold: true, color: C.white, fontFace: FONT, align: "center", valign: "middle", margin: 0 });
    s.addText(st.title, { x: 1.1, y: y+0.07, w: 3.2, h: 0.28,
      fontSize: 11, bold: true, color: C.dark, fontFace: FONT, margin: 0 });
    s.addText(st.desc, { x: 1.1, y: y+0.36, w: 8.2, h: 0.28,
      fontSize: 9.5, color: C.mid, fontFace: FONT, margin: 0 });
  });
}

// ── Slide 3: Requirements ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("System Requirements & Performance", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT, margin: 0
  });
  s.addText("Designed to run anywhere — laptop, server, or cloud free tier.", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.35,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  const reqs = [
    { icon: "⚡", label: "Speed",
      val: "< 35 seconds",
      desc: "100,000 candidates scored end-to-end on a standard laptop CPU. Parallel workers via concurrent.futures." },
    { icon: "🧠", label: "Memory",
      val: "< 400 MB RAM",
      desc: "Streaming JSONL reader — never loads full dataset. Top-1000 pool for semantic stage only." },
    { icon: "💻", label: "CPU Only",
      val: "No GPU needed",
      desc: "All scoring is pure NumPy / scikit-learn math. Sentence-transformers inference runs on CPU for re-ranking." },
    { icon: "📦", label: "Dependencies",
      val: "0 for CLI mode",
      desc: "ranker_v3.py uses stdlib only for core ranking. Streamlit UI adds pandas, plotly, sentence-transformers." },
    { icon: "🐍", label: "Python",
      val: "3.9 +",
      desc: "No version-specific APIs. Tested on 3.9, 3.11, 3.12. Works on macOS, Linux, Windows." },
    { icon: "✅", label: "Output",
      val: "100 rows · CSV",
      desc: "candidate_id, rank, score, reasoning — monotone scores, passes validate_submission.py with 0 errors." },
  ];

  const colX = [0.4, 5.1];
  reqs.forEach((r, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = colX[col];
    const y = 1.45 + row * 1.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.55, h: 1.18,
      fill: { color: C.navyLight }, rectRadius: 0.1 });
    s.addText(r.icon, { x: x+0.15, y: y+0.08, w: 0.55, h: 0.55,
      fontSize: 22, fontFace: FONT, align: "center", margin: 0 });
    s.addText(r.label, { x: x+0.75, y: y+0.1, w: 1.5, h: 0.28,
      fontSize: 10, bold: true, color: C.muted, fontFace: FONT, margin: 0 });
    s.addText(r.val, { x: x+0.75, y: y+0.36, w: 3.6, h: 0.3,
      fontSize: 14, bold: true, color: C.teal, fontFace: FONT, margin: 0 });
    s.addText(r.desc, { x: x+0.15, y: y+0.72, w: 4.3, h: 0.38,
      fontSize: 8.5, color: C.muted, fontFace: FONT, margin: 0 });
  });
}

// ── Slide 4: Challenges ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Challenges & How We Solved Them", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.dark, fontFace: FONT, margin: 0
  });
  s.addText("Real engineering problems that keyword rankers ignore entirely.", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.35,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  const challenges = [
    { num: "1", color: C.coral, title: "Schema Heterogeneity",
      problem: "Candidates use different field names, nested objects, missing values, mixed types.",
      solution: "Defensive getters with fallbacks. Normalise YoE, notice period, skills list at ingest." },
    { num: "2", color: C.amber, title: "Honeypot / Fake Profiles",
      problem: "~80 planted profiles with impossible skill combos, zeroed signals, salary inversions.",
      solution: "5 rule-based detectors fire before scoring. Flagged candidates get score = 0.0." },
    { num: "3", color: C.teal, title: "No LLM / No API Access",
      problem: "Cannot call GPT or any external service. Must infer seniority from raw text alone.",
      solution: "Keyword taxonomy of 40+ terms mapped to JD vocabulary. Career text regex for production evidence." },
    { num: "4", color: C.green, title: "Availability vs. Skill Trade-off",
      problem: "High-skill but inactive/unresponsive candidates should not dominate the list.",
      solution: "Multiplicative availability factor (0.45 + 0.55×avail) demotes unreachable candidates regardless of skill." },
    { num: "5", color: "8B5CF6", title: "Scale: 100K Candidates",
      problem: "Loading all 100K into memory and scoring serially would be too slow.",
      solution: "Streaming JSONL reader + concurrent.futures parallel scoring + top-1000 pool for semantic stage." },
  ];

  challenges.forEach((c, i) => {
    const y = 1.4 + i * 0.82;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y, w: 9.2, h: 0.72,
      fill: { color: C.white }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.OVAL, { x: 0.55, y: y+0.17, w: 0.38, h: 0.38,
      fill: { color: c.color }, line: { color: c.color }});
    s.addText(c.num, { x: 0.55, y: y+0.17, w: 0.38, h: 0.38,
      fontSize: 11, bold: true, color: C.white, fontFace: FONT, align: "center", valign: "middle", margin: 0 });
    s.addText(c.title, { x: 1.1, y: y+0.06, w: 8.5, h: 0.25,
      fontSize: 11, bold: true, color: C.dark, fontFace: FONT, margin: 0 });
    s.addText(`Problem: ${c.problem}`, { x: 1.1, y: y+0.33, w: 4.3, h: 0.32,
      fontSize: 8.8, color: C.coral, fontFace: FONT, margin: 0 });
    s.addText(`Solution: ${c.solution}`, { x: 5.5, y: y+0.33, w: 3.9, h: 0.32,
      fontSize: 8.8, color: C.green, fontFace: FONT, margin: 0 });
  });
}

// ── Slide 5: The Problem ────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("The Problem with Keyword Search", {
    x: 0.5, y: 0.3, w: 9.0, h: 0.7,
    fontSize: 30, bold: true, color: C.dark, fontFace: FONT, margin: 0
  });

  const cols = [
    {
      icon: "✗", iconColor: C.coral, head: "What keyword filters do",
      items: [
        "Match 'Pinecone' in skills → include",
        "Miss 'built hybrid search over 50M profiles' in career description",
        "Rank a Marketing Manager #1 because they listed 9 AI skills",
        "Ignore Search Eng. at Swiggy who never typed 'vector database'",
        "Ignore availability — inactive 11 months, 5% response rate"
      ]
    },
    {
      icon: "✓", iconColor: C.green, head: "What a great recruiter does",
      items: [
        "Reads career history for evidence of shipped systems",
        "Understands 'designed relevance labeling pipeline' = ranking",
        "Checks behavioral signals: active? responsive? available?",
        "Weights India/preferred city location appropriately",
        "Spots impossible profiles and keyword-stuffed honeypots"
      ]
    }
  ];

  cols.forEach((col, ci) => {
    const x = 0.5 + ci * 4.85;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.1, w: 4.5, h: 4.1,
      fill: { color: C.white }, rectRadius: 0.1, shadow: makeShadow() });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.1, w: 4.5, h: 0.65,
      fill: { color: col.iconColor }, rectRadius: 0.1, line: { color: col.iconColor }});
    s.addText(`${col.icon}  ${col.head}`, { x: x+0.1, y: 1.1, w: 4.3, h: 0.65,
      fontSize: 13, bold: true, color: C.white, fontFace: FONT, valign: "middle", margin: 0 });
    col.items.forEach((item, ii) => {
      s.addText(`• ${item}`, { x: x+0.15, y: 1.85 + ii*0.65, w: 4.2, h: 0.6,
        fontSize: 11, color: C.mid, fontFace: FONT, align: "left", margin: 0 });
    });
  });
}

// ── Slide 6: Architecture ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("Architecture: Four-Dimensional Scoring", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT, margin: 0
  });
  s.addText("Each dimension reads the candidate differently. No embeddings, no APIs — pure structured-data reasoning.", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.4,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  const dims = [
    { pct: "30%", label: "Skill Match",        color: C.teal,   desc: "JD-derived skill taxonomy vs. skills list\nMust-haves: embeddings, vector DB, ranking, Python\nBonus: LangChain, LLM fine-tuning, MLOps" },
    { pct: "35%", label: "Career Depth",       color: C.coral,  desc: "Text analysis of career descriptions\nEvidence of shipped retrieval/ranking systems\nProduct vs. services companies; YoE band" },
    { pct: "20%", label: "Behavioral Signals", color: C.amber,  desc: "Last active date, open-to-work flag\nRecruiter response rate, interview completion\nNotice period, GitHub activity" },
    { pct: "15%", label: "Location Fit",       color: C.green,  desc: "Pune/Noida → 1.0x; India Tier-1 → 0.9x\nIndia non-preferred → 0.78x\nNon-India willing to relocate → 0.55x" },
  ];

  dims.forEach((d, i) => {
    const x = 0.4 + i * 2.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 2.15, h: 3.7,
      fill: { color: C.navyLight }, rectRadius: 0.1 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 2.15, h: 0.75,
      fill: { color: d.color }, rectRadius: 0.1, line: { color: d.color }});
    s.addText(d.pct, { x, y: 1.52, w: 2.15, h: 0.45,
      fontSize: 22, bold: true, color: C.white, fontFace: FONT, align: "center", margin: 0 });
    s.addText(d.label, { x, y: 2.0, w: 2.15, h: 0.45,
      fontSize: 11.5, bold: true, color: C.ice, fontFace: FONT, align: "center", margin: 0 });
    s.addText(d.desc, { x: x+0.1, y: 2.5, w: 1.95, h: 2.6,
      fontSize: 9.5, color: C.muted, fontFace: FONT, align: "left", margin: 0 });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y: 5.15, w: 9.2, h: 0.33,
    fill: { color: "2A3F60" }, rectRadius: 0.07 });
  s.addText("× Availability Multiplier (0.45 + 0.55 × avail) — ensures unreachable candidates rank below active ones regardless of skill score",
    { x: 0.55, y: 5.15, w: 9.0, h: 0.33,
      fontSize: 10, color: C.ice, fontFace: FONT, align: "left", valign: "middle", margin: 0 });
}

// ── Slide 7: Career Analysis ────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Career Analysis: Reading for Production Evidence", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.dark, fontFace: FONT, margin: 0
  });
  s.addText("We don't ask 'what did they list?' — we ask 'what did they ship?'", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.35,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  const signals = [
    { label: "production_retrieval", color: C.teal, weight: "35%",
      kws: "retrieval · vector search · semantic search · embedding · elasticsearch · faiss · pinecone · bm25 · hybrid search",
      desc: "Found in job description text or title. Indicates candidate has built real search systems." },
    { label: "production_ranking", color: C.coral, weight: "35%",
      kws: "ranking · rerank · learning to rank · ltr · recommendation · discovery feed · lightgbm · ranking model",
      desc: "Evidence of shipped LTR/recommendation models, not just familiarity." },
    { label: "production_ml", color: C.amber, weight: "20%",
      kws: "production · deployed · shipped · a/b test · serving · latency · inference · real-time",
      desc: "2+ of these in description = likely deployed to real users, not just notebooks." },
    { label: "eval_framework", color: C.green, weight: "10%",
      kws: "ndcg · mrr · a/b test · offline eval · relevance label · recall@ · precision@ · online experiment",
      desc: "Knowing how to measure search quality is a senior signal. JD: 'painful if you haven't done this.'" },
  ];

  signals.forEach((sig, i) => {
    const y = 1.45 + i * 1.05;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y, w: 9.2, h: 0.92,
      fill: { color: C.white }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y, w: 0.08, h: 0.92,
      fill: { color: sig.color }, rectRadius: 0.04, line: { color: sig.color }});
    s.addText(sig.label, { x: 0.6, y: y+0.06, w: 2.2, h: 0.3,
      fontSize: 11, bold: true, color: C.dark, fontFace: FONT, margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 2.85, y: y+0.08, w: 0.45, h: 0.22,
      fill: { color: sig.color }, rectRadius: 0.04, line: { color: sig.color }});
    s.addText(sig.weight, { x: 2.85, y: y+0.08, w: 0.45, h: 0.22,
      fontSize: 8, bold: true, color: C.white, fontFace: FONT, align: "center", margin: 0 });
    s.addText(sig.kws, { x: 0.6, y: y+0.38, w: 5.5, h: 0.22,
      fontSize: 8.5, color: C.teal, fontFace: FONT, italic: true, margin: 0 });
    s.addText(sig.desc, { x: 6.3, y: y+0.1, w: 3.0, h: 0.72,
      fontSize: 9, color: C.mid, fontFace: FONT, margin: 0 });
  });
}

// ── Slide 8: Behavioral Availability ───────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("Behavioral Signals: Availability is a Multiplier", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT, margin: 0
  });
  s.addText("A 0.95-skill candidate inactive for 11 months ranks below an active 0.65-skill candidate.", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.35,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  const rows = [
    ["Last Active", "Availability Score", "With Open-to-Work"],
    ["≤ 30 days",   "1.00",               "1.00 (capped)"],
    ["31–90 days",  "0.87",               "0.97"],
    ["91–180 days", "0.72",               "0.81"],
    ["181–365 days","0.50",               "0.56"],
    ["> 365 days",  "0.28",               "0.31"],
  ];

  const colW = [2.5, 2.5, 2.5];
  const colX = [0.5, 3.1, 5.7];
  rows.forEach((row, ri) => {
    const y = 1.4 + ri * 0.52;
    const isHeader = ri === 0;
    row.forEach((cell, ci) => {
      s.addShape(pres.shapes.RECTANGLE, { x: colX[ci], y, w: colW[ci], h: 0.5,
        fill: { color: isHeader ? C.teal : (ri % 2 === 0 ? "2A3F60" : C.navyLight) },
        line: { color: "33507A" }});
      s.addText(cell, { x: colX[ci]+0.1, y, w: colW[ci]-0.2, h: 0.5,
        fontSize: isHeader ? 10 : 11, bold: isHeader,
        color: isHeader ? C.white : (cell.includes("1.00") ? C.green : cell.includes("0.28") || cell.includes("0.31") ? C.coral : C.ice),
        fontFace: FONT, valign: "middle", margin: 0 });
    });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 4.65, w: 9.0, h: 0.75,
    fill: { color: "2A3F60" }, rectRadius: 0.1 });
  s.addText("final_score = raw_score × (0.45 + 0.55 × availability)", {
    x: 0.7, y: 4.68, w: 8.6, h: 0.35,
    fontSize: 14, bold: true, color: C.coral, fontFace: "Courier New", margin: 0
  });
  s.addText("Response rate < 10% → further ×0.55 penalty  |  Response rate < 25% → ×0.75  |  Saved by ≥5 recruiters → ×1.03 bonus",
    { x: 0.7, y: 5.02, w: 8.6, h: 0.3,
      fontSize: 9, color: C.muted, fontFace: FONT, margin: 0 });
}

// ── Slide 9: Honeypot Detection ─────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Honeypot Detection: 5 Patterns", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.dark, fontFace: FONT, margin: 0
  });
  s.addText("~80 honeypots in 100K candidates. >10% in top 100 = disqualified. We detect them before scoring.", {
    x: 0.5, y: 0.95, w: 9.0, h: 0.35,
    fontSize: 13, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  const patterns = [
    { num: "1", title: "Expert skills, 0 months",
      signal: "7+ skills with proficiency=expert/advanced and duration_months=0",
      action: "Score → 0.0 (impossible real-world usage)" },
    { num: "2", title: "Non-tech title + AI skill flood",
      signal: "Marketing Manager / HR Manager title + 7+ core AI skills listed",
      action: "Score → 0.0 (keyword stuffing, not real background)" },
    { num: "3", title: "All behavioral signals zeroed",
      signal: "5+ signals = 0 (views, applications, connections, endorsements, searches) AND >15 skills",
      action: "Score → 0.0 (synthetically zeroed profile)" },
    { num: "4", title: "Salary min > salary max",
      signal: "expected_salary_range.min > expected_salary_range.max",
      action: "Score → 0.0 (logically impossible data)" },
    { num: "5", title: "YoE >> company age",
      signal: "Candidate claims more YoE than current company has existed + margin",
      action: "Score → 0.0 (temporal impossibility)" },
  ];

  patterns.forEach((p, i) => {
    const y = 1.4 + i * 0.82;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y, w: 9.2, h: 0.72,
      fill: { color: C.white }, rectRadius: 0.08, shadow: makeShadow() });
    s.addShape(pres.shapes.OVAL, { x: 0.55, y: y+0.17, w: 0.38, h: 0.38,
      fill: { color: C.coral }, line: { color: C.coral }});
    s.addText(p.num, { x: 0.55, y: y+0.17, w: 0.38, h: 0.38,
      fontSize: 11, bold: true, color: C.white, fontFace: FONT, align: "center", valign: "middle", margin: 0 });
    s.addText(p.title, { x: 1.1, y: y+0.07, w: 3.8, h: 0.28,
      fontSize: 11, bold: true, color: C.dark, fontFace: FONT, margin: 0 });
    s.addText(p.signal, { x: 1.1, y: y+0.36, w: 4.5, h: 0.28,
      fontSize: 9, color: C.mid, fontFace: FONT, margin: 0 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.8, y: y+0.15, w: 3.6, h: 0.42,
      fill: { color: "FEE2E2" }, rectRadius: 0.06, line: { color: "FECACA" }});
    s.addText(p.action, { x: 5.9, y: y+0.15, w: 3.5, h: 0.42,
      fontSize: 9, color: "DC2626", fontFace: FONT, valign: "middle", margin: 0 });
  });
}

// ── Slide 10: Results — Top 5 (candidate_id · rank · score · reasoning) ────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addText("Results: Top 5 Candidates", {
    x: 0.5, y: 0.2, w: 9.0, h: 0.6,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT, margin: 0
  });
  s.addText("Ranked by composite score — all India-based ML/Search engineers with production retrieval + ranking evidence.", {
    x: 0.5, y: 0.82, w: 9.0, h: 0.32,
    fontSize: 12, color: C.muted, fontFace: FONT, italic: true, margin: 0
  });

  // Columns: candidate_id | rank | score | reasoning
  const headers  = ["candidate_id",  "rank", "score",  "reasoning"];
  const colXs    = [0.4,             2.75,   3.55,     4.45];
  const colWs    = [2.3,             0.75,   0.85,     5.15];

  // Header row
  headers.forEach((h, ci) => {
    s.addShape(pres.shapes.RECTANGLE, { x: colXs[ci], y: 1.22, w: colWs[ci], h: 0.4,
      fill: { color: C.teal }, line: { color: C.teal }});
    s.addText(h, { x: colXs[ci]+0.06, y: 1.22, w: colWs[ci]-0.1, h: 0.4,
      fontSize: 10, bold: true, color: C.white, fontFace: "Courier New", valign: "middle", margin: 0 });
  });

  // Real top-5 from submission_ranked_top100.csv
  const results = [
    ["CAND_0018499", "#1", "0.8781", "7yr Sr. ML Engineer at Zomato — retrieval + ranking shipped; embeddings, weaviate. Noida (JD-preferred), 15d notice, open to work."],
    ["CAND_0046525", "#2", "0.8738", "6yr Sr. ML Engineer at Genpact AI — retrieval + ranking shipped; embeddings, elasticsearch. Pune (JD-preferred), strong match."],
    ["CAND_0081846", "#3", "0.8694", "7yr Lead AI Engineer at Razorpay — retrieval + ranking shipped; embeddings, pgvector. Jaipur, 30d notice, open to work."],
    ["CAND_0055905", "#4", "0.8652", "8yr Sr. ML Engineer at Flipkart — retrieval + ranking shipped; embeddings, opensearch. Strong match, 30d notice."],
    ["CAND_0002025", "#5", "0.8482", "6yr Sr. AI Engineer at Apple — retrieval + ranking shipped; embeddings, opensearch. Trivandrum, 30d notice."],
  ];

  results.forEach((row, ri) => {
    const y = 1.62 + ri * 0.77;
    const bg = ri % 2 === 0 ? "2A3F60" : C.navyLight;
    row.forEach((cell, ci) => {
      s.addShape(pres.shapes.RECTANGLE, { x: colXs[ci], y, w: colWs[ci], h: 0.72,
        fill: { color: bg }, line: { color: "33507A" }});
      s.addText(cell, { x: colXs[ci]+0.06, y, w: colWs[ci]-0.1, h: 0.72,
        fontSize: ci === 2 ? 13 : ci === 1 ? 13 : ci === 0 ? 9 : 8.5,
        bold: ci === 1 || ci === 2,
        color: ci === 1 ? C.coral : ci === 2 ? C.green : ci === 0 ? C.ice : C.muted,
        fontFace: ci <= 2 ? "Courier New" : FONT,
        valign: "middle", wrap: true, margin: 0 });
    });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y: 5.5, w: 9.2, h: 0.33,
    fill: { color: "2A3F60" }, rectRadius: 0.07 });
  s.addText("Validated: 100 rows · monotone scores · 0 honeypots in top 100 · all India-based AI/ML engineers · passes validate_submission.py",
    { x: 0.55, y: 5.5, w: 9.0, h: 0.33,
      fontSize: 9.5, color: C.green, fontFace: FONT, valign: "middle", margin: 0 });
}

// ── Slide 11: Design Rationale ──────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.offwhite };

  s.addText("Design Rationale", {
    x: 0.5, y: 0.25, w: 9.0, h: 0.65,
    fontSize: 28, bold: true, color: C.dark, fontFace: FONT, margin: 0
  });

  const qas = [
    { q: "Why career depth (35%) > skill match (30%)?",
      a: "JD explicitly warns: keyword matching is a trap. A candidate can list 'Pinecone' without ever shipping search. Production evidence is more predictive than listed skills." },
    { q: "Why is availability a multiplier, not additive?",
      a: "A 0.95 career score × 0.45 multiplier = 0.43 final. Additive would barely move them. Multiplicative puts unreachable candidates below actively-searching candidates with weaker skills." },
    { q: "Why soft-score YoE instead of hard-filter?",
      a: "JD says 'some people hit senior judgment at 4 years.' A 4yr candidate with production evidence should rank above a 7yr candidate with no shipping evidence." },
    { q: "Why penalize pure-services careers?",
      a: "JD explicitly: 'only consulting firms in entire career' = disqualifier. -0.20 to career component, not a total ban — services engineer with real production work can still rank." },
    { q: "Why detect eval framework (NDCG/A-B)?",
      a: "JD: 'if you've never thought about how to evaluate a ranking system, this role will be very painful.' Detecting this in career text is a direct quality proxy." },
  ];

  qas.forEach((qa, i) => {
    const y = 1.0 + i * 0.96;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y, w: 9.2, h: 0.86,
      fill: { color: C.white }, rectRadius: 0.08, shadow: makeShadow() });
    s.addText(`Q: ${qa.q}`, { x: 0.6, y: y+0.07, w: 8.8, h: 0.28,
      fontSize: 10.5, bold: true, color: C.dark, fontFace: FONT, margin: 0 });
    s.addText(`A: ${qa.a}`, { x: 0.6, y: y+0.4, w: 8.8, h: 0.38,
      fontSize: 9.5, color: C.mid, fontFace: FONT, margin: 0 });
  });
}

// ── Slide 12: Summary ───────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.OVAL, { x: 7.5, y: -1.0, w: 3.5, h: 3.5,
    fill: { color: C.teal, transparency: 80 }, line: { color: C.teal, transparency: 85 }});
  s.addShape(pres.shapes.OVAL, { x: -1.0, y: 4.2, w: 2.8, h: 2.8,
    fill: { color: C.coral, transparency: 80 }, line: { color: C.coral, transparency: 85 }});

  s.addText("Summary", {
    x: 0.7, y: 0.7, w: 8.6, h: 0.75,
    fontSize: 36, bold: true, color: C.white, fontFace: FONT, align: "left", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.7, y: 1.5, w: 3.0, h: 0.04,
    fill: { color: C.coral }, line: { color: C.coral }});

  const bullets = [
    ["100K candidates ranked in <35s on CPU",     "Streaming JSONL · parallel scoring · zero external dependencies"],
    ["Four-dimensional scoring",                   "Skill 30% · Career 35% · Behavioral 20% · Location 15%"],
    ["Career text analysis beats keyword matching","We detect SHIPPED systems, not listed buzzwords"],
    ["Availability is a multiplier",               "Inactive candidates demoted regardless of skill score"],
    ["5 honeypot detection patterns",              "Impossible skill combos, zeroed signals, salary inversion, temporal impossibility"],
    ["Validated submission — top 5 (real scores)", "CAND_0018499 (0.878) · CAND_0046525 (0.874) · CAND_0081846 (0.869)"],
  ];

  bullets.forEach(([title, sub], i) => {
    const y = 1.7 + i * 0.65;
    s.addShape(pres.shapes.OVAL, { x: 0.65, y: y+0.08, w: 0.22, h: 0.22,
      fill: { color: C.coral }, line: { color: C.coral }});
    s.addText(title, { x: 1.05, y, w: 8.0, h: 0.3,
      fontSize: 12, bold: true, color: C.white, fontFace: FONT, margin: 0 });
    s.addText(sub, { x: 1.05, y: y+0.32, w: 8.0, h: 0.25,
      fontSize: 9.5, color: C.muted, fontFace: FONT, margin: 0 });
  });
}

pres.writeFile({ fileName: "approach_deck.pptx" })
  .then(() => console.log("✅  approach_deck.pptx written (12 slides)"))
  .catch(e => { console.error("Error:", e); process.exit(1); });
