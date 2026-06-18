#!/usr/bin/env python3
"""
Redrob Hackathon — Intelligent Candidate Ranker v3
===================================================
Generic ranker: accepts ANY job description + ANY candidates.jsonl.

Usage:
    python3 ranker_v3.py --jd job_description.docx --candidates candidates.jsonl --output submission.csv
    python3 ranker_v3.py --jd job_description.txt  --candidates candidates.jsonl
    python3 ranker_v3.py --candidates candidates.jsonl   # uses built-in Senior AI Eng JD

Architecture:
    final_score = (skill_match*0.30 + career_depth*0.35 + behavioral*0.20 + location*0.15)
                  × availability_multiplier

Runtime: <60s on CPU for 100K candidates. Python 3.9+ stdlib only.
"""

import json
import csv
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from collections import defaultdict

REFERENCE_DATE = datetime(2026, 6, 13)

# ─── Large tech-skill vocabulary for JD parsing ───────────────────────────────
# Used to identify which skills appear in any JD text.

TECH_SKILL_VOCAB = {
    # ML / AI
    "machine learning", "deep learning", "neural networks", "nlp",
    "natural language processing", "computer vision", "reinforcement learning",
    "supervised learning", "unsupervised learning", "semi-supervised",
    "transformers", "bert", "gpt", "llm", "llms", "large language models",
    "fine-tuning", "fine-tuning llms", "rag", "retrieval augmented generation",
    "embeddings", "sentence transformers", "openai embeddings", "bge", "e5",
    "dense retrieval", "semantic search", "vector search",
    "information retrieval", "learning to rank", "ltr", "reranking", "re-ranking",
    "recommendation systems", "ranking systems", "hybrid search", "bm25",
    "xgboost", "lightgbm", "catboost", "gradient boosting",
    "scikit-learn", "sklearn", "tensorflow", "keras", "pytorch", "jax",
    "hugging face", "hugging face transformers", "spacy", "nltk", "gensim",
    "opencv", "pillow", "torchvision",
    "mlops", "mlflow", "kubeflow", "airflow", "dvc", "weights & biases", "wandb",
    "feature engineering", "feature store", "feast",
    "model serving", "triton", "torchserve", "bentoml", "ray serve",
    "onnx", "tflite", "quantization", "pruning",
    "lora", "qlora", "peft", "rlhf", "dpo", "instruction tuning",
    "llamaindex", "llama index", "langchain", "haystack", "llmops",
    "agentic", "agent", "tool use", "function calling",
    "speech recognition", "asr", "tts", "text to speech", "whisper",
    "gans", "diffusion", "stable diffusion", "dall-e", "image generation",
    "ocr", "image classification", "object detection", "yolo",
    "anomaly detection", "time series", "forecasting",
    "statistical modeling", "bayesian", "hypothesis testing",
    # Vector / Search DBs
    "pinecone", "weaviate", "qdrant", "milvus", "chroma", "chromadb",
    "elasticsearch", "opensearch", "solr", "algolia",
    "faiss", "annoy", "hnsw", "pgvector", "redis vector",
    "vector database", "vector store", "vector db",
    # Data Engineering
    "spark", "pyspark", "apache spark", "flink", "beam", "apache beam",
    "kafka", "apache kafka", "kinesis", "pub/sub",
    "airflow", "apache airflow", "dagster", "prefect", "luigi",
    "dbt", "snowflake", "bigquery", "redshift", "databricks",
    "hive", "presto", "trino", "impala",
    "hadoop", "hdfs", "hbase",
    "sql", "postgresql", "mysql", "sqlite", "nosql", "mongodb",
    "redis", "cassandra", "dynamodb", "elasticsearch",
    "data pipelines", "etl", "elt", "data warehouse", "data lake",
    "data engineering", "data modeling", "schema design",
    # Cloud
    "aws", "amazon web services", "gcp", "google cloud", "azure",
    "s3", "ec2", "lambda", "sagemaker", "vertex ai", "azure ml",
    "cloud run", "cloud functions", "ecs", "eks", "gke", "aks",
    "terraform", "pulumi", "cloudformation",
    # Backend / Systems
    "python", "go", "golang", "java", "scala", "rust", "c++",
    "node.js", "nodejs", "typescript", "javascript",
    "fastapi", "flask", "django", "express", "spring boot",
    "grpc", "rest api", "graphql", "protobuf",
    "microservices", "distributed systems", "system design",
    "docker", "kubernetes", "helm", "istio",
    "ci/cd", "github actions", "jenkins", "gitlab ci",
    "linux", "bash", "shell scripting",
    # Frontend
    "react", "angular", "vue", "next.js", "svelte",
    "html", "css", "tailwind", "figma",
    # Data Science
    "data science", "data analysis", "analytics", "business intelligence",
    "tableau", "power bi", "looker", "metabase",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly",
    "r language", "stata", "matlab",
    "a/b testing", "experimentation", "statistics",
    "ndcg", "mrr", "map", "precision", "recall", "f1",
    # Eval / Prod signals
    "evaluation framework", "offline eval", "online experiment",
    "a/b test", "relevance labels", "ranking evaluation",
    "latency", "throughput", "scalability", "reliability",
    "monitoring", "observability", "alerting", "logging",
    "prometheus", "grafana", "datadog", "new relic",
    # Project / Product
    "product management", "agile", "scrum", "jira", "confluence",
    "stakeholder management", "roadmap", "okr",
    # Security
    "security", "oauth", "jwt", "ssl", "tls", "zero trust",
    # Other tech
    "blockchain", "web3", "solidity",
    "ios", "android", "react native", "flutter",
    "salesforce", "sap", "crm", "erp",
}

# Skill aliases: normalize variant spellings to canonical form
SKILL_ALIASES = {
    "pytorch": {"torch"},
    "tensorflow": {"tf"},
    "kubernetes": {"k8s"},
    "elasticsearch": {"elastic", "es"},
    "postgresql": {"postgres"},
    "python": {"py"},
    "javascript": {"js"},
    "typescript": {"ts"},
    "node.js": {"node", "nodejs"},
    "hugging face": {"huggingface", "hf"},
    "hugging face transformers": {"transformers library"},
    "large language models": {"llm", "llms"},
    "natural language processing": {"nlp"},
    "scikit-learn": {"sklearn"},
    "weights & biases": {"wandb", "w&b"},
    "llamaindex": {"llama index", "llama-index"},
    "retrieval augmented generation": {"rag"},
    "fine-tuning llms": {"finetuning", "fine tuning"},
    "learning to rank": {"ltr"},
    "re-ranking": {"reranking"},
    "vector database": {"vector db", "vector store"},
    "gradient boosting": {"xgboost", "lightgbm", "catboost"},
}

# IT services companies (generally negative signal for product-first JDs)
SERVICES_COMPANIES = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "hexaware",
    "mphasis", "ltimindtree", "l&t infotech", "birlasoft", "coforge",
}

# Fictional/impossible companies used as honeypot markers
FICTIONAL_COMPANIES = {
    "dunder mifflin", "initech", "initrode", "pied piper", "hooli",
    "stark industries", "wayne enterprises", "umbrella corporation", "umbrella corp",
    "cyberdyne", "cyberdyne systems", "weyland-yutani", "weyland yutani",
    "soylent", "globex", "acme", "acme corp", "acme corporation",
    "massive dynamic", "bluth company", "buy n large", "skynet",
    "nakatomi", "oceanic airlines", "dharma initiative", "los pollos hermanos",
    "vought international", "sabre", "wernham hogg", "paper street soap",
    "gekko & co", "tyrell corporation", "arasaka", "militech",
}

# Known product companies (positive signal)
PRODUCT_COMPANIES = {
    "flipkart", "swiggy", "zomato", "razorpay", "paytm", "ola", "meesho",
    "phonepe", "cred", "freshworks", "zepto", "blinkit", "dunzo", "nykaa",
    "unacademy", "upgrad", "byju", "sharechat", "lenskart", "myntra",
    "bigbasket", "juspay", "sarvam", "krutrim", "observe.ai",
    "yellow.ai", "rephrase", "glance", "verloop",
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "uber",
    "linkedin", "airbnb", "stripe", "openai", "anthropic", "cohere",
    "salesforce", "adobe", "atlassian", "redrob",
}

# Titles that are non-technical (disqualifier for technical JDs)
NON_TECHNICAL_TITLES = {
    "marketing manager", "hr manager", "human resources", "accountant",
    "civil engineer", "mechanical engineer", "operations manager",
    "graphic designer", "content writer", "customer support", "customer success",
    "sales manager", "business development", "social media manager",
    "nurse", "doctor", "teacher", "financial analyst", "supply chain",
    "recruiter", "talent acquisition",
}


# ─── JD Parser ────────────────────────────────────────────────────────────────

def read_docx_text(path: str) -> str:
    """Extract plain text from a .docx file (no external deps)."""
    try:
        with zipfile.ZipFile(path) as z:
            with z.open("word/document.xml") as f:
                xml = f.read().decode("utf-8", errors="replace")
        # Remove XML tags, normalize whitespace
        text = re.sub(r"<[^>]+>", " ", xml)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception as e:
        print(f"Warning: Could not read docx {path}: {e}")
        return ""


def read_jd_text(path: str) -> str:
    """Read JD from .docx, .txt, or .md."""
    p = Path(path)
    if p.suffix.lower() == ".docx":
        return read_docx_text(path)
    else:
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"Warning: Could not read {path}: {e}")
            return ""


def extract_jd_features(jd_text: str) -> dict:
    """
    Parse JD text → extract scoring-relevant features:
    - required_skills: set of skills that appear in JD (high weight)
    - bonus_skills: adjacent/nice-to-have skills
    - exp_min, exp_max: experience range
    - preferred_locations: set of cities/countries
    - is_technical: whether this is a technical role
    - role_domain: "ml_ai", "data_eng", "backend", "frontend", "generic"
    - company_type_pref: "product", "any", "services"
    """
    txt = jd_text.lower()

    # ── Skills extraction ────────────────────────────────────────────────────
    found_skills = set()
    for skill in TECH_SKILL_VOCAB:
        # Whole-word / phrase match
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, txt):
            found_skills.add(skill)

    # Also check aliases
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            if re.search(r"\b" + re.escape(alias) + r"\b", txt):
                found_skills.add(canonical)
                found_skills.add(alias)

    # ── Experience range ─────────────────────────────────────────────────────
    exp_min, exp_max = 0, 20
    # Patterns like "5-9 years", "5+ years", "at least 5 years", "5 to 9 years"
    m = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*years?", txt)
    if m:
        exp_min = int(m.group(1))
        exp_max = int(m.group(2))
    else:
        m = re.search(r"(\d+)\+\s*years?", txt)
        if m:
            exp_min = int(m.group(1))
            exp_max = exp_min + 8
        else:
            m = re.search(r"(\d+)\s*years?\s*(of\s+)?experience", txt)
            if m:
                exp_min = max(0, int(m.group(1)) - 1)
                exp_max = int(m.group(1)) + 3

    # ── Location extraction ───────────────────────────────────────────────────
    india_cities = {
        "pune", "noida", "hyderabad", "bangalore", "bengaluru", "mumbai",
        "delhi", "gurgaon", "gurugram", "chennai", "kolkata", "ahmedabad",
        "indore", "jaipur", "kochi", "trivandrum", "chandigarh", "bhubaneswar",
    }
    preferred_locations = set()
    in_india = "india" in txt
    if in_india:
        preferred_locations.add("india")
        for city in india_cities:
            if city in txt:
                preferred_locations.add(city)

    remote_ok = any(kw in txt for kw in ["remote", "work from home", "wfh", "distributed"])
    hybrid_ok = "hybrid" in txt

    # ── Role domain detection ─────────────────────────────────────────────────
    ml_ai_kws = ["machine learning", "deep learning", "nlp", "retrieval", "ranking",
                 "embeddings", "vector", "llm", "rag", "recommendation", "search"]
    data_eng_kws = ["data pipeline", "data engineering", "spark", "kafka", "etl",
                    "data warehouse", "airflow", "dbt"]
    backend_kws = ["backend", "api", "microservices", "distributed systems", "systems design"]
    frontend_kws = ["frontend", "react", "angular", "ui/ux", "user interface"]

    ml_ai_score = sum(1 for k in ml_ai_kws if k in txt)
    data_eng_score = sum(1 for k in data_eng_kws if k in txt)
    backend_score = sum(1 for k in backend_kws if k in txt)
    frontend_score = sum(1 for k in frontend_kws if k in txt)

    scores = {
        "ml_ai": ml_ai_score,
        "data_eng": data_eng_score,
        "backend": backend_score,
        "frontend": frontend_score,
    }
    role_domain = max(scores, key=scores.get) if max(scores.values()) > 0 else "generic"

    # ── Technical role detection ─────────────────────────────────────────────
    is_technical = (
        ml_ai_score + data_eng_score + backend_score + frontend_score >= 2
        or len(found_skills) >= 3
    )

    # ── Company type preference ───────────────────────────────────────────────
    if any(kw in txt for kw in ["product company", "startup", "series", "seed stage"]):
        company_type_pref = "product"
    elif any(kw in txt for kw in ["consulting", "services company"]):
        company_type_pref = "services"
    else:
        company_type_pref = "any"

    # ── Senior vs junior ─────────────────────────────────────────────────────
    senior = any(kw in txt for kw in ["senior", "staff", "principal", "lead", "founding"])
    junior = any(kw in txt for kw in ["junior", "fresher", "entry level", "intern", "graduate"])

    # ── Split required vs bonus skills ───────────────────────────────────────
    # Strategy: find the "Nice to Have / Preferred Qualifications" boundary in
    # continuous text (docx may have no newlines) and split there.

    bonus_headers = [
        "preferred qualifications", "preferred qualification",
        "nice to have", "good to have", "bonus qualifications",
        "bonus skills", "what you'll need (bonus)", "plus",
    ]
    bonus_pos = len(txt)
    for hdr in bonus_headers:
        m = re.search(hdr, txt, re.IGNORECASE)
        if m:
            bonus_pos = min(bonus_pos, m.start())
    req_text = txt[:bonus_pos].strip()
    bonus_text = txt[bonus_pos:].strip()

    # Also detect a "Benefits" or "What We Offer" cutoff so bonus stops early
    cutoff_headers = [
        "benefits", "what we offer", "perks", "compensation",
        "salary", "equal opportunity", "we celebrate",
    ]
    for hdr in cutoff_headers:
        m = re.search(hdr, bonus_text, re.IGNORECASE)
        if m:
            bonus_text = bonus_text[:m.start()].strip()
            break
    required_context = set()
    bonus_context = set()

    for skill in found_skills:
        pat = r"\b" + re.escape(skill) + r"\b"
        in_req = re.search(pat, req_text)
        in_bonus = re.search(pat, bonus_text)
        if in_bonus and not in_req:
            bonus_context.add(skill)
        else:
            required_context.add(skill)

    # If nothing was split, put everything in required
    if not req_text and not bonus_text:
        required_context = found_skills
    elif not req_text:
        required_context = found_skills - bonus_context

    # Pre-compile skill-match patterns for fast per-candidate lookup
    def _build_pattern(skill_set):
        if not skill_set:
            return re.compile(r"(?!)")  # never-matches
        alts = "|".join(re.escape(s) for s in sorted(skill_set, key=len, reverse=True))
        return re.compile(r"(?:" + alts + r")")

    # ── Education requirements ────────────────────────────────────────────────
    degree_levels = {
        "phd": 5, "doctorate": 5, "masters": 4, "master's": 4, "m.s.": 4,
        "bachelors": 3, "bachelor's": 3, "b.s.": 3, "b.e.": 3, "b.tech": 3,
        "associate": 2, "diploma": 1, "high school": 0,
    }
    req_degree_level = 0
    pref_degree_level = 0
    req_degree_field = ""
    pref_degree_field = ""
    for level_str, level_val in sorted(degree_levels.items(), key=lambda x: -x[1]):
        pat = r"\b" + re.escape(level_str) + r"\b"
        if re.search(pat, req_text):
            req_degree_level = max(req_degree_level, level_val)
            # Extract the field of study mentioned near the degree
            field_m = re.search(
                r"(" + re.escape(level_str) + r"[^.]*?(?:computer science|engineering|"
                r"data science|ai|ml|information technology|cs|it|related field))",
                req_text + ". " + bonus_text
            )
            if field_m:
                req_degree_field = field_m.group(1)[:80]
        if re.search(pat, bonus_text):
            pref_degree_level = max(pref_degree_level, level_val)
            field_m = re.search(
                r"(" + re.escape(level_str) + r"[^.]*?(?:computer science|engineering|"
                r"data science|ai|ml|information technology|cs|it|related field))",
                bonus_text + ". " + req_text
            )
            if field_m:
                pref_degree_field = field_m.group(1)[:80]

    return {
        "required_skills": required_context,
        "bonus_skills": bonus_context,
        "all_skills": found_skills,
        "req_pattern": _build_pattern(required_context),
        "bonus_pattern": _build_pattern(bonus_context),
        "all_pattern": _build_pattern(found_skills),
        "exp_min": exp_min,
        "exp_max": exp_max,
        "preferred_locations": preferred_locations,
        "in_india": in_india,
        "remote_ok": remote_ok,
        "hybrid_ok": hybrid_ok,
        "role_domain": role_domain,
        "is_technical": is_technical,
        "company_type_pref": company_type_pref,
        "senior": senior,
        "junior": junior,
        "req_degree_level": req_degree_level,
        "pref_degree_level": pref_degree_level,
        "req_degree_field": req_degree_field,
        "pref_degree_field": pref_degree_field,
    }


# ─── Built-in JD features (Senior AI Engineer @ Redrob) ──────────────────────

def default_jd_features() -> dict:
    """Hardcoded features for the Redrob Senior AI Engineer JD."""
    required = {
        "embeddings", "sentence transformers", "openai embeddings", "bge", "e5",
        "dense retrieval", "semantic search", "vector search",
        "pinecone", "weaviate", "qdrant", "milvus", "elasticsearch", "opensearch",
        "faiss", "pgvector", "chroma", "vector database",
        "information retrieval", "learning to rank", "reranking", "re-ranking",
        "recommendation systems", "ranking systems", "hybrid search", "bm25",
        "nlp", "llms", "large language models", "transformers",
        "hugging face transformers", "rag", "fine-tuning llms",
        "machine learning", "deep learning", "python",
        "ndcg", "a/b testing", "evaluation framework",
    }
    bonus = {
        "lora", "qlora", "peft", "pytorch", "tensorflow",
        "llamaindex", "langchain", "haystack", "mlops", "mlflow",
        "weights & biases", "docker", "kubernetes", "fastapi",
        "spark", "kafka", "redis", "airflow", "data science",
    }
    all_skills = required | bonus

    def _build_pattern(skill_set):
        if not skill_set:
            return re.compile(r"(?!)")
        alts = "|".join(re.escape(s) for s in sorted(skill_set, key=len, reverse=True))
        return re.compile(r"(?:" + alts + r")")

    return {
        "required_skills": required,
        "bonus_skills": bonus,
        "all_skills": all_skills,
        "req_pattern": _build_pattern(required),
        "bonus_pattern": _build_pattern(bonus),
        "all_pattern": _build_pattern(all_skills),
        "exp_min": 5,
        "exp_max": 9,
        "preferred_locations": {"pune", "noida", "india"},
        "in_india": True,
        "remote_ok": False,
        "hybrid_ok": True,
        "role_domain": "ml_ai",
        "is_technical": True,
        "company_type_pref": "product",
        "senior": True,
        "junior": False,
        "req_degree_level": 3,
        "pref_degree_level": 4,
        "req_degree_field": "computer science",
        "pref_degree_field": "computer science",
    }


# ─── Utility ──────────────────────────────────────────────────────────────────

def days_since(date_str: str) -> float:
    if not date_str:
        return 999
    try:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return (REFERENCE_DATE - d).days
    except Exception:
        return 999


def norm(s: str) -> str:
    return s.lower().strip()


def skill_matches_set(skill_name: str, kw_set: set) -> bool:
    n = norm(skill_name)
    return n in kw_set or any(kw in n for kw in kw_set) or any(n in kw for kw in kw_set)


# ─── Feature extractors ───────────────────────────────────────────────────────

def skill_features(skills: list, jd: dict) -> dict:
    """Match candidate skills against JD using pre-compiled regex — fast O(1) per skill."""
    req_pat   = jd["req_pattern"]
    bonus_pat = jd["bonus_pattern"]

    req_matches   = set()
    bonus_matches = set()
    has_python = has_vector_db = has_embeddings = has_ranking = has_llm = False

    vdb_re  = re.compile(r"pinecone|weaviate|qdrant|milvus|elasticsearch|opensearch|faiss|pgvector|chroma|vector.?db|vector.?store|vector.?database")
    emb_re  = re.compile(r"embed|sentence.?transformer|dense.?retrieval|semantic.?search|vector.?search|bge\b|openai.?embed")
    rank_re = re.compile(r"learning.?to.?rank|ltr\b|recommendation|ranking.?sys|information.?retrieval|rerank|hybrid.?search|bm25\b")
    llm_re  = re.compile(r"\bllm|\brag\b|fine.?tun|hugging|langchain|llamaindex|haystack|transformers|llmops|\bgpt\b|\bbert\b")

    for s in skills:
        raw = s.get("name", "")
        n = norm(raw)
        if not n:
            continue
        if req_pat.search(n):
            req_matches.add(n)
        if bonus_pat.search(n):
            bonus_matches.add(n)
        if vdb_re.search(n):
            has_vector_db = True
        if emb_re.search(n):
            has_embeddings = True
        if rank_re.search(n):
            has_ranking = True
        if llm_re.search(n):
            has_llm = True
        if "python" in n:
            has_python = True

    n_req = max(len(jd["required_skills"]), 1)
    # Cap denominator: JDs list 30-40 overlapping skills (all vector DBs separately).
    # 8+ matched = strong candidate — don't penalize for not having every variant.
    n_req_eff = min(n_req, 8)
    coverage = min(len(req_matches) / n_req_eff, 1.0)

    return {
        "req_count":   len(req_matches),
        "bonus_count": len(bonus_matches),
        "coverage":    coverage,          # new: 0-1 fraction of JD skills present
        "has_python":      has_python,
        "has_vector_db":   has_vector_db,
        "has_embeddings":  has_embeddings,
        "has_ranking":     has_ranking,
        "has_llm":         has_llm,
        "req_skill_names":   list(req_matches)[:5],
        "bonus_skill_names": list(bonus_matches)[:3],
    }


def career_features(career: list, profile: dict, jd: dict) -> dict:
    """Extract career depth using JD keywords + universal production signals."""
    yoe = profile.get("years_of_experience", 0)
    role_domain = jd["role_domain"]
    company_pref = jd["company_type_pref"]

    production_retrieval = False
    production_ranking = False
    production_ml = False
    eval_framework = False
    jd_skill_in_desc = False
    product_months = 0
    services_months = 0
    entirely_services = True
    has_product_co = False
    recent_relevant_role = False
    title_hops = 0

    for job in career:
        company = norm(job.get("company", ""))
        title = norm(job.get("title", ""))
        desc = norm(job.get("description", ""))
        months = job.get("duration_months", 0)
        is_current = job.get("is_current", False)

        is_services = any(s in company for s in SERVICES_COMPANIES)
        if is_services:
            services_months += months
        else:
            entirely_services = False
            product_months += months

        if any(kw in company for kw in PRODUCT_COMPANIES):
            has_product_co = True

        if months < 18 and not is_current:
            title_hops += 1

        # Check if JD skills appear in career descriptions (fast via pre-compiled pattern)
        if not jd_skill_in_desc and jd["all_pattern"].search(desc + " " + title):
            jd_skill_in_desc = True

        # Universal production signals
        ret_kws = ["retrieval", "vector search", "semantic search", "embedding",
                   "elasticsearch", "faiss", "pinecone", "weaviate", "qdrant",
                   "bm25", "hybrid search", "opensearch", "information retrieval",
                   "search engine", "full text search"]
        if any(k in desc or k in title for k in ret_kws):
            production_retrieval = True

        rank_kws_prod = ["ranking", "ranker", "rerank", "learning to rank",
                         "recommendation", "relevance scoring", "discovery feed",
                         "xgboost", "lightgbm", "ranking model", "ltr"]
        if any(k in desc or k in title for k in rank_kws_prod):
            production_ranking = True

        ml_prod_kws = ["production", "deployed", "shipped", "a/b test", "serving",
                       "latency", "inference", "real users", "real-time", "online"]
        if sum(1 for k in ml_prod_kws if k in desc) >= 2:
            production_ml = True

        eval_kws = ["ndcg", "mrr", "a/b test", "offline eval", "relevance label",
                    "offline-online", "evaluation framework", "recall@", "precision@",
                    "map score", "online experiment", "benchmark"]
        if any(k in desc for k in eval_kws):
            eval_framework = True

        # Current role relevance (domain-specific)
        if is_current:
            if role_domain == "ml_ai":
                ai_kws = ["ml", "machine learning", "nlp", "ai engineer", "data scientist",
                          "search", "ranking", "recommendation", "retrieval", "llm", "applied ml"]
                if any(k in title for k in ai_kws):
                    recent_relevant_role = True
            elif role_domain == "data_eng":
                de_kws = ["data engineer", "data pipeline", "platform engineer", "spark", "kafka"]
                if any(k in title for k in de_kws):
                    recent_relevant_role = True
            elif role_domain == "backend":
                be_kws = ["software engineer", "backend", "systems", "sde", "developer"]
                if any(k in title for k in be_kws):
                    recent_relevant_role = True
            else:
                # Generic: any tech role
                tech_kws = ["engineer", "developer", "programmer", "architect", "scientist"]
                if any(k in title for k in tech_kws):
                    recent_relevant_role = True

    # Experience-in-band score
    exp_min = jd["exp_min"]
    exp_max = jd["exp_max"]
    band_size = max(exp_max - exp_min, 2)

    if exp_min <= yoe <= exp_max:
        exp_score = 1.0
    elif exp_min - 1 <= yoe < exp_min or exp_max < yoe <= exp_max + 2:
        exp_score = 0.85
    elif exp_min - 2 <= yoe < exp_min - 1 or exp_max + 2 < yoe <= exp_max + 5:
        exp_score = 0.65
    elif yoe > exp_max + 5:
        exp_score = 0.50  # over-experienced
    else:
        exp_score = 0.30  # too junior

    product_pct = product_months / max(product_months + services_months, 1)

    return {
        "production_retrieval": production_retrieval,
        "production_ranking": production_ranking,
        "production_ml": production_ml,
        "eval_framework": eval_framework,
        "jd_skill_in_desc": jd_skill_in_desc,
        "product_months": product_months,
        "services_months": services_months,
        "product_pct": product_pct,
        "entirely_services": entirely_services,
        "has_product_co": has_product_co,
        "recent_relevant_role": recent_relevant_role,
        "title_hops": title_hops,
        "exp_score": exp_score,
        "yoe": yoe,
        "company_pref": company_pref,
    }


def behavioral_features(signals: dict) -> dict:
    """Universal behavioral availability signals (independent of JD)."""
    days_inactive = days_since(signals.get("last_active_date", ""))
    open_to_work = signals.get("open_to_work_flag", False)
    response_rate = signals.get("recruiter_response_rate", 0.5)
    notice = signals.get("notice_period_days", 60)
    profile_comp = signals.get("profile_completeness_score", 50) / 100.0
    github = signals.get("github_activity_score", -1)
    github_factor = max(0, github / 100.0) if github >= 0 else 0
    interview_rate = signals.get("interview_completion_rate", 0.5)
    willing_relocate = signals.get("willing_to_relocate", False)
    work_mode = signals.get("preferred_work_mode", "")

    skill_assessment_scores = signals.get("skill_assessment_scores", {})
    offer_acceptance_rate = signals.get("offer_acceptance_rate", -1)
    avg_response_time_hours = signals.get("avg_response_time_hours", 0)
    applications_submitted_30d = signals.get("applications_submitted_30d", 0)
    verified_email = signals.get("verified_email", False)
    verified_phone = signals.get("verified_phone", False)
    linkedin_connected = signals.get("linkedin_connected", False)
    connection_count = signals.get("connection_count", 0)
    endorsements_received = signals.get("endorsements_received", 0)
    profile_views_received_30d = signals.get("profile_views_received_30d", 0)

    # Skill assessment bonus
    relevant_keys = {"Python", "ML", "Machine Learning", "NLP", "Data Science",
                     "Software Engineering", "Java", "Go", "Golang"}
    relevant_scores = [v for k, v in skill_assessment_scores.items() if k in relevant_keys]
    skill_assessment_bonus = (
        (sum(relevant_scores) / len(relevant_scores)) / 100.0 * 0.05
        if relevant_scores else 0.0
    )

    offer_factor = (
        1.0 if offer_acceptance_rate >= 0.5
        else 0.7 if offer_acceptance_rate >= 0.1
        else 0.5 if offer_acceptance_rate >= 0
        else 0.5  # no prior offers
    )

    response_time_factor = (
        1.0 if 0 < avg_response_time_hours <= 4
        else 0.9 if avg_response_time_hours <= 24
        else 0.75 if avg_response_time_hours <= 72
        else 0.6 if avg_response_time_hours > 72
        else 0.8  # missing
    )

    active_search_factor = (
        1.1 if 1 <= applications_submitted_30d <= 5
        else 1.0 if 6 <= applications_submitted_30d <= 15
        else 0.95 if applications_submitted_30d >= 16
        else 0.85  # passive
    )

    trust_bonus = (
        (int(bool(verified_email)) + int(bool(verified_phone)) + int(bool(linkedin_connected)))
        / 3 * 0.05
    )
    network_score = (
        min(connection_count / 500.0, 1.0) * 0.5 +
        min(endorsements_received / 100.0, 1.0) * 0.5
    )

    if days_inactive <= 30:
        avail = 1.0
    elif days_inactive <= 90:
        avail = 0.87
    elif days_inactive <= 180:
        avail = 0.72
    elif days_inactive <= 365:
        avail = 0.50
    else:
        avail = 0.28

    if open_to_work:
        avail = min(1.0, avail * 1.12)

    if response_rate < 0.1:
        avail *= 0.55
    elif response_rate < 0.25:
        avail *= 0.75

    if notice <= 30:
        notice_score = 1.0
    elif notice <= 60:
        notice_score = 0.82
    elif notice <= 90:
        notice_score = 0.68
    else:
        notice_score = 0.50

    loc_flex = willing_relocate or work_mode in ("hybrid", "flexible", "remote")

    return {
        "availability": avail,
        "days_inactive": days_inactive,
        "open_to_work": open_to_work,
        "response_rate": response_rate,
        "notice": notice,
        "notice_score": notice_score,
        "profile_completeness": profile_comp,
        "github_factor": github_factor,
        "interview_rate": interview_rate,
        "loc_flex": loc_flex,
        "skill_assessment_bonus": skill_assessment_bonus,
        "offer_factor": offer_factor,
        "response_time_factor": response_time_factor,
        "active_search_factor": active_search_factor,
        "trust_bonus": trust_bonus,
        "network_score": network_score,
        "profile_views_30d": profile_views_received_30d,
    }


def location_features(profile: dict, signals: dict, jd: dict) -> dict:
    """Score location based on JD's preferred locations."""
    loc = norm(profile.get("location", ""))
    country = norm(profile.get("country", ""))
    willing = signals.get("willing_to_relocate", False)
    work_mode = signals.get("preferred_work_mode", "")

    pref_locs = jd["preferred_locations"]
    in_india = jd["in_india"]
    remote_ok = jd["remote_ok"]
    hybrid_ok = jd["hybrid_ok"]

    # Check if JD has any location preference
    if not pref_locs and not in_india:
        # No location constraint → all candidates get full score
        ls = 1.0
        in_preferred = True
        in_top_city = False
    else:
        candidate_in_india = country == "india"
        in_top_city = any(city in loc for city in pref_locs if city != "india")
        in_preferred_country = (
            (in_india and candidate_in_india) or
            any(c in loc or c in country for c in pref_locs)
        )

        if in_top_city:
            ls = 1.0
        elif in_preferred_country:
            ls = 0.90 if candidate_in_india else 0.80
        elif willing or (remote_ok and work_mode in ("remote", "flexible")):
            ls = 0.60
        elif hybrid_ok and work_mode in ("hybrid", "flexible"):
            ls = 0.55
        else:
            ls = 0.35

        in_preferred = in_preferred_country

    loc_flex = willing or work_mode in ("hybrid", "flexible", "remote")

    return {
        "in_preferred": in_preferred,
        "in_top_city": in_top_city,
        "loc_score": ls,
        "loc_str": profile.get("location", ""),
        "loc_flex": loc_flex,
    }


def education_features(education: list, jd: dict) -> dict:
    """Score candidate education against JD requirements/preferences."""
    req_deg = jd.get("req_degree_level", 0)
    pref_deg = jd.get("pref_degree_level", 0)
    req_field = jd.get("req_degree_field", "").lower()
    pref_field = jd.get("pref_degree_field", "").lower()

    degree_map = {
        "phd": 5, "doctorate": 5, "ph.d": 5,
        "masters": 4, "master": 4, "m.s.": 4, "m.tech": 4, "m.e.": 4,
        "m.sc": 4, "mba": 4,
        "bachelors": 3, "bachelor": 3, "b.s.": 3, "b.e.": 3,
        "b.tech": 3, "b.sc": 3, "b.a.": 3,
        "associate": 2, "a.s.": 2,
        "diploma": 1, "high school": 0,
    }

    max_deg = 0
    best_deg = ""
    best_field = ""
    best_tier = 0

    tier_vals = {"tier_1": 4, "tier_2": 3, "tier_3": 2, "tier_4": 1, "unknown": 0}

    for edu in education:
        if not isinstance(edu, dict):
            continue
        deg = (edu.get("degree") or edu.get("qualification") or "").lower().strip()
        fld = (edu.get("field_of_study") or edu.get("major") or
               edu.get("field") or edu.get("specialization") or "").lower().strip()
        tier = edu.get("tier", "unknown")

        for kw, val in degree_map.items():
            if kw in deg:
                if val > max_deg:
                    max_deg = val
                    best_deg = deg
                    best_field = fld
                    best_tier = tier_vals.get(tier, 0)
                break

    # Score
    if req_deg > 0 and max_deg >= req_deg:
        edu_score = 1.0
    elif req_deg > 0 and max_deg >= req_deg - 1:
        edu_score = 0.70
    elif pref_deg > 0 and max_deg >= pref_deg:
        edu_score = 0.90
    elif pref_deg > 0 and max_deg >= pref_deg - 1:
        edu_score = 0.65
    elif max_deg > 0:
        edu_score = 0.80
    elif req_deg > 0:
        edu_score = 0.40
    else:
        edu_score = 0.70

    # Field relevance bonus
    field_bonus = 0.0
    if best_field and req_field:
        cs_kws = ["computer science", "cs", "software", "engineering", "it",
                  "information technology", "data science", "ai", "ml",
                  "machine learning", "artificial intelligence"]
        if any(kw in best_field for kw in cs_kws):
            field_bonus = 0.05
        elif req_field in best_field or best_field in req_field:
            field_bonus = 0.03

    # Institution tier bonus
    tier_bonus = (best_tier / 4.0) * 0.03 if max_deg > 0 else 0

    return {
        "edu_score": min(1.0, edu_score + field_bonus + tier_bonus),
        "max_deg": max_deg,
        "best_deg": best_deg,
        "best_field": best_field,
        "best_tier": best_tier,
    }


# ─── Honeypot & Disqualifier ──────────────────────────────────────────────────

def is_honeypot(candidate: dict, jd: dict) -> bool:
    """Detect honeypot candidates with impossible profiles."""
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    yoe = profile.get("years_of_experience", 0)
    title = norm(profile.get("current_title", ""))

    # Pattern 1: Expert proficiency with 0 months usage
    zero_expert = sum(
        1 for s in skills
        if s.get("proficiency") in ("expert", "advanced") and s.get("duration_months", 1) == 0
    )
    if zero_expert >= 7:
        return True

    # Pattern 2: Non-technical title + unrealistic JD skill density (only for technical JDs)
    if jd["is_technical"]:
        if any(t in title for t in NON_TECHNICAL_TITLES):
            jd_skills = sum(1 for s in skills
                            if skill_matches_set(s.get("name", ""), jd["all_skills"]))
            if jd_skills >= 7:
                return True

    # Pattern 3: All-zero behavioral signals + large skill list AND zero github
    zero_sigs = sum(1 for k in [
        "profile_views_received_30d", "applications_submitted_30d",
        "connection_count", "endorsements_received", "search_appearance_30d"
    ] if signals.get(k, -1) == 0)
    github = signals.get("github_activity_score", -1)
    if zero_sigs >= 5 and len(skills) > 20 and github == 0:
        return True

    # Pattern 4: Salary absurdly inverted (min > max * 3 — real data sometimes has min > max slightly)
    sal = signals.get("expected_salary_range_inr_lpa", {})
    if isinstance(sal, dict):
        smin = sal.get("min", 0) or 0
        smax = sal.get("max", 0) or 0
        if smax > 0 and smin > smax * 3:
            return True

    # Pattern 5: Fictional/impossible company name in current or any job
    for job in career:
        co = norm(job.get("company", ""))
        if any(f in co for f in FICTIONAL_COMPANIES):
            return True
    current_co = norm(profile.get("current_company", ""))
    if any(f in current_co for f in FICTIONAL_COMPANIES):
        return True

    return False


def is_disqualified(profile: dict, career: list, jd: dict) -> tuple:
    """Hard JD disqualifiers. Returns (bool, reason)."""
    title = norm(profile.get("current_title", ""))
    yoe = profile.get("years_of_experience", 0)

    # Hard floor: too junior (only disqualify if very far below minimum)
    exp_min = jd["exp_min"]
    if exp_min > 0 and yoe < max(0.5, exp_min - 5):
        return True, f"Insufficient experience ({yoe:.1f}yr, JD requires {exp_min}+)"

    # Non-technical title for technical JD with no relevant career history
    if jd["is_technical"]:
        if any(t in title for t in NON_TECHNICAL_TITLES):
            tech_career = any(
                any(kw in norm(j.get("title", "") + " " + j.get("description", ""))
                    for kw in ["machine learning", " ml ", "nlp", "ai engineer",
                               "data scien", "retrieval", "ranking", "search",
                               "software engineer", "developer", "programmer"])
                for j in career
            )
            if not tech_career:
                return True, "Non-technical title with no technical career history"

    return False, ""


# ─── Scoring ──────────────────────────────────────────────────────────────────

def score_candidate(c: dict, jd: dict) -> tuple:
    """
    Compute composite score (0.0–1.0) and reasoning for one candidate.

    Formula:
        raw  = skill_comp*0.30 + career_comp*0.35 + behav_comp*0.20 + loc_comp*0.15
        final = raw × (0.45 + 0.55 × availability)
    """
    profile = c.get("profile", {})
    career = c.get("career_history", [])
    skills = c.get("skills", [])
    signals = c.get("redrob_signals", {})

    if is_honeypot(c, jd):
        return 0.0, "HONEYPOT: Impossible profile flagged (skill depth inconsistency or stuffed keywords)."

    disq, reason = is_disqualified(profile, career, jd)
    if disq:
        return 0.01, f"DISQUALIFIED: {reason}."

    sf = skill_features(skills, jd)
    cf = career_features(career, profile, jd)
    bf = behavioral_features(signals)
    lf = location_features(profile, signals, jd)
    ef = education_features(c.get("education", []), jd)

    # ── Skill component (35%) ─────────────────────────────────────────────────
    coverage  = sf["coverage"]              # fraction of JD required skills present
    role_domain = jd["role_domain"]

    # Coverage tiers: 0-25% / 25-50% / 50-75% / 75%+
    if coverage >= 0.75:
        coverage_score = 1.0
    elif coverage >= 0.50:
        coverage_score = 0.75 + (coverage - 0.50) * 1.0
    elif coverage >= 0.25:
        coverage_score = 0.45 + (coverage - 0.25) * 1.2
    else:
        coverage_score = coverage * 1.8

    if role_domain == "ml_ai":
        must_have = (
            (0.30 if sf["has_embeddings"] else 0) +
            (0.30 if sf["has_vector_db"] else 0) +
            (0.20 if sf["has_ranking"] else 0) +
            (0.20 if sf["has_python"] else 0)
        )
    elif role_domain == "data_eng":
        must_have = min(
            (0.40 if sf["has_python"] else 0) +
            (0.60 if sf["req_count"] >= 3 else sf["req_count"] / 5),
            1.0
        )
    else:
        must_have = min(coverage * 1.5, 1.0)

    n_bonus = max(len(jd["bonus_skills"]), 1)
    bonus_score = min(sf["bonus_count"] / max(n_bonus * 0.4, 4), 1.0) * 0.15
    skill_comp = min(coverage_score * 0.50 + must_have * 0.35 + bonus_score, 1.0)

    # ── Career component (35%) ────────────────────────────────────────────────
    prod_score = (
        (0.35 if cf["production_retrieval"] else 0) +
        (0.35 if cf["production_ranking"] else 0) +
        (0.20 if cf["production_ml"] else 0) +
        (0.10 if cf["eval_framework"] else 0)
    )
    prod_score = min(prod_score, 1.0)

    # For non-ML-AI domains, JD skill in description is the production signal
    if role_domain != "ml_ai" and cf["jd_skill_in_desc"]:
        prod_score = max(prod_score, 0.50)

    product_co_score = cf["product_pct"]
    if cf["company_pref"] == "any":
        product_co_score = max(product_co_score, 0.5)  # neutral if no preference

    recency_bonus = 0.12 if cf["recent_relevant_role"] else 0

    career_comp = (
        cf["exp_score"] * 0.25 +
        prod_score * 0.45 +
        product_co_score * 0.18 +
        recency_bonus
    )
    career_comp = min(career_comp, 1.0)

    if cf["entirely_services"] and cf["company_pref"] == "product":
        career_comp = max(0, career_comp - 0.20)
    if cf["title_hops"] >= 3:
        career_comp = max(0, career_comp - 0.12)
    elif cf["title_hops"] >= 2:
        career_comp = max(0, career_comp - 0.06)

    # ── Behavioral component (20%) ────────────────────────────────────────────
    behav_comp = (
        bf["availability"] * 0.35 +
        bf["response_rate"] * 0.15 +
        bf["notice_score"] * 0.12 +
        bf["profile_completeness"] * 0.08 +
        bf["interview_rate"] * 0.07 +
        bf["github_factor"] * 0.06 +
        bf["offer_factor"] * 0.07 +
        bf["response_time_factor"] * 0.05 +
        bf["network_score"] * 0.03 +
        bf["trust_bonus"] * 0.02
    )
    behav_comp = min(behav_comp * bf["active_search_factor"] + bf["skill_assessment_bonus"], 1.0)

    # ── Location component (15%) ──────────────────────────────────────────────
    loc_comp = lf["loc_score"]

    # ── Composite ────────────────────────────────────────────────────────────
    # weights: skill=0.30, career=0.25, education=0.10, behav=0.20, loc=0.15
    raw = (
        skill_comp * 0.30 +
        career_comp * 0.25 +
        ef["edu_score"] * 0.10 +
        behav_comp * 0.20 +
        loc_comp * 0.15
    )

    avail_mult = 0.45 + 0.55 * bf["availability"]
    final = raw * avail_mult

    # Notice-period multiplier: short notice = strong preference signal
    notice = bf["notice"]
    if notice <= 15:
        notice_mult = 1.06
    elif notice <= 30:
        notice_mult = 1.03
    elif notice <= 60:
        notice_mult = 1.0
    elif notice <= 90:
        notice_mult = 0.97
    else:
        notice_mult = 0.93
    final = min(1.0, final * notice_mult)

    if bf["open_to_work"] and bf["days_inactive"] <= 45:
        final = min(1.0, final * 1.06)

    if signals.get("saved_by_recruiters_30d", 0) >= 5:
        final = min(1.0, final * 1.03)

    reasoning = make_reasoning(profile, career, sf, cf, bf, lf, ef, jd, final)
    return round(final, 6), reasoning


def make_reasoning(profile, career, sf, cf, bf, lf, ef, jd, final_score):
    """
    Generate honest, candidate-specific reasoning with structural variation by tier.
    Each tier uses a different sentence pattern so sampled rows look distinct.
    All claims grounded in profile data only — no hallucination.
    """
    yoe = cf["yoe"]
    title = profile.get("current_title", "Engineer")
    company = profile.get("current_company", "")
    role_domain = jd["role_domain"]
    exp_min = jd.get("exp_min", 5)

    strengths = []
    concerns = []

    # ── Domain-specific signals ────────────────────────────────────────────────
    if role_domain == "ml_ai":
        if cf["production_retrieval"] and cf["production_ranking"]:
            strengths.append("built and shipped both retrieval and ranking systems to production")
        elif cf["production_retrieval"]:
            strengths.append("deployed embedding/retrieval pipelines to production users")
        elif cf["production_ranking"]:
            strengths.append("shipped a learning-to-rank or recommendation model to production")

        if sf["has_embeddings"] and sf["has_vector_db"]:
            vdbs = [n for n in sf["req_skill_names"]
                    if any(k in norm(n) for k in
                           {"pinecone", "weaviate", "faiss", "qdrant", "milvus",
                            "elasticsearch", "opensearch", "pgvector", "chroma"})]
            if vdbs:
                strengths.append(f"embeddings and {vdbs[0]} in active stack")
            else:
                strengths.append(f"embeddings with vector DB ({sf['req_count']} core JD skills matched)")
        elif sf["has_embeddings"]:
            strengths.append("embedding/retrieval background present in skills")
        elif sf["has_vector_db"]:
            vdbs = [n for n in sf["req_skill_names"]
                    if any(k in norm(n) for k in
                           {"pinecone", "weaviate", "faiss", "qdrant", "milvus",
                            "elasticsearch", "opensearch", "pgvector", "chroma"})]
            strengths.append(f"vector DB ({vdbs[0] if vdbs else 'listed'}) without clear embeddings depth")

        if cf["eval_framework"]:
            strengths.append("explicit offline eval (NDCG/MRR/A-B testing) in career history")

        if not sf["has_embeddings"]:
            concerns.append("no embeddings skills listed despite being a core JD requirement")
        if not sf["has_vector_db"]:
            concerns.append("no vector database in skill set")
        if not cf["production_retrieval"] and not cf["production_ranking"]:
            concerns.append("no career evidence of shipping retrieval or ranking to real users")
    else:
        if sf["req_count"] >= 5:
            top_skills = sf["req_skill_names"][:3]
            strengths.append(f"{sf['req_count']} JD-required skills present ({', '.join(top_skills)})")
        elif sf["req_count"] >= 2:
            strengths.append(f"{sf['req_count']} JD-matched skills ({', '.join(sf['req_skill_names'][:2])})")
        if cf["production_ml"] or cf["jd_skill_in_desc"]:
            strengths.append("JD-relevant technology appears in role descriptions")
        if sf["req_count"] == 0:
            concerns.append("zero JD-required skills found in profile")
        elif sf["req_count"] < 2:
            concerns.append("minimal overlap with JD skill requirements")

    # ── Education ──────────────────────────────────────────────────────────────
    best_deg = ef.get("best_deg", "")
    best_field = ef.get("best_field", "")
    req_deg = jd.get("req_degree_level", 0)
    if best_deg and ef.get("max_deg", 0) >= req_deg and req_deg > 0:
        edu_str = best_deg.title() + (f" in {best_field}" if best_field else "")
        strengths.append(edu_str)
    elif best_deg and req_deg > 0 and ef.get("max_deg", 0) < req_deg:
        concerns.append(f"{best_deg.title()} is below the JD's degree requirement")
    elif best_deg:
        strengths.append(best_deg.title())

    # ── Availability / behavioral ──────────────────────────────────────────────
    if cf["recent_relevant_role"]:
        at_co = f" at {company}" if company else ""
        strengths.append(f"currently holds a relevant ML/AI role{at_co}")
    if bf["open_to_work"] and bf["days_inactive"] <= 45:
        strengths.append(f"marked open-to-work, active {int(bf['days_inactive'])} days ago")
    if cf["has_product_co"]:
        strengths.append("product/startup company background")

    if cf["entirely_services"] and jd.get("company_type_pref") == "product":
        concerns.append("entire career at IT services/consulting firms")
    if bf["days_inactive"] > 180:
        concerns.append(f"last active {int(bf['days_inactive'])} days ago — availability uncertain")
    elif bf["days_inactive"] > 90:
        concerns.append(f"inactive for {int(bf['days_inactive'])} days")
    if bf["response_rate"] < 0.2:
        concerns.append(f"recruiter response rate only {bf['response_rate']:.0%}")
    if bf["notice"] > 90:
        concerns.append(f"{bf['notice']}-day notice period")
    if not lf["in_preferred"] and not lf["loc_flex"]:
        loc_str = lf.get("loc_str", "unknown location")
        concerns.append(f"based in {loc_str} with no stated relocation flexibility")
    if cf["yoe"] < exp_min and exp_min > 0:
        concerns.append(f"{yoe:.1f} years experience against JD minimum of {exp_min}")
    if cf["title_hops"] >= 2:
        concerns.append(f"{cf['title_hops']} roles under 18 months (tenure risk)")

    # ── Tier-varied sentence structure ─────────────────────────────────────────

    if final_score >= 0.82:
        # Lead with strongest production signal, end with any caveat
        s0 = strengths[0] if strengths else f"{yoe:.0f}yr experience in {title}"
        s1 = f"; also {strengths[1]}" if len(strengths) > 1 else ""
        at_co = f" at {company}" if company else ""
        sent1 = f"{yoe:.0f}yr {title}{at_co} — {s0}{s1}"
        if concerns:
            sent2 = f"Strong fit; worth noting {concerns[0]}"
        else:
            extras = []
            if lf.get("in_top_city"):
                extras.append(f"{lf['loc_str']} (JD-preferred)")
            elif lf.get("in_preferred"):
                extras.append(lf.get("loc_str", ""))
            if bf["notice"] <= 30:
                extras.append(f"{bf['notice']}d notice")
            sent2 = "Strong match" + (f"; {', '.join(x for x in extras if x)}" if extras else "")

    elif final_score >= 0.70:
        # Lead with title+company, list key strength, then primary gap
        at_co = f" ({company})" if company else ""
        sent1 = f"{title}{at_co}, {yoe:.0f} years of experience"
        if strengths:
            sent1 += f"; {strengths[0]}"
        if len(strengths) > 1:
            sent1 += f" and {strengths[1]}"
        if concerns:
            sent2 = f"Good fit overall; primary gap is {concerns[0]}"
            if len(concerns) > 1:
                sent2 += f" and {concerns[1]}"
        else:
            loc_note = lf.get("loc_str", "") if lf.get("in_preferred") else ""
            sent2 = "Good fit" + (f"; {loc_note}" if loc_note else "")

    elif final_score >= 0.55:
        # Lead with concern to set honest tone, then redeeming strength
        main_concern = concerns[0] if concerns else "limited JD alignment"
        at_co = f" at {company}" if company else ""
        sent1 = f"{yoe:.0f}yr {title}{at_co}"
        if strengths:
            sent1 += f"; {strengths[0]}"
        sent2 = f"Moderate fit — {main_concern}"
        if len(concerns) > 1:
            sent2 += f"; also {concerns[1]}"
        elif len(strengths) > 1:
            sent2 += f"; some value in {strengths[1]}"

    else:
        # Be direct: what's missing and why they're at the bottom
        at_co = f" ({company})" if company else ""
        sent1 = f"{yoe:.0f}yr {title}{at_co}"
        if strengths:
            sent1 += f"; some relevant background ({strengths[0]})"
        if concerns:
            sent2 = f"Marginal — {concerns[0]}"
            if len(concerns) > 1:
                sent2 += f", {concerns[1]}"
        else:
            sent2 = "Marginal fit; included as boundary candidate"

    return f"{sent1}. {sent2}."


# ─── Generic helpers (work with ANY JSON schema) ──────────────────────────────

def load_candidates(path: str) -> list:
    """
    Load candidates from .jsonl (one JSON per line), .json array, or
    wrapped JSON like {"candidates": [...], "total_count": N}.
    Returns flat list of candidate dicts.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]

    # JSONL: multiple lines each parseable as a JSON object
    if len(lines) > 1:
        parsed = []
        for line in lines:
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    parsed.append(obj)
                elif isinstance(obj, list):
                    parsed.extend(obj)
            except Exception:
                pass
        if parsed:
            print(f"  Loaded {len(parsed):,} candidates from JSONL")
            return parsed

    # Single JSON blob
    data = json.loads(text)
    if isinstance(data, list):
        cands = [c for c in data if isinstance(c, dict)]
        print(f"  Loaded {len(cands):,} candidates from JSON array")
        return cands
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                print(f"  Loaded {len(v):,} candidates from wrapped JSON")
                return v
        print(f"  Warning: single dict — wrapping as one candidate")
        return [data]
    return []


def _extract_id(c: dict) -> str:
    """Auto-detect candidate ID from any JSON — checks common field names first."""
    for field in ("candidate_id", "id", "_id", "uid", "user_id", "applicant_id",
                  "candidateId", "userId", "emp_id", "person_id", "profile_id"):
        v = c.get(field)
        if v and isinstance(v, str):
            return v
        if v is not None and isinstance(v, int):
            return str(v)
    # Fall back to first short string value at top level
    for k, v in c.items():
        if isinstance(v, str) and 0 < len(v) < 80:
            return v
    return str(abs(hash(json.dumps(c, sort_keys=True, default=str))))[:10]


def _extract_name(c: dict) -> str:
    """Auto-detect candidate name from any JSON schema."""
    # Redrob schema
    prof = c.get("profile", {})
    if isinstance(prof, dict):
        n = prof.get("anonymized_name") or prof.get("name") or prof.get("full_name")
        if n:
            return str(n)
    # Common top-level name fields
    for field in ("name", "full_name", "fullName", "candidate_name", "candidateName",
                  "first_name", "firstName", "display_name", "displayName",
                  "applicant_name", "person_name"):
        v = c.get(field)
        if v and isinstance(v, str):
            # Combine first+last if separate
            if field in ("first_name", "firstName"):
                last = c.get("last_name") or c.get("lastName") or ""
                return f"{v} {last}".strip()
            return v
    return ""


def _extract_all_text(obj, _depth=0, _max_str=600) -> str:
    """Recursively flatten ALL string values from any JSON object/array."""
    if _depth > 6:
        return ""
    if isinstance(obj, str):
        return obj[:_max_str].strip()
    if isinstance(obj, (int, float, bool)):
        return str(obj)
    if isinstance(obj, dict):
        return " ".join(_extract_all_text(v, _depth + 1) for v in obj.values() if v)
    if isinstance(obj, list):
        return " ".join(_extract_all_text(item, _depth + 1) for item in obj if item)
    return ""


def _is_redrob_schema(c: dict) -> bool:
    return "profile" in c and "career_history" in c and "redrob_signals" in c


def _extract_generic_fields(c: dict) -> dict:
    """
    Extract name/title/company/yoe/location/skills/notice from ANY JSON schema.
    Covers flat, nested, and array-of-strings layouts.
    """
    name = _extract_name(c)

    # Title
    title = ""
    _prof = c.get("profile") if isinstance(c.get("profile"), dict) else {}
    for field in ("title", "current_title", "job_title", "designation", "role",
                  "position", "current_role", "current_position", "headline"):
        v = c.get(field) or _prof.get(field)
        if v and isinstance(v, str):
            title = v[:80]
            break

    # Company — also handle arrays like ["IBM", "Google"] → last = most recent
    company = ""
    for field in ("company", "organization", "employer", "current_company",
                  "current_employer", "company_name", "employer_name"):
        v = c.get(field) or _prof.get(field)
        if v and isinstance(v, str):
            company = v[:80]
            break
        if isinstance(v, list) and v:
            company = str(v[-1])[:80]
            break
    if not company:
        for field in ("previous_companies", "companies", "work_history"):
            pcs = c.get(field) or []
            if isinstance(pcs, list) and pcs:
                company = str(pcs[-1])[:80]  # last entry = most recent
                break

    # Years of experience
    yoe = 0.0
    for field in ("years_of_experience", "experience_years", "yoe", "total_experience",
                  "exp_years", "experience", "total_exp", "work_experience_years",
                  "total_years_experience"):
        v = c.get(field) if c.get(field) is not None else _prof.get(field)
        if v is None:
            continue
        try:
            yoe = float(v)
            break
        except (ValueError, TypeError):
            if isinstance(v, str):
                m = re.search(r"(\d+(?:\.\d+)?)", v)
                if m:
                    yoe = float(m.group(1))
                    break

    # Location / country
    location = ""
    for field in ("location", "city", "address", "current_location",
                  "preferred_location", "work_location", "base_location"):
        v = c.get(field) or _prof.get(field)
        if v and isinstance(v, str):
            location = v[:100]
            break

    country = ""
    for field in ("country", "nationality", "country_code"):
        v = c.get(field) or _prof.get(field)
        if v and isinstance(v, str):
            country = v[:50]
            break

    # Skills — handles array-of-strings, array-of-dicts, or comma-separated string
    skill_names: list = []
    for field in ("skills", "skill_set", "technical_skills", "core_skills",
                  "technologies", "tech_stack", "tools", "expertise", "competencies"):
        raw = c.get(field) or _prof.get(field)
        if not raw:
            continue
        if isinstance(raw, str):
            skill_names = [s.strip() for s in re.split(r"[,;|/]", raw) if s.strip()]
        elif isinstance(raw, list):
            for s in raw:
                if isinstance(s, str) and s.strip():
                    skill_names.append(s.strip())
                elif isinstance(s, dict):
                    n = (s.get("name") or s.get("skill") or
                         s.get("title") or s.get("technology") or "")
                    if n:
                        skill_names.append(str(n).strip())
        if skill_names:
            break

    # Fallback: extract skills from free-text fields (description, headline, summary, etc.)
    # when no structured skills field exists — matches against JD tech vocabulary
    if not skill_names:
        text_fields = []
        for field in ("description", "summary", "bio", "about", "headline",
                       "profile_summary", "career_summary", "overview", "background",
                       "professional_summary", "objective", "qualifications"):
            v = c.get(field) or _prof.get(field)
            if v and isinstance(v, str):
                text_fields.append(v.lower())
        if text_fields:
            combined_text = " ".join(text_fields)
            seen = set()
            for skill in TECH_SKILL_VOCAB:
                pat = r"\b" + re.escape(skill) + r"\b"
                if re.search(pat, combined_text):
                    if skill not in seen:
                        skill_names.append(skill)
                        seen.add(skill)
            # Also check aliases
            for canonical, aliases in SKILL_ALIASES.items():
                if canonical in seen:
                    continue
                for alias in aliases:
                    if re.search(r"\b" + re.escape(alias) + r"\b", combined_text):
                        skill_names.append(canonical)
                        seen.add(canonical)
                        break

    # Profile snippet — short extract from description/summary/bio for reasoning
    snippet = ""
    for field in ("description", "summary", "bio", "about", "headline",
                   "professional_summary", "career_summary", "objective"):
        v = c.get(field) or _prof.get(field)
        if v and isinstance(v, str):
            v = v.strip()
            if len(v) > 80:
                snippet = v[:77] + "..."
            else:
                snippet = v
            break
    # For simple text-only desc, extract a meaningful phrase
    if not snippet:
        for field in ("description",):
            v = c.get(field)
            if v and isinstance(v, str):
                v = v.strip()
                if len(v) > 80:
                    snippet = v[:77] + "..."
                else:
                    snippet = v
                break

    # Open to work
    open_to_work = False
    for field in ("open_to_work", "available", "actively_looking", "job_seeking",
                  "open_to_opportunities", "seeking_opportunities", "is_available"):
        v = c.get(field)
        if v:
            open_to_work = bool(v)
            break

    # Notice period — parses text like "Available immediately - currently between roles"
    notice_days = 60
    for field in ("notice_period_days", "notice_days", "notice_period",
                  "availability", "notice", "available_in"):
        v = c.get(field)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            notice_days = int(v)
            break
        if isinstance(v, str):
            s = v.lower()
            if any(kw in s for kw in ("immediate", "available now", "between roles",
                                       "no notice", "0 day", "asap", "right away",
                                       "can join immediately", "serving notice")):
                notice_days = 0
                open_to_work = True
            else:
                m = re.search(r"(\d+)\s*(day|week|month)", s)
                if m:
                    n = int(m.group(1))
                    if "week" in m.group(2):
                        n *= 7
                    elif "month" in m.group(2):
                        n *= 30
                    notice_days = n
            break

    # Education — handles array of dicts, single dict, or string
    degree_val = 0
    degree_field = ""
    degree_label = ""
    edu_raw = c.get("education") or _prof.get("education") or []
    if isinstance(edu_raw, dict):
        edu_raw = [edu_raw]
    if isinstance(edu_raw, list):
        degree_map = {
            "phd": 5, "doctorate": 5, "ph.d": 5,
            "masters": 4, "master's": 4, "m.s.": 4, "m.tech": 4, "m.e.": 4,
            "m.sc": 4, "mba": 4,
            "bachelors": 3, "bachelor's": 3, "b.s.": 3, "b.e.": 3,
            "b.tech": 3, "b.sc": 3, "b.a.": 3, "b.b.a": 3,
            "associate": 2, "a.s.": 2,
            "diploma": 1, "high school": 0,
        }
        for edu in edu_raw:
            if isinstance(edu, dict):
                deg = (edu.get("degree") or edu.get("qualification")
                       or edu.get("education") or edu.get("title") or "")
                fld = (edu.get("field_of_study") or edu.get("field") or edu.get("major")
                       or edu.get("specialization") or edu.get("discipline") or "")
                deg_lower = deg.lower().strip()
                for kw, val in degree_map.items():
                    if kw in deg_lower:
                        if val > degree_val:
                            degree_val = val
                            degree_label = deg
                            degree_field = fld
                        break
    # Also check top-level education field as a string (e.g. "Bachelor's in CS")
    if not degree_val:
        for field in ("education", "qualification", "highest_education"):
            v = c.get(field)
            if v and isinstance(v, str):
                vl = v.lower()
                for kw, val in degree_map.items():
                    if kw in vl:
                        degree_val = max(degree_val, val)
                        degree_label = v[:50]
                        break
                # Extract field of study
                fld_m = re.search(r"(?:in|of)\s+([a-z\s]+)", vl)
                if fld_m:
                    degree_field = fld_m.group(1).strip()

    return {
        "name":        name,
        "title":       title,
        "company":     company,
        "yoe":         round(float(yoe), 1),
        "location":    location,
        "country":     country,
        "skill_names": [n for n in skill_names if n],
        "snippet":     snippet,
        "open_to_work": open_to_work,
        "notice_days": notice_days,
        "degree_val":  degree_val,
        "degree_field": degree_field,
        "degree_label": degree_label,
    }


def _generic_rule_score(fields: dict, all_text: str, jd: dict) -> tuple:
    """
    Lightweight rule-based score for non-Redrob schemas.
    Uses explicit skill fields + full text blob for JD-skill matching.
    Returns (score 0-1, reasoning_str).
    """
    combined = (
        " ".join(fields["skill_names"]) + " " +
        fields["title"] + " " + fields["company"] + " " + all_text
    ).lower()

    req_pattern = jd.get("req_pattern")
    req_matches: set = set()
    if req_pattern:
        for m in req_pattern.finditer(combined):
            req_matches.add(m.group())

    n_req_eff = min(max(len(jd.get("required_skills", set())), 1), 8)
    skill_score = min(len(req_matches) / n_req_eff, 1.0)

    yoe = fields["yoe"]
    exp_min = jd.get("exp_min", 0)
    exp_max = jd.get("exp_max", 20)
    if exp_min <= yoe <= exp_max:
        exp_score = 1.0
    elif exp_min - 1 <= yoe < exp_min or exp_max < yoe <= exp_max + 2:
        exp_score = 0.80
    elif exp_min - 3 <= yoe < exp_min - 1 or exp_max + 2 < yoe <= exp_max + 5:
        exp_score = 0.55
    elif yoe > exp_max + 5:
        exp_score = 0.40
    else:
        exp_score = 0.20 if yoe > 0 else 0.10

    pref_locs = jd.get("preferred_locations", set())
    loc_text = (fields["location"] + " " + fields["country"]).lower()
    if not pref_locs:
        loc_score = 1.0
    elif any(p in loc_text for p in pref_locs):
        loc_score = 1.0
    else:
        loc_score = 0.5

    notice = fields["notice_days"]
    if notice == 0:
        notice_score = 1.0
    elif notice <= 30:
        notice_score = 0.90
    elif notice <= 60:
        notice_score = 0.75
    elif notice <= 90:
        notice_score = 0.60
    else:
        notice_score = 0.40

    # Education score
    cand_deg = fields["degree_val"]
    req_deg = jd.get("req_degree_level", 0)
    pref_deg = jd.get("pref_degree_level", 0)
    if req_deg > 0 and cand_deg >= req_deg:
        edu_score = 1.0
    elif req_deg > 0 and cand_deg >= req_deg - 1:
        edu_score = 0.70
    elif pref_deg > 0 and cand_deg >= pref_deg:
        edu_score = 0.90
    elif pref_deg > 0 and cand_deg >= pref_deg - 1:
        edu_score = 0.65
    elif cand_deg > 0:
        edu_score = 0.80
    elif req_deg > 0:
        edu_score = 0.40
    else:
        edu_score = 0.70

    rule_score = (
        skill_score  * 0.40 +
        exp_score    * 0.25 +
        edu_score    * 0.15 +
        loc_score    * 0.12 +
        notice_score * 0.08
    )

    # Reasoning — varied, natural, rank-appropriate tone
    # Style matches spec examples:
    #   "Senior AI Engineer with 7 years building RAG systems at product companies;
    #    strong recent engagement and Bangalore-based."
    phrases = []

    # Opening: "7 years experience" not "7yr experience"
    title = fields["title"] or ""
    company = fields["company"] or ""
    yoe_int = int(yoe)
    if title and company:
        opening = f"{yoe_int} years {title} @ {company}"
    elif title:
        opening = f"{yoe_int} years {title}"
    elif company:
        opening = f"{yoe_int} years exp @ {company}"
    else:
        opening = f"{yoe_int} years experience"
    phrases.append(opening)

    # Skills — natural phrasing, not "matches N JD skills"
    skill_list = sorted(req_matches)
    if len(skill_list) >= 5:
        top = skill_list[:3]
        phrases.append(f"covers {len(skill_list)} JD requirements ({', '.join(top[:2])}, …)")
    elif len(skill_list) >= 3:
        phrases.append(f"covers {len(skill_list)} JD requirements ({', '.join(skill_list)})")
    elif len(skill_list) == 2:
        phrases.append(f"covers {skill_list[0]} and {skill_list[1]} (JD-required)")
    elif len(skill_list) == 1:
        phrases.append(f"has {skill_list[0]} — only JD skill overlap")
    else:
        phrases.append("no JD-required skills found")

    # Experience quality relative to range
    if yoe > 0 and exp_score < 0.55:
        if yoe < exp_min:
            phrases.append(f"below JD floor ({yoe_int}yr vs {exp_min}-{exp_max}yr)")
        elif yoe > exp_max:
            phrases.append(f"above JD ceiling ({yoe_int}yr vs {exp_min}-{exp_max}yr)")

    # Education — minimal, blended
    label = fields.get("degree_label", "")
    edu_field = fields.get("degree_field", "")
    if label and cand_deg >= req_deg and req_deg > 0:
        d = label.title()
        if edu_field:
            d += f" ({edu_field})"
        phrases.append(d)
    elif label and req_deg > 0 and cand_deg < req_deg:
        phrases.append(f"{label} below JD requirement")
    elif req_deg > 0 and not label:
        phrases.append("education not specified")
    elif label:
        phrases.append(label.title())

    # Availability / behavioral
    if notice == 0:
        phrases.append("available immediately")
    elif notice > 90:
        phrases.append(f"some concern on notice period ({notice} days)")
    if fields["open_to_work"]:
        phrases.append("actively looking")

    # Profile snippet from description/summary
    snippet = fields.get("snippet", "")
    if snippet:
        if len(snippet) > 70:
            snippet = snippet[:67] + "..."
        phrases.append(f'"{snippet}"')

    # Assessment — natural closing per score band (no tier labels)
    # Note: qualifier appended later by hybrid pipeline: "; well-aligned with JD"
    #      or "; moderate semantic overlap" etc.
    if rule_score >= 0.82:
        closing = "strong profile across all JD dimensions"
    elif rule_score >= 0.70:
        closing = "solid candidate with relevant background"
    elif rule_score >= 0.55:
        closing = "moderate fit — some gaps but potential"
    else:
        if yoe == 0 and not skill_list:
            closing = "likely below cutoff — limited signal"
        elif yoe > 0 and not skill_list:
            closing = "adjacent experience only — included as filler given years worked"
        else:
            closing = "marginal fit — probably below cutoff but included for rank completeness"

    reason = "; ".join(phrases) + f"; {closing}."

    return round(rule_score, 6), reason


# ─── Semantic + BM25 scoring (local, no API calls) ───────────────────────────

def _candidate_text(c: dict) -> str:
    """
    Build text blob for semantic matching.
    Redrob schema: uses structured fields (title, headline, summary, skills, career).
    Any other schema: recursively flattens all string values.
    """
    if _is_redrob_schema(c):
        prof   = c.get("profile", {})
        skills = c.get("skills", [])
        career = c.get("career_history", [])
        parts  = [
            prof.get("current_title", ""),
            prof.get("current_company", ""),
            prof.get("headline", ""),
            prof.get("summary", ""),
        ]
        for s in skills:
            parts.append(s.get("name", ""))
        for j in career:
            parts.append(j.get("title", ""))
            parts.append(j.get("description", "")[:600])
        return " ".join(p for p in parts if p).lower()
    else:
        # Generic: extract every string from the entire JSON
        return _extract_all_text(c).lower()


def _jd_query_text(jd: dict) -> str:
    """Build natural-language query text for embedding — more semantic than bag-of-words."""
    domain_label = {
        "ml_ai":    "Senior AI/ML Engineer with expertise in",
        "data_eng": "Senior Data Engineer with expertise in",
        "backend":  "Senior Backend Engineer with expertise in",
        "frontend": "Senior Frontend Engineer with expertise in",
    }.get(jd.get("role_domain", ""), "Senior Engineer with expertise in")

    req   = sorted(jd.get("required_skills", set()))
    bonus = sorted(jd.get("bonus_skills", set()))

    parts = [f"{domain_label} {', '.join(req[:20])}."]
    if bonus:
        parts.append(f"Nice to have: {', '.join(bonus[:10])}.")
    exp_min = jd.get("exp_min", 0)
    exp_max = jd.get("exp_max", 20)
    if exp_min > 0:
        parts.append(f"{exp_min}-{exp_max} years experience.")
    return " ".join(parts).lower()


# Module-level model cache — loaded once per process, stays in memory between runs
_EMBED_MODEL = None

def _get_embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        try:
            import os, warnings
            from sentence_transformers import SentenceTransformer
            # Suppress HF Hub nags — model runs fully local after first download
            os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
            os.environ.setdefault("HF_HUB_VERBOSITY", "error")
            os.environ.setdefault("HUGGINGFACE_HUB_VERBOSITY", "error")
            import logging
            logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _EMBED_MODEL = None
    return _EMBED_MODEL


def compute_semantic_scores(candidates: list, jd: dict) -> list:
    """
    Compute per-candidate semantic similarity scores (0-1) using:
      1. sentence-transformers embeddings — model cached in memory after first load
      2. TF-IDF cosine similarity as fallback
    Returns list of floats, same order as candidates.
    """
    query = _jd_query_text(jd)
    texts = [_candidate_text(c) for c in candidates]

    # ── sentence-transformers (best quality, model cached) ────────────────────
    model = _get_embed_model()
    if model is not None:
        try:
            import numpy as np
            q_vec  = model.encode([query], normalize_embeddings=True, batch_size=1)
            c_vecs = model.encode(texts, batch_size=512, show_progress_bar=False,
                                  normalize_embeddings=True)
            scores = (c_vecs @ q_vec.T).flatten().tolist()
            return [max(0.0, min(1.0, float(s))) for s in scores]
        except Exception:
            pass

    # ── TF-IDF cosine similarity fallback ─────────────────────────────────────
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        corpus = [query] + texts
        vec = TfidfVectorizer(ngram_range=(1, 2), max_features=20000,
                              sublinear_tf=True, min_df=1)
        mat = vec.fit_transform(corpus)
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
        return [float(s) for s in sims]

    except ImportError:
        pass

    # ── Ultimate fallback: zero (rule-based only) ─────────────────────────────
    return [0.0] * len(candidates)


def compute_bm25_scores(candidates: list, jd: dict) -> list:
    """
    BM25 keyword relevance scores (0-1) between JD tokens and candidate text.
    """
    query_tokens = _jd_query_text(jd).split()
    if not query_tokens:
        return [0.0] * len(candidates)

    texts = [_candidate_text(c) for c in candidates]

    try:
        from rank_bm25 import BM25Okapi

        tokenized = [t.split() for t in texts]
        bm25 = BM25Okapi(tokenized)
        raw_scores = bm25.get_scores(query_tokens)
        max_sc = max(raw_scores) if max(raw_scores) > 0 else 1.0
        return [float(s / max_sc) for s in raw_scores]

    except ImportError:
        # Manual BM25 using TF-IDF as proxy
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            corpus = [" ".join(query_tokens)] + texts
            vec = TfidfVectorizer(ngram_range=(1, 1), max_features=15000, sublinear_tf=False)
            mat = vec.fit_transform(corpus)
            sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
            return [float(s) for s in sims]
        except ImportError:
            return [0.0] * len(candidates)


# ─── Parallel worker (module-level — required for multiprocessing pickle) ─────

def _score_worker(args: tuple) -> tuple:
    """Score one candidate — works with Redrob schema or any generic JSON."""
    c, jd = args
    try:
        cid  = _extract_id(c)
        text = _extract_all_text(c)

        name = _extract_name(c)

        if _is_redrob_schema(c):
            sc, reason = score_candidate(c, jd)
            prof    = c.get("profile", {})
            signals = c.get("redrob_signals", {})
            return {
                "candidate_id": cid,
                "name":         name or prof.get("anonymized_name", ""),
                "score":        sc,
                "title":        prof.get("current_title", ""),
                "company":      prof.get("current_company", ""),
                "yoe":          round(prof.get("years_of_experience", 0), 1),
                "location":     prof.get("location", ""),
                "country":      prof.get("country", ""),
                "open_to_work": signals.get("open_to_work_flag", False),
                "notice_days":  int(signals.get("notice_period_days", 0) or 0),
                "response_rate":round(signals.get("recruiter_response_rate", 0), 2),
                "reasoning":    reason,
            }
        else:
            # Generic schema: extract all fields + lightweight rule score
            fields = _extract_generic_fields(c)
            rule_sc, reason = _generic_rule_score(fields, text, jd)
            return {
                "candidate_id": cid,
                "name":         fields["name"],
                "score":        rule_sc,
                "title":        fields["title"],
                "company":      fields["company"],
                "yoe":          fields["yoe"],
                "location":     fields["location"],
                "country":      fields["country"],
                "open_to_work": fields["open_to_work"],
                "notice_days":  fields["notice_days"],
                "response_rate": 0.0,
                "reasoning":    reason,
            }
    except Exception:
        return None


def score_all_parallel(candidates: list, jd: dict, n_workers: int = None,
                       use_semantic: bool = True) -> tuple:
    """
    Score all candidates — schema-agnostic hybrid pipeline.

    Redrob schema:  rule×0.45 + semantic×0.35 + bm25×0.20
    Generic schema: rule×0.30 + semantic×0.50 + bm25×0.20

    Returns (results_list, error_count).
    """
    from multiprocessing import Pool, cpu_count

    if n_workers is None:
        n_workers = max(1, cpu_count() - 1)

    # Detect schema from first candidate
    sample = candidates[0] if candidates else {}
    generic_mode = not _is_redrob_schema(sample)

    # ── Rule-based scoring ────────────────────────────────────────────────────
    args      = [(c, jd) for c in candidates]
    chunksize = max(1, len(args) // max(n_workers * 8, 1))

    if n_workers > 1:
        with Pool(processes=n_workers) as pool:
            raw = pool.map(_score_worker, args, chunksize=chunksize)
    else:
        raw = [_score_worker(a) for a in args]

    results = [r for r in raw if r is not None]
    errors  = sum(1 for r in raw if r is None)

    if not results:
        return results, errors

    if not use_semantic:
        results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
        for i, r in enumerate(results):
            r["rank"] = i + 1
        return results, errors

    # ── Two-stage: semantic + BM25 re-rank top pool ───────────────────────────
    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))

    SEMANTIC_POOL = 1000
    pool_results = results[:SEMANTIC_POOL]
    if not generic_mode:
        # Redrob: only re-rank candidates that passed rule-based filter
        rule_passed = [r for r in results if r["score"] > 0.01]
        if rule_passed:
            pool_results = rule_passed[:SEMANTIC_POOL]

    pool_ids   = {r["candidate_id"] for r in pool_results}
    pool_cands = [c for c in candidates if _extract_id(c) in pool_ids]
    id_to_result = {r["candidate_id"]: r for r in pool_results}

    try:
        sem_scores  = compute_semantic_scores(pool_cands, jd)
        bm25_scores = compute_bm25_scores(pool_cands, jd)

        for c, sem, bm25 in zip(pool_cands, sem_scores, bm25_scores):
            cid = _extract_id(c)
            if cid not in id_to_result:
                continue
            rule_sc = id_to_result[cid]["score"]
            if generic_mode:
                hybrid = rule_sc * 0.30 + sem * 0.50 + bm25 * 0.20
                # Fill title from text blob if not extracted
                if not id_to_result[cid]["title"]:
                    id_to_result[cid]["title"] = _extract_all_text(c)[:60]
                # Incorporate semantic quality naturally into reasoning closing
                if sem >= 0.70:
                    qualifier = "; well-aligned with JD"
                elif sem >= 0.55:
                    qualifier = "; solid semantic match"
                else:
                    qualifier = "; weak semantic alignment"
                id_to_result[cid]["reasoning"] = (
                    id_to_result[cid]["reasoning"][:-1] + qualifier + "."
                )
            else:
                hybrid = rule_sc * 0.45 + sem * 0.35 + bm25 * 0.20
            id_to_result[cid]["score"] = round(min(1.0, hybrid), 6)
    except Exception:
        pass  # fall back to rule-only if semantic fails

    results.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results, errors


# ─── Main pipeline ────────────────────────────────────────────────────────────

def run(candidates_path: str, output_path: str, jd_path: str = None, top_n: int = 100):
    """Load JD, score all candidates via hybrid pipeline, write top-N to CSV."""

    # Load JD features
    if jd_path and Path(jd_path).exists():
        print(f"Parsing JD from {jd_path} ...")
        jd_text = read_jd_text(jd_path)
        jd = extract_jd_features(jd_text)
        print(f"  Domain: {jd['role_domain']} | "
              f"Exp: {jd['exp_min']}-{jd['exp_max']}yr | "
              f"Required skills found: {len(jd['required_skills'])} | "
              f"Bonus skills: {len(jd['bonus_skills'])}")
        if len(jd["all_skills"]) < 3:
            print("  Warning: very few skills extracted from JD. Using built-in defaults as fallback.")
            jd = default_jd_features()
    else:
        if jd_path:
            print(f"Warning: JD file not found at {jd_path}. Using built-in Senior AI Eng defaults.")
        else:
            print("No --jd provided. Using built-in Senior AI Engineer JD defaults.")
        jd = default_jd_features()

    # Load all candidates — handles JSONL, JSON array, and wrapped {"candidates": [...]}
    print(f"Loading candidates from {candidates_path} ...")
    candidates = load_candidates(candidates_path)
    load_errors = 0

    # Hybrid scoring: rule-based (parallel) + semantic (local sentence-transformers) + BM25
    print("Scoring with hybrid pipeline (rule + semantic + BM25) ...")
    results, errors = score_all_parallel(candidates, jd, use_semantic=True)
    print(f"  Scored {len(results):,} candidates ({errors} score errors)")

    top = results[:top_n]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for r in top:
            writer.writerow([r["candidate_id"], r["rank"], f"{r['score']:.6f}", r["reasoning"]])

    print(f"  Top {top_n} written to {output_path}")

    # Summary stats
    honeypots = sum(1 for r in top if "HONEYPOT" in r["reasoning"])
    strong = sum(1 for r in top if r["score"] >= 0.82)
    good   = sum(1 for r in top if 0.70 <= r["score"] < 0.82)
    print(f"  Strong match (≥0.82): {strong} | Good fit (0.70-0.82): {good} | Honeypots in top-100: {honeypots}")

    # Return in legacy format for __main__ preview compatibility
    return [(r["score"], r["candidate_id"], r["reasoning"]) for r in top]


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Redrob Candidate Ranker v3 — generic JD + candidates → top-100 CSV"
    )
    p.add_argument("--jd", default=None,
                   help="Path to job description file (.docx or .txt). "
                        "If omitted, uses built-in Senior AI Engineer JD.")
    p.add_argument("--candidates", default="candidates.jsonl",
                   help="Path to candidates.jsonl")
    p.add_argument("--output", default="submission_ranked_top100.csv",
                   help="Output CSV path")
    p.add_argument("--top", type=int, default=100,
                   help="Number of top candidates to output (default: 100)")
    args = p.parse_args()

    top = run(args.candidates, args.output, args.jd, args.top)
    print(f"\nTop 5 preview:")
    for rank, (sc, cid, reason) in enumerate(top[:5], 1):
        print(f"  {rank}. {cid}  {sc:.4f}  {reason[:90]}...")
