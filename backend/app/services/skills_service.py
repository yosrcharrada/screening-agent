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
    # Use utf-8-sig to strip BOM if present (Windows)
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def load_yaml(path: Path) -> dict:
    # Use utf-8-sig to strip BOM if present (Windows)
    with open(path, "r", encoding="utf-8-sig") as f:
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
        sents = re.split(r"(?<=[.!?])\s+", text.strip())
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