# Redrob Hackathon — Intelligent Candidate Ranker

**Challenge:** Rank 100,000 candidates for a Senior AI Engineer role at Redrob AI  
**Approach:** Multi-dimensional rule-based scoring with JD-semantic analysis  
**Runtime:** ~35 seconds on CPU · No GPU · No network · No external dependencies

---

## Quick Start

```bash
git clone <repo-url>
cd redrob-ranker

# Reproduce submission (single command — no pip installs for ranking step):
python3 ranker_v3.py --candidates candidates.jsonl --output submission_ranked_top100.csv

# Validate:
python3 validate_submission.py submission_ranked_top100.csv
```

**Runtime:** ~10 seconds on any modern CPU for 100K candidates.  
**Requirements:** Python 3.9+ standard library only for ranking. No pip installs.

## Sandbox (Streamlit)

```bash
pip install streamlit pandas
streamlit run app.py
```

Upload a `.jsonl` sample or use the pre-loaded `sample_candidates.json`. Runs on CPU, no external APIs.

---

## Dashboard

Open `dashboard.html` in any modern browser (no server required):

```bash
open dashboard.html
```

Load your `submission_ranked_top100.csv` and optionally `candidates.jsonl`.

**Features:**
- Ranked candidate cards with score rings and availability dots
- Score breakdown bars: Skill / Career / Behavioral / Location
- Live search by name, title, company, or skill
- Filter chips: Open to Work, India Only, Active <30d, Notice ≤30d
- Candidate detail drawer with career timeline and behavioral signal tiles
- Export filtered shortlist as CSV

---

## Architecture

```
final_score = (
    skill_match      × 0.30  +
    career_depth     × 0.35  +
    behavioral       × 0.20  +
    location         × 0.15
) × availability_multiplier
```

### 1. Skill Match (30%)
Matches against 40+ JD-relevant skills mapped to the actual dataset vocabulary.
Weighted by must-have tier (embeddings, vector DB, ranking, Python) vs. bonus tier.

### 2. Career Depth (35%)
Reads career description text for evidence of SHIPPED systems:
- `production_retrieval`: 'hybrid search', 'semantic search', 'FAISS', 'Elasticsearch' in descriptions
- `production_ranking`: 'learning to rank', 'ranking model', 'recommendation', 'discovery feed'
- `eval_framework`: 'NDCG', 'A/B test', 'offline eval', 'relevance labels'
- `product_pct`: proportion of career at product companies vs. services companies

### 3. Behavioral Signals (20%)
- Last active date → availability multiplier (0.28×–1.0×)
- Recruiter response rate → further availability penalty if <25%
- Notice period → 0.50–1.0 score
- GitHub activity, profile completeness, interview completion rate

### 4. Location (15%)
Pune/Noida → 1.0, India Tier-1 → 0.90, India non-preferred → 0.78,
willing to relocate → 0.55, outside India no relocation → 0.35

### Availability Multiplier
`avail_mult = 0.45 + 0.55 × availability`

Ensures a candidate with high skills but zero engagement is ranked below an
active, responsive candidate with slightly weaker skills.

### Honeypot Detection
- Expert proficiency on 7+ skills with 0 months usage → score 0.0
- Non-technical title (Marketing Manager) + 7+ core AI skills → score 0.0
- All behavioral signals = 0 + large skill list → score 0.0
- Salary min > salary max → score 0.0

---

## Files

| File | Description |
|------|-------------|
| `ranker_v3.py` | Main ranker — run this |
| `dashboard.html` | Recruiter UI — open in browser |
| `submission_ranked_top100.csv` | Final ranked output |
| `approach_deck.pptx` | Methodology presentation |
| `build_deck.js` | Deck builder (requires pptxgenjs) |
| `requirements.txt` | Empty — stdlib only |
| `submission_metadata_template 2.yaml` | Fill before submitting |

---

## Build the Deck

```bash
npm install -g pptxgenjs
node build_deck.js
# Converts to PDF:
soffice --headless --convert-to pdf approach_deck.pptx
```
