# Run from repo root: pwsh -File scripts\setup_wp4.ps1
# If blocked: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

function Write-TextFile {
  param([string]$Path, [string]$Text)
  $dir = Split-Path $Path
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  $Text | Out-File -FilePath $Path -Encoding utf8 -Force
}

# .gitignore
Write-TextFile ".gitignore" @'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.venv/
.env

# OS
.DS_Store

# Reports / caches
reports/
.cache/
'@

# requirements
Write-TextFile "requirements.txt" @'
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
spacy==3.7.6
sentence-transformers==3.0.1
numpy==2.1.1
pandas==2.2.2
pyyaml==6.0.2
'@

# README
Write-TextFile "README_WP4.md" @'
# WP4 — Skills & Questions (with evidence XAI)

What you build:
- POST /skills → returns skills present in CV & JD, similarities, gap_map (present/partial/missing), tips, and evidence quotes (XAI).
- POST /questions → returns 5 JD-aware questions with rationale “Targets gap: <Skill>”.

Run locally (PowerShell):
1) py -3 -m venv .venv
2) .venv\Scripts\Activate.ps1
3) pip install -r requirements.txt
4) python -m spacy download en_core_web_sm
5) CLI demo: python scripts\skills_demo.py data\sample_cv.txt data\sample_jd.txt
6) Start API: uvicorn backend.app.main:app --reload
7) Open http://127.0.0.1:8000/docs

Quick curl tests:
- /skills
curl -X POST http://127.0.0.1:8000/skills -H "Content-Type: application/json" -d "{\"cv_text\":\"Built Python ETL with SQL and Docker.\",\"jd_text\":\"We need Python and SQL; Docker is a plus.\"}"

- /questions
curl -X POST http://127.0.0.1:8000/questions -H "Content-Type: application/json" -d "{\"gap_map\":[{\"skill\":\"python\",\"status\":\"present\"},{\"skill\":\"sql\",\"status\":\"present\"},{\"skill\":\"docker\",\"status\":\"partial\"}]}"
'@

# config
Write-TextFile "config/thresholds.yaml" @'
present_threshold: 0.85
partial_threshold: 0.60
max_questions: 5
use_embeddings: true   # set to false if sentence-transformers is heavy
'@

# data
Write-TextFile "data/skills_ontology.json" @'
{
  "python": ["py"],
  "sql": ["postgresql", "mysql", "sqlite"],
  "docker": ["containers", "containerization"],
  "react": ["reactjs"],
  "whisper": ["openai whisper"],
  "nlp": ["natural language processing"],
  "mlops": ["ml ops", "machine learning ops"]
}
'@

Write-TextFile "data/questions.csv" @'
id,text,skill_tag,type,difficulty
Q1,"Walk me through a recent project where you used {skill}. What was the goal and the measurable outcome?",generic,behavioral,medium
Q2,"Can you explain how you would design a solution using {skill} to meet a key requirement from this JD?",generic,technical,hard
Q3,"Tell me about a time you had to quickly learn or improve your {skill}. What did you do and what changed?",generic,behavioral,medium
Q4,"Given this JD emphasizes {skill}, what trade-offs would you consider when implementing it in production?",generic,technical,hard
Q5,"Describe a challenge you faced while working with {skill} and how you resolved it. Include metrics.",generic,behavioral,medium
Q7,"For SQL: how would you optimize a slow query on a large table with frequent writes?",sql,technical,hard
Q8,"For Docker: how do you structure images and manage multi-stage builds for smaller, secure artifacts?",docker,technical,medium
Q9,"For Python: how do you ensure code quality and performance in data pipelines?",python,technical,medium
Q10,"For React: how do you manage state and performance for large lists?",react,technical,medium
'@

Write-TextFile "data/sample_cv.txt" @'
Built Python ETL jobs and optimized SQL queries (PostgreSQL). Containerized services with Docker.
Improved model latency by 30%. React dashboard for reporting.
'@

Write-TextFile "data/sample_jd.txt" @'
Looking for strong Python and SQL experience. Bonus: Docker for deployment, React for UI.
Experience with NLP or Whisper is a plus.
'@

# packages
Write-TextFile "backend/__init__.py" ""
Write-TextFile "backend/app/__init__.py" ""
Write-TextFile "backend/app/routers/__init__.py" ""
Write-TextFile "backend/app/services/__init__.py" ""
Write-TextFile "backend/app/models/__init__.py" ""

# FastAPI main
Write-TextFile "backend/app/main.py" @'
from fastapi import FastAPI
from backend.app.routers.skills import router as skills_router
from backend.app.routers.questions import router as questions_router

app = FastAPI(title="screening-agent — WP4 Skills & Questions")

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(skills_router, tags=["skills"])
app.include_router(questions_router, tags=["questions"])
'@

# models
Write-TextFile "backend/app/models/skills.py" @'
from pydantic import BaseModel
from typing import List, Tuple, Optional

class SkillSpan(BaseModel):
    name: str
    spans: List[Tuple[int, int]]

class EvidenceItem(BaseModel):
    skill: str
    cv_quote: Optional[str] = ""
    jd_quote: Optional[str] = ""

class SimilarityItem(BaseModel):
    skill: str
    score: float
    cv_sent: str
    jd_sent: str

class GapItem(BaseModel):
    skill: str
    status: str  # present | partial | missing

class SkillsResponse(BaseModel):
    skills_cv: List[SkillSpan]
    skills_jd: List[SkillSpan]
    similarities: List[SimilarityItem]
    gap_map: List[GapItem]
    tips: List[str]
    evidence: List[EvidenceItem]
'@

Write-TextFile "backend/app/models/questions.py" @'
from pydantic import BaseModel
from typing import List

class QuestionItem(BaseModel):
    id: str
    text: str
    difficulty: str
    rationale: str

class QuestionsResponse(BaseModel):
    questions: List[QuestionItem]
'@

# services: skills
Write-TextFile "backend/app/services/skills_service.py" @'
from __future__ import annotations
from typing import Dict, List, Tuple
import json, re
from pathlib import Path
import yaml
import numpy as np

import spacy
from spacy.matcher import PhraseMatcher

try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_ST = True
except Exception:
    _HAS_ST = False

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
CONFIG = ROOT / "config"

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class SkillsEngine:
    def __init__(self,
                 ontology_path: Path = DATA / "skills_ontology.json",
                 thresholds_path: Path = CONFIG / "thresholds.yaml",
                 model_name: str = "en_core_web_sm",
                 embedder_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.ontology = load_json(ontology_path)
        self.cfg = load_yaml(thresholds_path)
        self.use_embeddings = bool(self.cfg.get("use_embeddings", True) and _HAS_ST)
        self.nlp = spacy.load(model_name, disable=["ner","parser","lemmatizer"])
        self.matcher = self._build_matcher()
        self.embedder = SentenceTransformer(embedder_name) if self.use_embeddings else None

    def _build_matcher(self) -> PhraseMatcher:
        pm = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        for canon, syns in self.ontology.items():
            phrases = [canon] + syns
            pm.add(canon, [self.nlp.make_doc(p) for p in phrases])
        return pm

    @staticmethod
    def _sentences(text: str) -> List[str]:
        sents = re.split(r"(?<=[.!?])\\s+", text.strip())
        return [s for s in sents if s]

    def extract_skill_mentions(self, text: str) -> Dict[str, List[Tuple[int,int]]]:
        doc = self.nlp.make_doc(text)
        matches = self.matcher(doc)
        spans: Dict[str, List[Tuple[int,int]]] = {}
        for mid, start, end in matches:
            key = self.nlp.vocab.strings[mid]
            span = doc[start:end]
            spans.setdefault(key, []).append((span.start_char, span.end_char))
        return spans

    def _best_sentence_for_skill(self, text: str, skill: str) -> str:
        sents = self._sentences(text)
        for s in sents:
            if skill.lower() in s.lower():
                return s
            for syn in self.ontology.get(skill, []):
                if syn.lower() in s.lower():
                    return s
        if not sents:
            return ""
        if not self.use_embeddings:
            return sents[0]
        emb_sents = self.embedder.encode(sents, convert_to_tensor=True, normalize_embeddings=True)
        emb_skill = self.embedder.encode([skill], convert_to_tensor=True, normalize_embeddings=True)
        sims = util.cos_sim(emb_skill, emb_sents).cpu().numpy()[0]
        return sents[int(np.argmax(sims))]

    def compute_similarities(self, cv_text: str, jd_text: str) -> List[Dict]:
        out = []
        for skill in sorted(self.ontology.keys()):
            cv_sent = self._best_sentence_for_skill(cv_text, skill)
            jd_sent = self._best_sentence_for_skill(jd_text, skill)
            if self.use_embeddings:
                if not cv_sent and not jd_sent:
                    score = 0.0
                else:
                    emb = self.embedder.encode([cv_sent or "", jd_sent or ""],
                                               convert_to_tensor=True, normalize_embeddings=True)
                    score = float(util.cos_sim(emb[0:1], emb[1:2]).cpu().numpy()[0][0])
            else:
                if skill.lower() in cv_text.lower() and skill.lower() in jd_text.lower():
                    score = 0.95
                elif skill.lower() in cv_text.lower():
                    score = 0.7
                elif skill.lower() in jd_text.lower():
                    score = 0.6
                else:
                    score = 0.0
            out.append({"skill": skill, "score": round(score,3), "cv_sent": cv_sent, "jd_sent": jd_sent})
        return out

    def build_gap_map(self, similarities: List[Dict]) -> List[Dict]:
        present_th = float(self.cfg["present_threshold"])
        partial_th = float(self.cfg["partial_threshold"])
        gap = []
        for item in similarities:
            s = item["score"]
            if s >= present_th:
                status = "present"
            elif s >= partial_th:
                status = "partial"
            else:
                status = "missing"
            gap.append({"skill": item["skill"], "status": status})
        return gap

    @staticmethod
    def tips_from_gap(gap_map: List[Dict]) -> List[str]:
        tips = []
        miss = [g["skill"] for g in gap_map if g["status"] == "missing"][:3]
        part = [g["skill"] for g in gap_map if g["status"] == "partial"][:3]
        for s in miss:
            tips.append(f"Add a concrete project or bullet using {s}; include a metric.")
        for s in part:
            tips.append(f"Strengthen {s}: add a quantified example or recent repo link.")
        return tips or ["Great alignment. Keep examples recent and quantified."]

    def evidence_items(self, cv_text: str, jd_text: str) -> List[Dict]:
        items = []
        for skill in sorted(self.ontology.keys()):
            items.append({
                "skill": skill,
                "cv_quote": self._best_sentence_for_skill(cv_text, skill),
                "jd_quote": self._best_sentence_for_skill(jd_text, skill)
            })
        return items

    def payload(self, cv_text: str, jd_text: str) -> Dict:
        skills_cv = [{"name": k, "spans": v} for k, v in self.extract_skill_mentions(cv_text).items()]
        skills_jd = [{"name": k, "spans": v} for k, v in self.extract_skill_mentions(jd_text).items()]
        sims = self.compute_similarities(cv_text, jd_text)
        gap = self.build_gap_map(sims)
        tips = self.tips_from_gap(gap)
        evid = self.evidence_items(cv_text, jd_text)
        return {
            "skills_cv": skills_cv,
            "skills_jd": skills_jd,
            "similarities": sims,
            "gap_map": gap,
            "tips": tips,
            "evidence": evid
        }
'@

# services: questions
Write-TextFile "backend/app/services/questions_service.py" @'
from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import csv
import yaml

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
CONFIG = ROOT / "config"

class QuestionBank:
    def __init__(self, csv_path: Path = DATA / "questions.csv", thresholds_path: Path = CONFIG / "thresholds.yaml"):
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            self.rows = [row for row in r]
        with open(thresholds_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self.max_q = int(cfg.get("max_questions", 5))

    def generate(self, gap_map: List[Dict]) -> List[Dict]:
        missing = [g["skill"] for g in gap_map if g["status"] == "missing"]
        partial = [g["skill"] for g in gap_map if g["status"] == "partial"]
        targets = (missing + partial)[:3] or ["generic"]

        picked: List[Dict] = []
        used_ids = set()

        # Skill-specific first
        for skill in targets:
            for row in self.rows:
                if row["skill_tag"].lower() == skill.lower() and row["id"] not in used_ids:
                    picked.append({
                        "id": row["id"],
                        "text": row["text"].replace("{skill}", skill),
                        "difficulty": row["difficulty"],
                        "rationale": f"Targets gap: {skill}"
                    })
                    used_ids.add(row["id"])
                    if len(picked) >= self.max_q:
                        return picked

        # Generic templates using the top target
        main = targets[0]
        for row in self.rows:
            if row["skill_tag"].lower() == "generic" and row["id"] not in used_ids:
                picked.append({
                    "id": row["id"],
                    "text": row["text"].replace("{skill}", main),
                    "difficulty": row["difficulty"],
                    "rationale": f"Targets gap: {main}"
                })
                used_ids.add(row["id"])
                if len(picked) >= self.max_q:
                    break

        return picked
'@

# routers
Write-TextFile "backend/app/routers/skills.py" @'
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict
from backend.app.services.skills_service import SkillsEngine

router = APIRouter()
engine = SkillsEngine()

class SkillsIn(BaseModel):
    cv_text: str
    jd_text: str

@router.post("/skills")
def skills_endpoint(req: SkillsIn) -> Dict[str, Any]:
    return engine.payload(req.cv_text, req.jd_text)
'@

Write-TextFile "backend/app/routers/questions.py" @'
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.app.services.questions_service import QuestionBank

router = APIRouter()
bank = QuestionBank()

class GapItem(BaseModel):
    skill: str
    status: str  # present | partial | missing

class QuestionsIn(BaseModel):
    gap_map: List[GapItem]

@router.post("/questions")
def questions_endpoint(req: QuestionsIn) -> Dict[str, Any]:
    qs = bank.generate([g.model_dump() for g in req.gap_map])
    return {"questions": qs}
'@

# demo script
Write-TextFile "scripts/skills_demo.py" @'
import sys
from pathlib import Path
from pprint import pprint
from backend.app.services.skills_service import SkillsEngine

def main(cv_path: str, jd_path: str):
    cv = Path(cv_path).read_text(encoding="utf-8")
    jd = Path(jd_path).read_text(encoding="utf-8")
    eng = SkillsEngine()
    out = eng.payload(cv, jd)
    pprint(out)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts\\skills_demo.py data\\sample_cv.txt data\\sample_jd.txt")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
'@

# test
Write-TextFile "tests/test_skills_basic.py" @'
from backend.app.services.skills_service import SkillsEngine

def test_gap_map_basic():
    cv = "Built Python ETL and optimized SQL queries. Docker for deployment."
    jd = "We need Python and SQL. Docker is a plus."
    eng = SkillsEngine()
    out = eng.payload(cv, jd)
    # Structure check
    assert "gap_map" in out and "evidence" in out and "similarities" in out
    # Obvious tech skills should not be "missing"
    statuses = {g["skill"]: g["status"] for g in out["gap_map"]}
    for s in ["python", "sql"]:
        assert statuses.get(s) in {"present", "partial"}
'@

Write-Host "WP4 files created. Next steps:"
Write-Host "1) py -3 -m venv .venv"
Write-Host "2) .venv\\Scripts\\Activate.ps1"
Write-Host "3) pip install -r requirements.txt"
Write-Host "4) python -m spacy download en_core_web_sm"
Write-Host "5) python scripts\\skills_demo.py data\\sample_cv.txt data\\sample_jd.txt"
Write-Host "6) uvicorn backend.app.main:app --reload"